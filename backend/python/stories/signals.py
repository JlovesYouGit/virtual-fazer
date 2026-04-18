from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

from .models import (
    Story, StoryView, StoryLike, StoryReply, StoryShare,
    StoryHighlight, StoryMention, StoryAnalytics
)
from social.models import Notification
from users.models import UserActivity


@shared_task
def cleanup_expired_stories():
    """
    Background task to mark expired stories as inactive
    """
    now = timezone.now()
    expired_stories = Story.objects.filter(
        expires_at__lt=now,
        is_active=True,
        is_expired=False
    )
    
    count = expired_stories.count()
    expired_stories.update(
        is_expired=True,
        is_active=False
    )
    
    return f"Marked {count} stories as expired"


@shared_task
def generate_story_analytics():
    """
    Background task to generate daily analytics for stories
    """
    today = timezone.now().date()
    
    # Get all active stories
    active_stories = Story.objects.filter(
        is_active=True,
        created_at__date=today
    )
    
    for story in active_stories:
        # Calculate metrics
        total_views = story.view_count
        unique_viewers = StoryView.objects.filter(story=story).count()
        total_likes = story.likes_count
        total_shares = story.shares_count
        total_replies = story.replies_count
        
        # Calculate engagement rate
        engagement_rate = 0
        if total_views > 0:
            engagement_rate = ((total_likes + total_shares + total_replies) / total_views) * 100
        
        # Calculate completion rate (placeholder - would need tracking)
        completion_rate = 85.0  # Default assumption
        
        # Create or update analytics
        analytics, created = StoryAnalytics.objects.get_or_create(
            story=story,
            date=today,
            defaults={
                'views_count': total_views,
                'unique_viewers': unique_viewers,
                'likes_count': total_likes,
                'shares_count': total_shares,
                'replies_count': total_replies,
                'completion_rate': completion_rate,
                'engagement_rate': engagement_rate,
                'reach': unique_viewers
            }
        )
        
        if not created:
            analytics.views_count = total_views
            analytics.unique_viewers = unique_viewers
            analytics.likes_count = total_likes
            analytics.shares_count = total_shares
            analytics.replies_count = total_replies
            analytics.engagement_rate = engagement_rate
            analytics.reach = unique_viewers
            analytics.save()
    
    return f"Generated analytics for {active_stories.count()} stories"


@receiver(post_save, sender=Story)
def handle_story_created(sender, instance, created, **kwargs):
    """
    Handle story creation events
    """
    if not created:
        return
    
    # Schedule cleanup task for when story expires
    from celery import current_app
    current_app.send_task(
        'stories.signals.cleanup_expired_stories',
        eta=instance.expires_at + timedelta(minutes=5)
    )
    
    # Log activity
    UserActivity.objects.create(
        user=instance.user,
        activity_type='story',
        metadata={
            'story_id': str(instance.id),
            'content_type': instance.content_type,
            'caption': instance.caption[:100] if instance.caption else ''
        }
    )
    
    # Send WebSocket notification to followers
    channel_layer = get_channel_layer()
    followers = User.objects.filter(following__following=instance.user, following__is_active=True)
    
    for follower in followers:
        async_to_sync(channel_layer.group_send)(
            f'user_{follower.id}',
            {
                'type': 'new_story',
                'story_id': str(instance.id),
                'user_id': str(instance.user.id),
                'username': instance.user.username,
                'content_type': instance.content_type,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=StoryView)
def handle_story_viewed(sender, instance, created, **kwargs):
    """
    Handle story view events
    """
    if not created:
        return
    
    # Send WebSocket notification to story owner
    if instance.story.user != instance.viewer:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.story.user.id}',
            {
                'type': 'story_viewed',
                'story_id': str(instance.story.id),
                'viewer_id': str(instance.viewer.id),
                'viewer_username': instance.viewer.username,
                'timestamp': instance.viewed_at.isoformat()
            }
        )


