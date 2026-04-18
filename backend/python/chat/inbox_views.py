from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Max, Subquery, OuterRef
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    ChatRoom, ChatParticipant, Message, MessageReaction, MessageRead,
    TypingIndicator
)
from .serializers import (
    ChatRoomSerializer, MessageSerializer, MessageReadSerializer,
    InboxRoomSerializer, InboxMessageSerializer
)
from users.models import User, UserActivity
from social.models import Notification


class InboxListView(generics.ListAPIView):
    """
    Get user's inbox with chat rooms and unread counts
    """
    serializer_class = InboxRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get all rooms user participates in
        rooms = ChatRoom.objects.filter(
            participants=user,
            is_active=True
        ).annotate(
            unread_count=Subquery(
                Message.objects.filter(
                    room=OuterRef('pk'),
                    created_at__gt=Subquery(
                        ChatParticipant.objects.filter(
                            room=OuterRef('pk'),
                            user=user
                        ).values('last_read')[:1]
                    ),
                    is_deleted=False
                ).exclude(sender=user)
                .values('unread_count')[:1]
            ),
            last_message_content=Subquery(
                Message.objects.filter(
                    room=OuterRef('pk'),
                    is_deleted=False
                ).order_by('-created_at')
                .values('content')[:1]
            ),
            last_message_time=Subquery(
                Message.objects.filter(
                    room=OuterRef('pk'),
                    is_deleted=False
                ).order_by('-created_at')
                .values('created_at')[:1]
            ),
            last_message_sender=Subquery(
                Message.objects.filter(
                    room=OuterRef('pk'),
                    is_deleted=False
                ).order_by('-created_at')
                .values('sender__username')[:1]
            )
        ).order_by('-last_message_time', '-created_at')
        
        return rooms


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_inbox_summary(request):
    """
    Get inbox summary with unread counts and recent activity
    """
    user = request.user
    
    # Get total unread count
    room_participants = ChatParticipant.objects.filter(user=user)
    total_unread = 0
    
    for participant in room_participants:
        last_read = participant.last_read or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        room_unread = Message.objects.filter(
            room=participant.room,
            created_at__gt=last_read,
            is_deleted=False
        ).exclude(sender=user).count()
        total_unread += room_unread
    
    # Get recent rooms (last 5)
    recent_rooms = ChatRoom.objects.filter(
        participants=user,
        is_active=True
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')[:5]
    
    # Get unread notifications (chat-related)
    chat_notifications = Notification.objects.filter(
        recipient=user,
        notification_type__in=['message', 'chat_request'],
        is_read=False
    ).count()
    
    return Response({
        'total_unread_messages': total_unread,
        'unread_notifications': chat_notifications,
        'recent_rooms': InboxRoomSerializer(recent_rooms, many=True).data,
        'total_rooms': room_participants.count()
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_room(request, room_id):
    """
    Get detailed chat room information
    """
    user = request.user
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get room details with participants
    room_data = ChatRoomSerializer(room).data
    
    # Add participant details
    participants = ChatParticipant.objects.filter(room=room).select_related('user')
    room_data['participants'] = [
        {
            'user_id': str(p.user.id),
            'username': p.user.username,
            'first_name': p.user.first_name,
            'last_name': p.user.last_name,
            'role': p.role,
            'joined_at': p.joined_at,
            'last_read': p.last_read,
            'is_muted': p.is_muted,
            'is_archived': p.is_archived
        }
        for p in participants
    ]
    
    # Get unread count for this room
    user_participant = participants.get(user=user)
    last_read = user_participant.last_read or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
    
    unread_count = Message.objects.filter(
        room=room,
        created_at__gt=last_read,
        is_deleted=False
    ).exclude(sender=user).count()
    
    room_data['unread_count'] = unread_count
    
    return Response(room_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_direct_message(request):
    """
    Create or get a direct message room with another user
    """
    user = request.user
    recipient_id = request.data.get('recipient_id')
    
    if not recipient_id:
        return Response({'error': 'recipient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        recipient = User.objects.get(id=recipient_id)
        
        if recipient == user:
            return Response({'error': 'Cannot message yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if direct message room already exists
        existing_room = ChatRoom.objects.filter(
            room_type=ChatRoom.DIRECT,
            participants=user
        ).filter(participants=recipient).first()
        
        if existing_room:
            # Return existing room
            return Response({
                'room': InboxRoomSerializer(existing_room).data,
                'message': 'Direct message room already exists'
            }, status=status.HTTP_200_OK)
        
        # Create new direct message room
        room = ChatRoom.objects.create(
            room_type=ChatRoom.DIRECT,
            created_by=user
        )
        
        # Add both users as participants
        ChatParticipant.objects.create(room=room, user=user, role=ChatParticipant.ADMIN)
        ChatParticipant.objects.create(room=room, user=recipient, role=ChatParticipant.MEMBER)
        
        # Send notification to recipient
        Notification.objects.create(
            recipient=recipient,
            sender=user,
            notification_type='message',
            message=f"{user.username} started a conversation with you"
        )
        
        # Send WebSocket notification to recipient
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient.id}",
            {
                'type': 'new_direct_message',
                'room_id': str(room.id),
                'sender_id': str(user.id),
                'sender_username': user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return Response({
            'room': InboxRoomSerializer(room).data,
            'message': 'Direct message created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_room_as_read(request, room_id):
    """
    Mark all messages in a room as read for the user
    """
    user = request.user
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
        
        # Get latest message time
        latest_message = Message.objects.filter(
            room=room,
            is_deleted=False
        ).order_by('-created_at').first()
        
        if latest_message:
            # Update participant's last read time
            participant = ChatParticipant.objects.get(room=room, user=user)
            participant.last_read = latest_message.created_at
            participant.save()
            
            # Create read receipts for all unread messages
            unread_messages = Message.objects.filter(
                room=room,
                created_at__lte=latest_message.created_at,
                is_deleted=False
            ).exclude(sender=user)
            
            for message in unread_messages:
                MessageRead.objects.get_or_create(
                    message=message,
                    user=user,
                    defaults={'read_at': timezone.now()}
                )
            
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'messages_read',
                    'user_id': str(user.id),
                    'username': user.username,
                    'read_up_to': latest_message.created_at.isoformat()
                }
            )
        
        return Response({'status': 'room marked as read'})
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def archive_room(request, room_id):
    """
    Archive a chat room
    """
    user = request.user
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
        
        participant = ChatParticipant.objects.get(room=room, user=user)
        participant.is_archived = True
        participant.save()
        
        return Response({'status': 'room archived'})
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mute_room(request, room_id):
    """
    Mute notifications for a chat room
    """
    user = request.user
    is_muted = request.data.get('is_muted', True)
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
        
        participant = ChatParticipant.objects.get(room=room, user=user)
        participant.is_muted = is_muted
        participant.save()
        
        return Response({
            'status': 'room muted' if is_muted else 'room unmuted',
            'is_muted': is_muted
        })
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_room(request, room_id):
    """
    Delete a chat room (only for direct messages, removes user from room)
    """
    user = request.user
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
        
        if room.room_type == ChatRoom.GROUP:
            return Response({'error': 'Cannot delete group chat, leave instead'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For direct messages, remove user from room
        participant = ChatParticipant.objects.get(room=room, user=user)
        participant.delete()
        
        # If no participants left, deactivate room
        if room.participants.count() == 0:
            room.is_active = False
            room.save()
        
        return Response({'status': 'room deleted'})
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_conversations(request):
    """
    Search conversations by username or message content
    """
    user = request.user
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Search rooms by participant username
    rooms_by_user = ChatRoom.objects.filter(
        participants=user,
        participants__username__icontains=query,
        is_active=True
    ).distinct()
    
    # Search rooms by message content
    rooms_by_message = ChatRoom.objects.filter(
        participants=user,
        messages__content__icontains=query,
        messages__is_deleted=False,
        is_active=True
    ).distinct()
    
    # Combine and deduplicate
    all_rooms = rooms_by_user.union(rooms_by_message).order_by('-last_message_time')
    
    # Annotate with search highlights
    results = []
    for room in all_rooms:
        room_data = InboxRoomSerializer(room).data
        
        # Add search context
        if room in rooms_by_user:
            room_data['search_context'] = 'username'
        else:
            room_data['search_context'] = 'message'
            # Get matching message snippet
            matching_message = Message.objects.filter(
                room=room,
                content__icontains=query,
                is_deleted=False
            ).first()
            if matching_message:
                room_data['message_snippet'] = matching_message.content[:100]
        
        results.append(room_data)
    
    return Response({
        'query': query,
        'results': results
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_message_history(request, room_id):
    """
    Get message history with pagination and search
    """
    user = request.user
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get pagination parameters
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 50))
    search_query = request.query_params.get('search', '').strip()
    
    # Build message queryset
    messages = Message.objects.filter(
        room=room,
        is_deleted=False
    )
    
    if search_query:
        messages = messages.filter(content__icontains=search_query)
    
    # Order by creation time (newest first for pagination)
    messages = messages.order_by('-created_at')
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    messages_page = messages[start:end]
    
    # Serialize messages
    serializer = MessageSerializer(messages_page, many=True)
    
    return Response({
        'messages': serializer.data,
        'page': page,
        'page_size': page_size,
        'total': messages.count(),
        'has_more': end < messages.count()
    })
