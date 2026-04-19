import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Comment, CommentLike, CommentNotification


class CommentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time comment updates
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Join user's personal channel for notifications
        self.user_channel_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_channel_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave user's personal channel
        if hasattr(self, 'user_channel_name'):
            await self.channel_layer.group_discard(
                self.user_channel_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_to_content':
                # Subscribe to content-specific comment updates
                content_type = data.get('content_type')
                content_id = data.get('content_id')
                
                if content_type and content_id:
                    self.content_channel_name = f"comments_{content_type}_{content_id}"
                    await self.channel_layer.group_add(
                        self.content_channel_name,
                        self.channel_name
                    )
                    
                    await self.send(text_data=json.dumps({
                        'type': 'subscribed',
                        'content_type': content_type,
                        'content_id': content_id
                    }))
            
            elif message_type == 'unsubscribe_from_content':
                # Unsubscribe from content-specific updates
                if hasattr(self, 'content_channel_name'):
                    await self.channel_layer.group_discard(
                        self.content_channel_name,
                        self.channel_name
                    )
                    delattr(self, 'content_channel_name')
                    
                    await self.send(text_data=json.dumps({
                        'type': 'unsubscribed'
                    }))
            
            elif message_type == 'typing':
                # Handle typing indicators
                content_type = data.get('content_type')
                content_id = data.get('content_id')
                is_typing = data.get('is_typing', False)
                
                if content_type and content_id:
                    await self.channel_layer.group_send(
                        f"comments_{content_type}_{content_id}",
                        {
                            'type': 'typing_indicator',
                            'user_id': str(self.user.id),
                            'username': self.user.username,
                            'is_typing': is_typing
                        }
                    )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def comment_notification(self, event):
        """Handle comment notifications"""
        await self.send(text_data=json.dumps({
            'type': 'comment_notification',
            'notification_type': event['notification_type'],
            'comment_id': event['comment_id'],
            'comment_text': event['comment_text'],
            'comment_user': event['comment_user'],
            'content_type': event['content_type'],
            'content_id': event['content_id'],
            'timestamp': event['timestamp']
        }))
    
    async def thread_update(self, event):
        """Handle thread updates"""
        await self.send(text_data=json.dumps({
            'type': 'thread_update',
            'comment_id': event['comment_id'],
            'comment_text': event['comment_text'],
            'comment_user': event['comment_user'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    async def new_comment(self, event):
        """Handle new comments in subscribed threads"""
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_id': event['comment_id'],
            'comment_text': event['comment_text'],
            'comment_user': event['comment_user'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicators"""
        # Don't send typing indicator to the user who is typing
        if str(self.user.id) != event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))


class CommentThreadConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for specific comment threads
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Extract content type and ID from URL
        self.content_type = self.scope['url_route']['kwargs']['content_type']
        self.content_id = self.scope['url_route']['kwargs']['content_id']
        
        # Join content-specific channel
        self.thread_channel_name = f"comments_{self.content_type}_{self.content_id}"
        await self.channel_layer.group_add(
            self.thread_channel_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave thread channel
        await self.channel_layer.group_discard(
            self.thread_channel_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages for the thread"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'typing':
                # Handle typing indicators
                is_typing = data.get('is_typing', False)
                
                await self.channel_layer.group_send(
                    self.thread_channel_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def new_comment(self, event):
        """Handle new comments in this thread"""
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_id': event['comment_id'],
            'comment_text': event['comment_text'],
            'comment_user': event['comment_user'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    async def comment_updated(self, event):
        """Handle comment updates"""
        await self.send(text_data=json.dumps({
            'type': 'comment_updated',
            'comment_id': event['comment_id'],
            'comment_text': event['comment_text'],
            'is_edited': event.get('is_edited', False),
            'timestamp': event['timestamp']
        }))
    
    async def comment_deleted(self, event):
        """Handle comment deletions"""
        await self.send(text_data=json.dumps({
            'type': 'comment_deleted',
            'comment_id': event['comment_id'],
            'timestamp': event['timestamp']
        }))
    
    async def comment_liked(self, event):
        """Handle comment likes"""
        await self.send(text_data=json.dumps({
            'type': 'comment_liked',
            'comment_id': event['comment_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicators"""
        # Don't send typing indicator to the user who is typing
        if str(self.user.id) != event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
