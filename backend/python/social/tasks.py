from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import (
    UserProfile, Follow, Like, Share, FollowRequest, 
    UserActivity, Notification
)
from .utils import update_user_stats, get_trending_users, calculate_engagement_rate


@shared_task
def update_user_stats_task(user_id):
    """
    Update user statistics (background task)
    """
    return update_user_stats(user_id)


@shared_task
def send_follow_notification(follower_id, following_id):
    """
    Send follow notification via WebSocket
    """
    try:
        follower = User.objects.get(id=follower_id)
        following = User.objects.get(id=following_id)
        
        channel_layer = get_channel_layer()
        
        # Send notification to following user
        message = {
            'type': 'follow_notification',
            'follower_id': str(follower_id),
            'follower_username': follower.username,
            'follower_name': f"{follower.first_name} {follower.last_name}",
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{following_id}",
            {
                'type': 'social_update',
                'message': message
            }
        )
        
        # Update follower count in real-time
        profile = following.social_profile
        async_to_sync(channel_layer.group_send)(
            f"user_{following_id}",
            {
                'type': 'stats_update',
                'message': {
                    'followers_count': profile.followers_count
                }
            }
        )
        
    except Exception as e:
        print(f"Error sending follow notification: {e}")


@shared_task
def send_like_notification(user_id, content_type, content_id, content_owner_id):
    """
    Send like notification via WebSocket
    """
    try:
        user = User.objects.get(id=user_id)
        
        channel_layer = get_channel_layer()
        
        # Send notification to content owner
        message = {
            'type': 'like_notification',
            'user_id': str(user_id),
            'username': user.username,
            'user_name': f"{user.first_name} {user.last_name}",
            'content_type': content_type,
            'content_id': str(content_id),
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{content_owner_id}",
            {
                'type': 'social_update',
                'message': message
            }
        )
        
        # Update like count for content
        from .models import Like
        like_count = Like.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        async_to_sync(channel_layer.group_send)(
            f"social_{content_type}_{content_id}",
            {
                'type': 'content_stats_update',
                'message': {
                    'likes_count': like_count
                }
            }
        )
        
    except Exception as e:
        print(f"Error sending like notification: {e}")


@shared_task
def send_comment_notification(user_id, content_type, content_id, content_owner_id, comment_text):
    """
    Send comment notification via WebSocket
    """
    try:
        user = User.objects.get(id=user_id)
        
        channel_layer = get_channel_layer()
        
        # Send notification to content owner
        message = {
            'type': 'comment_notification',
            'user_id': str(user_id),
            'username': user.username,
            'user_name': f"{user.first_name} {user.last_name}",
            'content_type': content_type,
            'content_id': str(content_id),
            'comment_text': comment_text[:100],  # First 100 chars
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{content_owner_id}",
            {
                'type': 'social_update',
                'message': message
            }
        )
        
        # Update comment count for content
        # This would need integration with comment system
        # comment_count = Comment.objects.filter(
        #     content_type=content_type,
        #     content_id=content_id
        # ).count()
        
        # async_to_sync(channel_layer.group_send)(
        #     f"social_{content_type}_{content_id}",
        #     {
        #         'type': 'content_stats_update',
        #         'message': {
        #             'comments_count': comment_count
        #         }
        #     }
        # )
        
    except Exception as e:
        print(f"Error sending comment notification: {e}")


@shared_task
def send_share_notification(user_id, content_type, content_id, content_owner_id):
    """
    Send share notification via WebSocket
    """
    try:
        user = User.objects.get(id=user_id)
        
        channel_layer = get_channel_layer()
        
        # Send notification to content owner
        message = {
            'type': 'share_notification',
            'user_id': str(user_id),
            'username': user.username,
            'user_name': f"{user.first_name} {user.last_name}",
            'content_type': content_type,
            'content_id': str(content_id),
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{content_owner_id}",
            {
                'type': 'social_update',
                'message': message
            }
        )
        
        # Update share count for content
        from .models import Share
        share_count = Share.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        async_to_sync(channel_layer.group_send)(
            f"social_{content_type}_{content_id}",
            {
                'type': 'content_stats_update',
                'message': {
                    'shares_count': share_count
                }
            }
        )
        
    except Exception as e:
        print(f"Error sending share notification: {e}")


@shared_task
def update_content_stats(content_type, content_id):
    """
    Update content statistics and send real-time updates
    """
    try:
        channel_layer = get_channel_layer()
        
        # Get current stats
        from .models import Like, Share
        # Import comment system when available
        # from comments.models import Comment
        
        likes_count = Like.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        shares_count = Share.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        # comments_count = Comment.objects.filter(
        #     content_type=content_type,
        #     content_id=content_id
        # ).count()
        
        stats_message = {
            'type': 'content_stats_update',
            'content_type': content_type,
            'content_id': str(content_id),
            'stats': {
                'likes_count': likes_count,
                'shares_count': shares_count,
                # 'comments_count': comments_count
            },
            'timestamp': timezone.now().isoformat()
        }
        
        # Send to content-specific channel
        async_to_sync(channel_layer.group_send)(
            f"social_{content_type}_{content_id}",
            {
                'type': 'social_content_update',
                'message': stats_message
            }
        )
        
    except Exception as e:
        print(f"Error updating content stats: {e}")


