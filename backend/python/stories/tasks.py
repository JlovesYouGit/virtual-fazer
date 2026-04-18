from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Count, Q, Avg
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Story, StoryView, StoryLike, StoryReply, StoryShare, StoryAnalytics
from social.models import Notification
from users.models import User


@shared_task
def cleanup_expired_stories():
    """
    Background task to mark expired stories as inactive and send notifications
    """
    now = timezone.now()
    expired_stories = Story.objects.filter(
        expires_at__lt=now,
        is_active=True,
        is_expired=False
    )
    
    count = expired_stories.count()
    
    # Mark stories as expired
    expired_stories.update(
        is_expired=True,
        is_active=False
    )
    
    # Send notifications to story owners about expired stories
    channel_layer = get_channel_layer()
    for story in expired_stories:
        async_to_sync(channel_layer.group_send)(
            f'user_{story.user.id}',
            {
                'type': 'story_expired',
                'story_id': str(story.id),
                'timestamp': now.isoformat()
            }
        )
    
    return f"Marked {count} stories as expired"


@shared_task
def generate_story_analytics():
    """
    Background task to generate daily analytics for stories
    """
    today = timezone.now().date()
    
    # Get all active stories created today
    active_stories = Story.objects.filter(
        is_active=True,
        created_at__date=today
    )
    
    analytics_count = 0
    
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
        
        analytics_count += 1
    
    return f"Generated analytics for {analytics_count} stories"


@shared_task
def send_story_digest_notifications():
    """
    Send daily digest notifications about story activity
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get users with active stories
    users_with_stories = User.objects.filter(
        stories__is_active=True,
        stories__created_at__date=yesterday
    ).distinct()
    
    notifications_sent = 0
    
    for user in users_with_stories:
        # Get story stats for yesterday
        user_stories = Story.objects.filter(
            user=user,
            created_at__date=yesterday,
            is_active=True
        )
        
        if not user_stories.exists():
            continue
        
        total_views = sum(story.view_count for story in user_stories)
        total_likes = sum(story.likes_count for story in user_stories)
        total_replies = sum(story.replies_count for story in user_stories)
        total_shares = sum(story.shares_count for story in user_stories)
        
        # Create digest notification
        Notification.objects.create(
            recipient=user,
            sender=user,  # Self notification
            notification_type='story_digest',
            content_type='story',
            message=f"Your stories from yesterday: {total_views} views, {total_likes} likes, {total_replies} replies, {total_shares} shares"
        )
        
        notifications_sent += 1
    
    return f"Sent {notifications_sent} story digest notifications"


@shared_task
def process_story_view_analytics():
    """
    Process detailed view analytics for stories
    """
    # Get stories with significant view activity
    popular_stories = Story.objects.filter(
        is_active=True,
        view_count__gt=10,  # Stories with more than 10 views
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-view_count')[:100]
    
    analytics_processed = 0
    
    for story in popular_stories:
        # Calculate view patterns
        views = StoryView.objects.filter(story=story)
        
        # Average view duration
        avg_duration = views.aggregate(avg_duration=Avg('view_duration'))['avg_duration'] or 0
        
        # View completion rate (views that lasted more than 10 seconds)
        completed_views = views.filter(view_duration__gt=10).count()
        completion_rate = (completed_views / views.count() * 100) if views.count() > 0 else 0
        
        # Update story analytics with detailed metrics
        today = timezone.now().date()
        analytics, created = StoryAnalytics.objects.get_or_create(
            story=story,
            date=today,
            defaults={
                'views_count': story.view_count,
                'unique_viewers': views.count(),
                'completion_rate': completion_rate,
                'reach': views.count()
            }
        )
        
        if not created:
            analytics.completion_rate = completion_rate
            analytics.save()
        
        analytics_processed += 1
    
    return f"Processed analytics for {analytics_processed} popular stories"


@shared_task
def cleanup_old_story_analytics():
    """
    Clean up old story analytics data (keep only last 90 days)
    """
    cutoff_date = timezone.now().date() - timedelta(days=90)
    
    deleted_count = StoryAnalytics.objects.filter(
        date__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old story analytics records"


@shared_task
def generate_trending_stories_report():
    """
    Generate daily trending stories report
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get top performing stories from yesterday
    trending_stories = Story.objects.filter(
        created_at__date=yesterday,
        is_active=True
    ).annotate(
        engagement_score=F('likes_count') + F('shares_count') + F('replies_count') + (F('view_count') * 0.1)
    ).order_by('-engagement_score')[:20]
    
    # Create a report (could be saved to a file or sent as notification)
    report_data = []
    for story in trending_stories:
        report_data.append({
            'story_id': str(story.id),
            'user': story.user.username,
            'content_type': story.content_type,
            'views': story.view_count,
            'likes': story.likes_count,
            'shares': story.shares_count,
            'replies': story.replies_count,
            'engagement_score': story.likes_count + story.shares_count + story.replies_count + (story.view_count * 0.1)
        })
    
    # Send notification to admin users about trending stories
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    channel_layer = get_channel_layer()
    
    for admin in admin_users:
        async_to_sync(channel_layer.group_send)(
            f'user_{admin.id}',
            {
                'type': 'trending_stories_report',
                'date': yesterday.isoformat(),
                'stories': report_data[:10],  # Top 10 stories
                'timestamp': timezone.now().isoformat()
            }
        )
    
    return f"Generated trending stories report for {len(report_data)} stories"


