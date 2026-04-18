from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    ChatRoom, ChatParticipant, Message, MessageReaction, MessageRead,
    ChatCategory, RoomCategory, TypingIndicator, ChatAnalytics
)
from .serializers import (
    ChatRoomSerializer, ChatParticipantSerializer, MessageSerializer,
    MessageReactionSerializer, MessageReadSerializer, ChatCategorySerializer,
    RoomCategorySerializer, TypingIndicatorSerializer, ChatAnalyticsSerializer,
    CreateRoomSerializer, SendMessageSerializer, MarkAsReadSerializer,
    ReactToMessageSerializer
)
from users.models import User, UserActivity


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            participants=user,
            is_active=True
        ).order_by('-last_message_time')


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.kwargs['room_id']
        user = self.request.user
        
        # Check if user is participant
        if not ChatRoom.objects.filter(
            id=room_id,
            participants=user,
            is_active=True
        ).exists():
            return Message.objects.none()
        
        return Message.objects.filter(
            room_id=room_id,
            is_deleted=False
        ).order_by('created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_room(request):
    """Create a new chat room"""
    serializer = CreateRoomSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    name = serializer.validated_data.get('name', '')
    room_type = serializer.validated_data['room_type']
    participant_ids = serializer.validated_data['participant_ids']
    
    # Validate participants
    participants = User.objects.filter(id__in=participant_ids)
    if participants.count() != len(participant_ids):
        return Response({'error': 'Some participants not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    # For direct messages, check if room already exists
    if room_type == ChatRoom.DIRECT and len(participant_ids) == 1:
        other_user = participants.first()
        existing_room = ChatRoom.objects.filter(
            room_type=ChatRoom.DIRECT,
            participants=user
        ).filter(participants=other_user).first()
        
        if existing_room:
            return Response({
                'room': ChatRoomSerializer(existing_room).data,
                'message': 'Room already exists'
            }, status=status.HTTP_200_OK)
    
    # Create room
    room = ChatRoom.objects.create(
        name=name,
        room_type=room_type,
        created_by=user
    )
    
    # Add participants
    all_participants = list(participants) + [user]
    for participant in all_participants:
        role = ChatParticipant.ADMIN if participant == user else ChatParticipant.MEMBER
        ChatParticipant.objects.create(
            room=room,
            user=participant,
            role=role
        )
    
    return Response({
        'room': ChatRoomSerializer(room).data,
        'message': 'Room created successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """Send a message to a chat room"""
    serializer = SendMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    room_id = serializer.validated_data['room_id']
    content = serializer.validated_data['content']
    message_type = serializer.validated_data['message_type']
    reply_to_id = serializer.validated_data.get('reply_to_id')
    
    # Check if user is participant
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=user,
            is_active=True
        )
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    # Validate reply_to
    reply_to = None
    if reply_to_id:
        try:
            reply_to = Message.objects.get(id=reply_to_id, room=room)
        except Message.DoesNotExist:
            return Response({'error': 'Reply message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create message
    message = Message.objects.create(
        room=room,
        sender=user,
        content=content,
        message_type=message_type,
        reply_to=reply_to
    )
    
    # Update room's last message
    room.last_message = content
    room.last_message_time = message.created_at
    room.save()
    
    # Update participant's last read
    participant = ChatParticipant.objects.get(room=room, user=user)
    participant.last_read = message.created_at
    participant.save()
    
    # Send WebSocket notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{room_id}',
        {
            'type': 'chat_message',
            'message': MessageSerializer(message).data
        }
    )
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='message',
        metadata={
            'room_id': str(room_id),
            'message_id': str(message.id),
            'message_type': message_type
        }
    )
    
    return Response({
        'message': MessageSerializer(message).data,
        'status': 'sent'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_as_read(request):
    """Mark messages as read"""
    serializer = MarkAsReadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    message_id = serializer.validated_data['message_id']
    
    try:
        message = Message.objects.get(id=message_id)
        
        # Check if user is participant
        if not ChatRoom.objects.filter(
            id=message.room_id,
            participants=user,
            is_active=True
        ).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Create or update read receipt
        read_receipt, created = MessageRead.objects.get_or_create(
            message=message,
            user=user,
            defaults={'read_at': timezone.now()}
        )
        
        if not created:
            read_receipt.read_at = timezone.now()
            read_receipt.save()
        
        # Update participant's last read
        participant = ChatParticipant.objects.get(
            room=message.room,
            user=user
        )
        participant.last_read = message.created_at
        participant.save()
        
        return Response({'status': 'marked as read'})
    
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def react_to_message(request):
    """Add or remove reaction to a message"""
    serializer = ReactToMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    message_id = serializer.validated_data['message_id']
    emoji = serializer.validated_data['emoji']
    
    try:
        message = Message.objects.get(id=message_id)
        
        # Check if user is participant
        if not ChatRoom.objects.filter(
            id=message.room_id,
            participants=user,
            is_active=True
        ).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Toggle reaction
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=user,
            emoji=emoji
        )
        
        if not created:
            # Remove reaction if it already exists
            reaction.delete()
            return Response({'status': 'reaction removed'})
        else:
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{message.room_id}',
                {
                    'type': 'message_reaction',
                    'reaction': MessageReactionSerializer(reaction).data
                }
            )
            
            return Response({
                'status': 'reaction added',
                'reaction': MessageReactionSerializer(reaction).data
            })
    
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_typing(request):
    """Indicate user is typing"""
    room_id = request.data.get('room_id')
    
    if not room_id:
        return Response({'error': 'room_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=request.user,
            is_active=True
        )
        
        typing_indicator, created = TypingIndicator.objects.update_or_create(
            room=room,
            user=request.user,
            defaults={'is_typing': True, 'last_seen': timezone.now()}
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'typing_indicator',
                'user_id': str(request.user.id),
                'username': request.user.username,
                'is_typing': True
            }
        )
        
        return Response({'status': 'typing'})
    
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stop_typing(request):
    """Indicate user stopped typing"""
    room_id = request.data.get('room_id')
    
    if not room_id:
        return Response({'error': 'room_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = ChatRoom.objects.get(
            id=room_id,
            participants=request.user,
            is_active=True
        )
        
        # Update typing indicator
        typing_indicators = TypingIndicator.objects.filter(
            room=room,
            user=request.user
        )
        
        for indicator in typing_indicators:
            indicator.is_typing = False
            indicator.save()
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'typing_indicator',
                'user_id': str(request.user.id),
                'username': request.user.username,
                'is_typing': False
            }
        )
        
        return Response({'status': 'stopped typing'})
    
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """Get unread message count for user"""
    user = request.user
    
    # Get all rooms user participates in
    room_participants = ChatParticipant.objects.filter(user=user)
    
    unread_count = 0
    for participant in room_participants:
        # Count messages after user's last read time
        last_read = participant.last_read or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        
        room_unread = Message.objects.filter(
            room=participant.room,
            created_at__gt=last_read,
            is_deleted=False
        ).exclude(sender=user).count()
        
        unread_count += room_unread
    
    return Response({'unread_count': unread_count})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_analytics(request):
    """Get chat analytics for the user"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    analytics = ChatAnalytics.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('-date')
    
    serializer = ChatAnalyticsSerializer(analytics, many=True)
    return Response(serializer.data)
