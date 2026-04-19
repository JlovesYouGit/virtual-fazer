import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Follow, Like, Share, UserProfile


class SocialConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time social updates
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
                # Subscribe to content-specific social updates
                content_type = data.get('content_type')
                content_id = data.get('content_id')
                
                if content_type and content_id:
                    self.content_channel_name = f"social_{content_type}_{content_id}"
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
            
            elif message_type == 'subscribe_to_user':
                # Subscribe to user-specific updates
                target_user_id = data.get('user_id')
                
                if target_user_id:
                    self.user_subscription_channel = f"user_updates_{target_user_id}"
                    await self.channel_layer.group_add(
                        self.user_subscription_channel,
                        self.channel_name
                    )
                    
                    await self.send(text_data=json.dumps({
                        'type': 'subscribed_to_user',
                        'user_id': target_user_id
                    }))
            
            elif message_type == 'unsubscribe_from_user':
                # Unsubscribe from user-specific updates
                if hasattr(self, 'user_subscription_channel'):
                    await self.channel_layer.group_discard(
                        self.user_subscription_channel,
                        self.channel_name
                    )
                    delattr(self, 'user_subscription_channel')
                    
                    await self.send(text_data=json.dumps({
                        'type': 'unsubscribed_from_user'
                    }))
        
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
    
    async def social_update(self, event):
        """Handle social notifications"""
        await self.send(text_data=json.dumps({
            'type': event['notification_type'],
            'sender_id': event.get('sender_id'),
            'sender_username': event.get('sender_username'),
            'content_type': event.get('content_type'),
            'content_id': event.get('content_id'),
            'timestamp': event['timestamp']
        }))
    
    async def stats_update(self, event):
        """Handle user stats updates"""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': event,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def social_content_update(self, event):
        """Handle content-specific social updates"""
        await self.send(text_data=json.dumps({
            'type': 'content_update',
            'content_type': event.get('content_type'),
            'content_id': event.get('content_id'),
            'stats': event.get('stats'),
            'timestamp': event['timestamp']
        }))
    
    async def user_update(self, event):
        """Handle user-specific updates"""
        await self.send(text_data=json.dumps({
            'type': 'user_update',
            'user_id': event.get('user_id'),
            'update_type': event.get('update_type'),
            'data': event.get('data'),
            'timestamp': event['timestamp']
        }))


class ContentSocialConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for specific content social interactions
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
        self.content_channel_name = f"social_{self.content_type}_{self.content_id}"
        await self.channel_layer.group_add(
            self.content_channel_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave content channel
        await self.channel_layer.group_discard(
            self.content_channel_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages for the content"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'like_update':
                # Handle like/unlike updates
                await self.channel_layer.group_send(
                    self.content_channel_name,
                    {
                        'type': 'content_like_update',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                        'is_liked': data.get('is_liked', False),
                        'timestamp': timezone.now().isoformat()
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
    
    async def content_stats_update(self, event):
        """Handle content statistics updates"""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': event.get('stats'),
            'timestamp': event['timestamp']
        }))
    
    async def content_like_update(self, event):
        """Handle content like updates"""
        await self.send(text_data=json.dumps({
            'type': 'like_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_liked': event['is_liked'],
            'timestamp': event['timestamp']
        }))
    
    async def content_comment_update(self, event):
        """Handle content comment updates"""
        await self.send(text_data=json.dumps({
            'type': 'comment_update',
            'user_id': event.get('user_id'),
            'username': event.get('username'),
            'comment_id': event.get('comment_id'),
            'action': event.get('action'),  # 'add', 'edit', 'delete'
            'timestamp': event['timestamp']
        }))
    
    async def content_share_update(self, event):
        """Handle content share updates"""
        await self.send(text_data=json.dumps({
            'type': 'share_update',
            'user_id': event.get('user_id'),
            'username': event.get('username'),
            'timestamp': event['timestamp']
        }))


class UserSocialConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific social updates
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Extract target user ID from URL
        self.target_user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Join user-specific channel
        self.user_channel_name = f"user_updates_{self.target_user_id}"
        await self.channel_layer.group_add(
            self.user_channel_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave user channel
        await self.channel_layer.group_discard(
            self.user_channel_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages for user updates"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'follow_update':
                # Handle follow/unfollow updates
                await self.channel_layer.group_send(
                    self.user_channel_name,
                    {
                        'type': 'user_follow_update',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                        'is_following': data.get('is_following', False),
                        'timestamp': timezone.now().isoformat()
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
    
    async def user_update(self, event):
        """Handle user profile updates"""
        await self.send(text_data=json.dumps({
            'type': 'profile_update',
            'update_type': event.get('update_type'),
            'data': event.get('data'),
            'timestamp': event['timestamp']
        }))
    
    async def user_follow_update(self, event):
        """Handle user follow updates"""
        await self.send(text_data=json.dumps({
            'type': 'follow_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_following': event['is_following'],
            'timestamp': event['timestamp']
        }))
    
    async def user_stats_update(self, event):
        """Handle user statistics updates"""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': event.get('stats'),
            'timestamp': event['timestamp']
        }))
