from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Comment, CommentLike, CommentThread, CommentNotification
from .tasks import update_comment_statistics, send_realtime_comment_update
from .utils import send_comment_notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Comment)
def handle_comment_created(sender, instance, created, **kwargs):
    """
    Handle comment creation events
    """
    if created:
        # Update thread statistics
        try:
            thread, thread_created = CommentThread.objects.get_or_create(
                content_type=instance.content_type,
                content_id=instance.content_id
            )
            thread.update_statistics()
        except Exception as e:
            logger.error(f"Failed to update thread statistics: {e}")
        
        # Send real-time update to content thread
        try:
            send_realtime_comment_update.delay(
                user_id=instance.user.id,
                notification_type='new_comment',
                comment_id=instance.id,
                comment_text=instance.text[:100],
                comment_user=instance.user.username,
                content_type=instance.content_type,
                content_id=instance.content_id
            )
        except Exception as e:
            logger.error(f"Failed to send real-time comment update: {e}")


@receiver(post_save, sender=CommentLike)
def handle_comment_liked(sender, instance, created, **kwargs):
    """
    Handle comment like events
    """
    if created:
        # Update comment's like count
        try:
            comment = instance.comment
            comment.likes_count = CommentLike.objects.filter(comment=comment).count()
            comment.save(update_fields=['likes_count'])
            
            # Send notification to comment author (if not self-like)
            if comment.user != instance.user:
                send_comment_notification(comment.user, comment, 'like')
                
                # Send real-time update
                send_realtime_comment_update.delay(
                    user_id=comment.user.id,
                    notification_type='like',
                    comment_id=comment.id,
                    comment_text=comment.text[:100],
                    comment_user=instance.user.username,
                    content_type=comment.content_type,
                    content_id=comment.content_id
                )
                
        except Exception as e:
            logger.error(f"Failed to handle comment like: {e}")


@receiver(post_delete, sender=CommentLike)
def handle_comment_unliked(sender, instance, **kwargs):
    """
    Handle comment unlike events
    """
    try:
        comment = instance.comment
        comment.likes_count = CommentLike.objects.filter(comment=comment).count()
        comment.save(update_fields=['likes_count'])
    except Exception as e:
        logger.error(f"Failed to handle comment unlike: {e}")


@receiver(post_save, sender=User)
def create_user_comment_settings(sender, instance, created, **kwargs):
    """
    Create default comment settings for new users
    """
    if created:
        try:
            # This would create user profile with comment preferences
            # if you have a user profile model
            pass
        except Exception as e:
            logger.error(f"Failed to create comment settings for user {instance.username}: {e}")


@receiver(post_save, sender=CommentThread)
def handle_thread_updated(sender, instance, created, **kwargs):
    """
    Handle thread update events
    """
    if not created:
        # Thread was updated, send real-time update to subscribers
        try:
            send_realtime_comment_update.delay(
                user_id=instance.last_comment_by.id if instance.last_comment_by else None,
                notification_type='thread_update',
                comment_id=None,
                comment_text='',
                comment_user=instance.last_comment_by.username if instance.last_comment_by else '',
                content_type=instance.content_type,
                content_id=instance.content_id
            )
        except Exception as e:
            logger.error(f"Failed to send thread update: {e}")


@receiver(post_delete, sender=Comment)
def handle_comment_deleted(sender, instance, **kwargs):
    """
    Handle comment deletion events
    """
    try:
        # Update thread statistics
        try:
            thread = CommentThread.objects.filter(
                content_type=instance.content_type,
                content_id=instance.content_id
            ).first()
            if thread:
                thread.update_statistics()
        except Exception as e:
            logger.error(f"Failed to update thread statistics after deletion: {e}")
        
        # Clean up related objects
        CommentLike.objects.filter(comment=instance).delete()
        CommentNotification.objects.filter(comment=instance).delete()
        
    except Exception as e:
        logger.error(f"Failed to handle comment deletion: {e}")


@receiver(post_save, sender=CommentNotification)
def handle_notification_created(sender, instance, created, **kwargs):
    """
    Handle notification creation events
    """
    if created:
        # Send real-time notification
        try:
            send_realtime_comment_update.delay(
                user_id=instance.recipient.id,
                notification_type=instance.notification_type,
                comment_id=instance.comment.id,
                comment_text=instance.comment.text[:100],
                comment_user=instance.comment.user.username,
                content_type=instance.comment.content_type,
                content_id=instance.comment.content_id
            )
        except Exception as e:
            logger.error(f"Failed to send notification update: {e}")
