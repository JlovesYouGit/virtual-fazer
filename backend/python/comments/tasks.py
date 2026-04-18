from celery import shared_task
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import Comment, CommentNotification, CommentThread
from .utils import cleanup_old_notifications, auto_moderate_comment


@shared_task
def send_realtime_comment_update(user_id, notification_type, comment_id, comment_text, comment_user, content_type, content_id):
    """
    Send real-time comment update via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        
        # Send to user's personal channel
        user_channel = f"user_{user_id}"
        
        message = {
            'type': 'comment_update',
            'notification_type': notification_type,
            'comment_id': str(comment_id),
            'comment_text': comment_text,
            'comment_user': comment_user,
            'content_type': content_type,
            'content_id': str(content_id),
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            user_channel,
            {
                'type': 'comment_notification',
                'message': message
            }
        )
        
        # Also send to content's comment thread channel
        thread_channel = f"comments_{content_type}_{content_id}"
        
        thread_message = {
            'type': 'new_comment',
            'comment_id': str(comment_id),
            'comment_text': comment_text,
            'comment_user': comment_user,
            'user_id': str(user_id),
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            thread_channel,
            {
                'type': 'thread_update',
                'message': thread_message
            }
        )
        
    except Exception as e:
        print(f"Error sending realtime comment update: {e}")


@shared_task
def process_comment_notifications():
    """
    Process pending comment notifications
    """
    try:
        # Get unread notifications
        notifications = CommentNotification.objects.filter(is_read=False)
        
        for notification in notifications:
            # Send push notification if user has enabled them
            if hasattr(notification.recipient, 'profile'):
                if notification.recipient.profile.push_notifications_enabled:
                    send_push_notification.delay(
                        user_id=notification.recipient.id,
                        title=f"New {notification.get_notification_type_display()}",
                        message=f"{notification.comment.user.username}: {notification.comment.text[:50]}...",
                        data={
                            'type': 'comment',
                            'comment_id': str(notification.comment.id),
                            'content_type': notification.comment.content_type,
                            'content_id': str(notification.comment.content_id)
                        }
                    )
        
        return {
            'processed': notifications.count()
        }
        
    except Exception as e:
        print(f"Error processing comment notifications: {e}")
        return {'error': str(e)}


@shared_task
def send_push_notification(user_id, title, message, data=None):
    """
    Send push notification to user
    """
    try:
        # This would integrate with push notification service
        # For now, just log the notification
        print(f"Push notification to user {user_id}: {title} - {message}")
        
        # Store notification in database for in-app notifications
        # This would be handled by the notification system
        
    except Exception as e:
        print(f"Error sending push notification: {e}")


@shared_task
def update_comment_statistics():
    """
    Update comment statistics for all threads
    """
    try:
        threads = CommentThread.objects.all()
        updated_count = 0
        
        for thread in threads:
            thread.update_statistics()
            updated_count += 1
        
        return {
            'updated_threads': updated_count
        }
        
    except Exception as e:
        print(f"Error updating comment statistics: {e}")
        return {'error': str(e)}


@shared_task
def moderate_pending_comments():
    """
    Auto-moderate pending comments
    """
    try:
        pending_comments = Comment.objects.filter(moderation_status='pending')
        moderated_count = 0
        
        for comment in pending_comments:
            result = auto_moderate_comment(comment)
            if result['action'] != 'approved':
                moderated_count += 1
        
        return {
            'processed': pending_comments.count(),
            'moderated': moderated_count
        }
        
    except Exception as e:
        print(f"Error moderating pending comments: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_comment_data():
    """
    Clean up old comment data
    """
    try:
        # Clean up old notifications
        notifications_deleted = cleanup_old_notifications()
        
        # Clean up old comment reports (older than 90 days)
        from django.utils import timezone
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        from .models import CommentReport
        reports_deleted = CommentReport.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        return {
            'notifications_deleted': notifications_deleted,
            'reports_deleted': reports_deleted
        }
        
    except Exception as e:
        print(f"Error cleaning up old comment data: {e}")
        return {'error': str(e)}


@shared_task
def generate_comment_analytics():
    """
    Generate comment analytics for reporting
    """
    try:
        from django.utils import timezone
        from django.db.models import Count, Avg
        from .models import Comment, CommentLike
        
        # Daily stats for the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        daily_stats = []
        for i in range(30):
            date = (timezone.now() - timezone.timedelta(days=i)).date()
            
            comments_count = Comment.objects.filter(
                created_at__date=date,
                is_deleted=False,
                moderation_status='approved'
            ).count()
            
            likes_count = CommentLike.objects.filter(
                created_at__date=date
            ).count()
            
            daily_stats.append({
                'date': date.isoformat(),
                'comments': comments_count,
                'likes': likes_count
            })
        
        # Top content by comments
        top_content = Comment.objects.filter(
            is_deleted=False,
            moderation_status='approved',
            created_at__gte=thirty_days_ago
        ).values('content_type', 'content_id').annotate(
            comment_count=Count('id')
        ).order_by('-comment_count')[:10]
        
        # Most active users
        top_users = Comment.objects.filter(
            is_deleted=False,
            moderation_status='approved',
            created_at__gte=thirty_days_ago
        ).values('user__username').annotate(
            comment_count=Count('id')
        ).order_by('-comment_count')[:10]
        
        return {
            'daily_stats': daily_stats,
            'top_content': list(top_content),
            'top_users': list(top_users)
        }
        
    except Exception as e:
        print(f"Error generating comment analytics: {e}")
        return {'error': str(e)}


@shared_task
def send_comment_digest_emails():
    """
    Send daily/weekly comment digest emails
    """
    try:
        from django.utils import timezone
        from django.contrib.auth.models import User
        from django.template.loader import render_to_string
        from django.core.mail import send_mail
        
        # Get users who want comment digests
        users = User.objects.filter(
            profile__comment_digest_enabled=True
        )
        
        for user in users:
            # Get user's comment activity from last 24 hours
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            
            user_comments = Comment.objects.filter(
                user=user,
                created_at__gte=twenty_four_hours_ago,
                is_deleted=False,
                moderation_status='approved'
            )
            
            # Get replies to user's comments
            replies_to_user = Comment.objects.filter(
                parent__user=user,
                created_at__gte=twenty_four_hours_ago,
                is_deleted=False,
                moderation_status='approved'
            )
            
            # Get likes on user's comments
            likes_on_user_comments = CommentLike.objects.filter(
                comment__user=user,
                created_at__gte=twenty_four_hours_ago
            )
            
            if user_comments.exists() or replies_to_user.exists() or likes_on_user_comments.exists():
                # Render email template
                context = {
                    'user': user,
                    'user_comments': user_comments[:5],
                    'replies_to_user': replies_to_user[:5],
                    'likes_count': likes_on_user_comments.count(),
                    'reply_count': replies_to_user.count(),
                    'comment_count': user_comments.count()
                }
                
                html_content = render_to_string('emails/comment_digest.html', context)
                text_content = render_to_string('emails/comment_digest.txt', context)
                
                # Send email
                send_mail(
                    subject='Your Comment Activity Digest',
                    message=text_content,
                    from_email='noreply@instagran.com',
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False
                )
        
        return {
            'emails_sent': users.count()
        }
        
    except Exception as e:
        print(f"Error sending comment digest emails: {e}")
        return {'error': str(e)}


@shared_task
def detect_comment_spam_batch():
    """
    Batch process comment spam detection
    """
    try:
        from .models import Comment
        from .utils import detect_spam_comment
        
        # Get recent comments not yet checked for spam
        recent_comments = Comment.objects.filter(
            is_deleted=False,
            moderation_status='approved'
        ).order_by('-created_at')[:100]
        
        spam_detected = 0
        
        for comment in recent_comments:
            spam_result = detect_spam_comment(comment.text, comment.user)
            
            if spam_result['is_spam']:
                comment.moderation_status = 'rejected'
                comment.is_flagged = True
                comment.save()
                spam_detected += 1
        
        return {
            'checked': recent_comments.count(),
            'spam_detected': spam_detected
        }
        
    except Exception as e:
        print(f"Error in batch spam detection: {e}")
        return {'error': str(e)}


# Schedule periodic tasks
from celery.schedules import crontab

# Schedule comment-related periodic tasks
process_comment_notifications.schedule = crontab(minute='*/5')  # Every 5 minutes
update_comment_statistics.schedule = crontab(minute=0)  # Every hour
moderate_pending_comments.schedule = crontab(minute='*/10')  # Every 10 minutes
cleanup_old_comment_data.schedule = crontab(hour=2, minute=0)  # Daily at 2 AM
generate_comment_analytics.schedule = crontab(hour=1, minute=0)  # Daily at 1 AM
send_comment_digest_emails.schedule = crontab(hour=8, minute=0)  # Daily at 8 AM
detect_comment_spam_batch.schedule = crontab(minute='*/15')  # Every 15 minutes
