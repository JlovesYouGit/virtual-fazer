from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message, ChatRoom, ChatParticipant, MessageReaction, MessageRead
from social.models import Notification
from users.models import User


@receiver(post_save, sender=Message)
def handle_message_created(sender, instance, created, **kwargs):
    """
    Handle message creation events
    """
    if not created:
        return
    
    # Update room's last message
    room = instance.room
    room.last_message = instance.content[:100]  # Truncate for preview
    room.last_message_time = instance.created_at
    room.save(update_fields=['last_message', 'last_message_time'])
    
    # Send WebSocket notification to room
    channel_layer = get_channel_layer()
    
    # Send message to all room participants
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.room.id}',
        {
            'type': 'chat_message',
            'message': {
                'id': str(instance.id),
                'room': str(instance.room.id),
                'sender': {
                    'id': str(instance.sender.id),
                    'username': instance.sender.username,
                    'first_name': instance.sender.first_name,
                    'last_name': instance.sender.last_name
                },
                'content': instance.content,
                'message_type': instance.message_type,
                'media_file': instance.media_file.url if instance.media_file else None,
                'reply_to': {
                    'id': str(instance.reply_to.id),
                    'content': instance.reply_to.content,
                    'sender': {
                        'id': str(instance.reply_to.sender.id),
                        'username': instance.reply_to.sender.username,
                        'first_name': instance.reply_to.sender.first_name,
                        'last_name': instance.reply_to.sender.last_name
                    }
                } if instance.reply_to else None,
                'is_edited': instance.is_edited,
                'is_deleted': instance.is_deleted,
                'created_at': instance.created_at.isoformat(),
                'updated_at': instance.updated_at.isoformat(),
                'reactions': [],
                'is_read': False,
                'read_receipts': []
            }
        }
    )
    
    # Send notification to all participants except sender
    participants = ChatParticipant.objects.filter(room=room).exclude(user=instance.sender)
    
    for participant in participants:
        # Create notification
        Notification.objects.create(
            recipient=participant.user,
            sender=instance.sender,
            notification_type='message',
            content_type='chat_room',
            content_id=str(room.id),
            message=f"{instance.sender.first_name} {instance.sender.last_name}: {instance.content[:50]}..."
        )
        
        # Send personal notification
        async_to_sync(channel_layer.group_send)(
            f'user_{participant.user.id}',
            {
                'type': 'new_message',
                'room_id': str(room.id),
                'message_id': str(instance.id),
                'sender_id': str(instance.sender.id),
                'sender_username': instance.sender.username,
                'content': instance.content,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=MessageReaction)
def handle_reaction_created(sender, instance, created, **kwargs):
    """
    Handle message reaction events
    """
    if not created:
        return
    
    # Send WebSocket notification to room
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.message.room.id}',
        {
            'type': 'message_reaction',
            'reaction': {
                'id': str(instance.id),
                'message_id': str(instance.message.id),
                'user': {
                    'id': str(instance.user.id),
                    'username': instance.user.username,
                    'first_name': instance.user.first_name,
                    'last_name': instance.user.last_name
                },
                'emoji': instance.emoji,
                'created_at': instance.created_at.isoformat()
            }
        }
    )


@receiver(post_delete, sender=MessageReaction)
def handle_reaction_deleted(sender, instance, **kwargs):
    """
    Handle message reaction deletion events
    """
    # Send WebSocket notification to room
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.message.room.id}',
        {
            'type': 'message_reaction_removed',
            'reaction': {
                'message_id': str(instance.message.id),
                'user_id': str(instance.user.id),
                'emoji': instance.emoji
            }
        }
    )


@receiver(post_save, sender=MessageRead)
def handle_message_read(sender, instance, created, **kwargs):
    """
    Handle message read events
    """
    if not created:
        return
    
    # Send WebSocket notification to room
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.message.room.id}',
        {
            'type': 'messages_read',
            'user_id': str(instance.user.id),
            'username': instance.user.username,
            'message_id': str(instance.message.id),
            'read_at': instance.read_at.isoformat()
        }
    )


@receiver(post_save, sender=ChatRoom)
def handle_room_created(sender, instance, created, **kwargs):
    """
    Handle chat room creation events
    """
    if not created:
        return
    
    # Send notification to all participants except creator
    participants = ChatParticipant.objects.filter(room=instance).exclude(user=instance.created_by)
    
    for participant in participants:
        # Create notification
        Notification.objects.create(
            recipient=participant.user,
            sender=instance.created_by,
            notification_type='chat_request',
            content_type='chat_room',
            content_id=str(instance.id),
            message=f"{instance.created_by.first_name} {instance.created_by.last_name} started a conversation with you"
        )
        
        # Send personal notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{participant.user.id}',
            {
                'type': 'new_direct_message',
                'room_id': str(instance.id),
                'sender_id': str(instance.created_by.id),
                'sender_username': instance.created_by.username,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=ChatParticipant)
def handle_participant_joined(sender, instance, created, **kwargs):
    """
    Handle participant joining room events
    """
    if not created:
        return
    
    # Send notification to room about new participant
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.room.id}',
        {
            'type': 'participant_joined',
            'participant': {
                'id': str(instance.user.id),
                'username': instance.user.username,
                'first_name': instance.user.first_name,
                'last_name': instance.user.last_name,
                'role': instance.role,
                'joined_at': instance.joined_at.isoformat()
            }
        }
    )