@shared_task
def calculate_user_engagement(user_id):
    """
    Calculate user engagement metrics
    """
    try:
        user = User.objects.get(id=user_id)
        
        engagement_rate = calculate_engagement_rate(user_id)
        
        # Update user profile with engagement rate
        profile = user.social_profile
        # Add engagement_rate field to profile if needed
        # profile.engagement_rate = engagement_rate
        # profile.save()
        
        return {
            'user_id': user_id,
            'engagement_rate': engagement_rate,
            'followers_count': profile.followers_count,
            'following_count': profile.following_count
        }
        
    except User.DoesNotExist:
        return {'error': f'User {user_id} not found'}
    except Exception as e:
        return {'error': str(e)}


@shared_task
def generate_trending_users_report():
    """
    Generate trending users report
    """
    try:
        trending_users = get_trending_users(limit=20)
        
        report_data = []
        for user in trending_users:
            profile = user.social_profile
            engagement_rate = calculate_engagement_rate(user.id)
            
            report_data.append({
                'user_id': user.id,
                'username': user.username,
                'followers_count': profile.followers_count,
                'engagement_rate': engagement_rate,
                'follower_growth': getattr(user, 'follower_growth', 0)
            })
        
        return {
            'generated_at': timezone.now().isoformat(),
            'trending_users': report_data
        }
        
    except Exception as e:
        return {'error': str(e)}


@shared_task
def cleanup_old_social_data():
    """
    Clean up old social data
    """
    try:
        # Clean up old notifications
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        notifications_deleted = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        # Clean up old activities
        activity_cutoff = timezone.now() - timezone.timedelta(days=90)
        activities_deleted = UserActivity.objects.filter(
            created_at__lt=activity_cutoff
        ).delete()[0]
        
        return {
            'notifications_deleted': notifications_deleted,
            'activities_deleted': activities_deleted
        }
        
    except Exception as e:
        return {'error': str(e)}


@shared_task
def update_all_content_stats():
    """
    Update statistics for all content
    """
    try:
        from reels.models import Reel
        
        reels = Reel.objects.all()
        updated_count = 0
        
        for reel in reels:
            # Update stats for each reel
            update_content_stats.delay('reel', str(reel.id))
            updated_count += 1
        
        return {
            'updated_content': updated_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}


@shared_task
def send_digest_notifications():
    """
    Send daily digest notifications to users
    """
    try:
        users = User.objects.filter(
            social_profile__show_activity_status=True
        )
        
        sent_count = 0
        
        for user in users:
            # Get recent activity
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            
            # New followers
            new_followers = Follow.objects.filter(
                following=user,
                created_at__gte=twenty_four_hours_ago
            ).count()
            
            # New likes on user's content
            from reels.models import Reel
            user_reels = Reel.objects.filter(user=user)
            new_likes = Like.objects.filter(
                content_type='reel',
                content_id__in=user_reels.values_list('id', flat=True),
                created_at__gte=twenty_four_hours_ago
            ).count()
            
            # Only send digest if there's activity
            if new_followers > 0 or new_likes > 0:
                channel_layer = get_channel_layer()
                
                digest_message = {
                    'type': 'digest_notification',
                    'new_followers': new_followers,
                    'new_likes': new_likes,
                    'timestamp': timezone.now().isoformat()
                }
                
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}",
                    {
                        'type': 'social_update',
                        'message': digest_message
                    }
                )
                
                sent_count += 1
        
        return {
            'sent_digests': sent_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}


@shared_task
def process_follow_request_notification(request_id, action):
    """
    Process follow request notification
    """
    try:
        from .models import FollowRequest
        
        follow_request = FollowRequest.objects.get(id=request_id)
        
        if action == 'accepted':
            # Send acceptance notification
            send_follow_notification.delay(
                follower_id=follow_request.target.id,
                following_id=follow_request.requester.id
            )
        elif action == 'declined':
            # Send decline notification
            channel_layer = get_channel_layer()
            
            decline_message = {
                'type': 'follow_request_declined',
                'target_username': follow_request.target.username,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"user_{follow_request.requester.id}",
                {
                    'type': 'social_update',
                    'message': decline_message
                }
            )
        
        return {
            'request_id': request_id,
            'action': action,
            'processed': True
        }
        
    except FollowRequest.DoesNotExist:
        return {'error': 'Follow request not found'}
    except Exception as e:
        return {'error': str(e)}


# Schedule periodic tasks
from celery.schedules import crontab

# Schedule social-related periodic tasks
update_all_content_stats.schedule = crontab(minute='*/30')  # Every 30 minutes
cleanup_old_social_data.schedule = crontab(hour=2, minute=0)  # Daily at 2 AM
generate_trending_users_report.schedule = crontab(hour=1, minute=0)  # Daily at 1 AM
send_digest_notifications.schedule = crontab(hour=20, minute=0)  # Daily at 8 PM
calculate_user_engagement.schedule = crontab(minute='*/15')  # Every 15 minutes
