import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageReaction, TypingIndicator

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Check if user is participant
        is_participant = await self.is_room_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Clear typing indicator
        await self.clear_typing_indicator()
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)
        elif message_type == 'reaction':
            await self.handle_reaction(text_data_json)
    
    async def handle_chat_message(self, data):
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to_id')
        
        # Create message
        message = await self.create_message(content, message_type, reply_to_id)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'message_type': message.message_type,
                    'sender': {
                        'id': str(message.sender.id),
                        'username': message.sender.username,
                        'profile_image': message.sender.profile_image.url if message.sender.profile_image else None
                    },
                    'created_at': message.created_at.isoformat(),
                    'reply_to': str(message.reply_to.id) if message.reply_to else None
                }
            }
        )
    
    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Update typing indicator
        await self.update_typing_indicator(is_typing)
        
        # Send typing indicator to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_reaction(self, data):
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        # Toggle reaction
        reaction = await self.toggle_reaction(message_id, emoji)
        
        if reaction:
            # Send reaction to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'reaction': {
                        'message_id': str(reaction.message.id),
                        'user_id': str(reaction.user.id),
                        'username': reaction.user.username,
                        'emoji': reaction.emoji,
                        'created_at': reaction.created_at.isoformat()
                    }
                }
            )
    
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def message_reaction(self, event):
        reaction = event['reaction']
        
        # Send reaction to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'reaction': reaction
        }))
    
    @database_sync_to_async
    def is_room_participant(self):
        try:
            room = ChatRoom.objects.get(
                id=self.room_id,
                participants=self.user,
                is_active=True
            )
            return True
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_message(self, content, message_type, reply_to_id):
        room = ChatRoom.objects.get(id=self.room_id)
        
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                pass
        
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type=message_type,
            reply_to=reply_to
        )
        
        # Update room's last message
        room.last_message = content
        room.last_message_time = message.created_at
        room.save()
        
        return message
    
    @database_sync_to_async
    def update_typing_indicator(self, is_typing):
        room = ChatRoom.objects.get(id=self.room_id)
        
        if is_typing:
            typing_indicator, created = TypingIndicator.objects.update_or_create(
                room=room,
                user=self.user,
                defaults={'is_typing': True}
            )
        else:
            TypingIndicator.objects.filter(
                room=room,
                user=self.user
            ).update(is_typing=False)
    
    @database_sync_to_async
    def clear_typing_indicator(self):
        room = ChatRoom.objects.get(id=self.room_id)
        TypingIndicator.objects.filter(
            room=room,
            user=self.user
        ).delete()
    
    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        try:
            message = Message.objects.get(id=message_id)
            room = ChatRoom.objects.get(id=self.room_id)
            
            # Check if reaction already exists
            existing_reaction = MessageReaction.objects.filter(
                message=message,
                user=self.user,
                emoji=emoji
            ).first()
            
            if existing_reaction:
                # Remove reaction
                existing_reaction.delete()
                return None
            else:
                # Add reaction
                reaction = MessageReaction.objects.create(
                    message=message,
                    user=self.user,
                    emoji=emoji
                )
                return reaction
        
        except (Message.DoesNotExist, ChatRoom.DoesNotExist):
            return None