@receiver(post_save, sender=StoryLike)
def handle_story_liked(sender, instance, created, **kwargs):
    """
    Handle story like events
    """
    if not created:
        return
    
    # Update story likes count
    Story.objects.filter(id=instance.story.id).update(
        likes_count=F('likes_count') + 1
    )
    
    # Create notification for story owner
    if instance.story.user != instance.user:
        Notification.objects.create(
            recipient=instance.story.user,
            sender=instance.user,
            notification_type='like',
            content_type='story',
            content_id=str(instance.story.id),
            message=f"{instance.user.username} liked your story"
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.story.user.id}',
            {
                'type': 'story_liked',
                'story_id': str(instance.story.id),
                'liker_id': str(instance.user.id),
                'liker_username': instance.user.username,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_delete, sender=StoryLike)
def handle_story_unliked(sender, instance, **kwargs):
    """
    Handle story unlike events
    """
    # Update story likes count
    Story.objects.filter(id=instance.story.id).update(
        likes_count=F('likes_count') - 1
    )


@receiver(post_save, sender=StoryReply)
def handle_story_replied(sender, instance, created, **kwargs):
    """
    Handle story reply events
    """
    if not created:
        return
    
    # Update story replies count
    Story.objects.filter(id=instance.story.id).update(
        replies_count=F('replies_count') + 1
    )
    
    # Create notification for story owner
    if instance.story.user != instance.user:
        Notification.objects.create(
            recipient=instance.story.user,
            sender=instance.user,
            notification_type='story_reply',
            content_type='story',
            content_id=str(instance.story.id),
            message=f"{instance.user.username} replied to your story: {instance.content[:50]}..."
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.story.user.id}',
            {
                'type': 'story_replied',
                'story_id': str(instance.story.id),
                'replier_id': str(instance.user.id),
                'replier_username': instance.user.username,
                'reply_id': str(instance.id),
                'content': instance.content,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=StoryShare)
def handle_story_shared(sender, instance, created, **kwargs):
    """
    Handle story share events
    """
    if not created:
        return
    
    # Update story shares count
    Story.objects.filter(id=instance.story.id).update(
        shares_count=F('shares_count') + 1
    )
    
    # Create notification for story owner
    if instance.story.user != instance.user:
        Notification.objects.create(
            recipient=instance.story.user,
            sender=instance.user,
            notification_type='share',
            content_type='story',
            content_id=str(instance.story.id),
            message=f"{instance.user.username} shared your story"
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.story.user.id}',
            {
                'type': 'story_shared',
                'story_id': str(instance.story.id),
                'sharer_id': str(instance.user.id),
                'sharer_username': instance.user.username,
                'share_type': instance.share_type,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=StoryMention)
def handle_story_mentioned(sender, instance, created, **kwargs):
    """
    Handle story mention events
    """
    if not created:
        return
    
    # Create notification for mentioned user
    if instance.mentioned_user != instance.story.user:
        Notification.objects.create(
            recipient=instance.mentioned_user,
            sender=instance.story.user,
            notification_type='mention',
            content_type='story',
            content_id=str(instance.story.id),
            message=f"{instance.story.user.username} mentioned you in their story"
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.mentioned_user.id}',
            {
                'type': 'story_mention',
                'story_id': str(instance.story.id),
                'sender_id': str(instance.story.user.id),
                'sender_username': instance.story.user.username,
                'timestamp': instance.created_at.isoformat()
            }
        )


@receiver(post_save, sender=StoryHighlight)
def handle_highlight_created(sender, instance, created, **kwargs):
    """
    Handle story highlight creation events
    """
    if not created:
        return
    
    # Log activity
    UserActivity.objects.create(
        user=instance.user,
        activity_type='highlight',
        metadata={
            'highlight_id': str(instance.id),
            'title': instance.title,
            'stories_count': instance.stories.count()
        }
    )