@shared_task
def send_story_expiration_reminders():
    """
    Send reminders to users about stories that will expire soon
    """
    # Get stories that will expire in the next 2 hours
    soon_to_expire = Story.objects.filter(
        expires_at__lte=timezone.now() + timedelta(hours=2),
        expires_at__gt=timezone.now(),
        is_active=True,
        is_expired=False
    )
    
    reminders_sent = 0
    channel_layer = get_channel_layer()
    
    for story in soon_to_expire:
        # Send reminder to story owner
        async_to_sync(channel_layer.group_send)(
            f'user_{story.user.id}',
            {
                'type': 'story_expiring_soon',
                'story_id': str(story.id),
                'expires_at': story.expires_at.isoformat(),
                'time_remaining': str(story.time_remaining),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        reminders_sent += 1
    
    return f"Sent {reminders_sent} story expiration reminders"


@shared_task
def update_story_engagement_metrics():
    """
    Update engagement metrics for all active stories
    """
    active_stories = Story.objects.filter(
        is_active=True,
        is_expired=False
    )
    
    updated_count = 0
    
    for story in active_stories:
        # Calculate engagement rate
        total_interactions = story.likes_count + story.shares_count + story.replies_count
        engagement_rate = (total_interactions / story.view_count * 100) if story.view_count > 0 else 0
        
        # Update story with engagement metrics (if you add these fields to the model)
        # For now, we'll just log this information
        updated_count += 1
    
    return f"Updated engagement metrics for {updated_count} stories"


# Schedule periodic tasks
from celery.schedules import crontab

# These would be configured in your Celery beat schedule
CELERYBEAT_SCHEDULE = {
    'cleanup-expired-stories': {
        'task': 'stories.tasks.cleanup_expired_stories',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate-story-analytics': {
        'task': 'stories.tasks.generate_story_analytics',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'send-story-digest-notifications': {
        'task': 'stories.tasks.send_story_digest_notifications',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'process-story-view-analytics': {
        'task': 'stories.tasks.process_story_view_analytics',
        'schedule': crontab(hour='*/2', minute=0),  # Every 2 hours
    },
    'cleanup-old-story-analytics': {
        'task': 'stories.tasks.cleanup_old_story_analytics',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
    'generate-trending-stories-report': {
        'task': 'stories.tasks.generate_trending_stories_report',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'send-story-expiration-reminders': {
        'task': 'stories.tasks.send_story_expiration_reminders',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'update-story-engagement-metrics': {
        'task': 'stories.tasks.update_story_engagement_metrics',
        'schedule': crontab(hour='*/1', minute=0),  # Every hour
    },
}
