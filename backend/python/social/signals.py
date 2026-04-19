from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import UserProfile, Follow, Like, Share, FollowRequest, UserActivity, Notification
from .tasks import (
    send_follow_notification, send_like_notification, 
    send_comment_notification, send_share_notification,
    update_content_stats, update_user_stats_task
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when user is created
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
        logger.info(f"Created profile for user {instance.username}")


@receiver(post_save, sender=Follow)
def handle_follow_created(sender, instance, created, **kwargs):
    """
    Handle follow creation - update stats and send notifications
    """
    if created:
        # Update user stats asynchronously
        update_user_stats_task.delay(instance.follower.id)
        update_user_stats_task.delay(instance.following.id)
        
        # Send real-time notification
        send_follow_notification.delay(
            follower_id=instance.follower.id,
            following_id=instance.following.id
        )
        
        # Create activity record
        UserActivity.objects.create(
            user=instance.follower,
            activity_type='follow',
            target_user=instance.following
        )
        
        # Create notification
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow',
            message=f"{instance.follower.username} started following you"
        )
        
        logger.info(f"User {instance.follower.username} followed {instance.following.username}")


@receiver(post_delete, sender=Follow)
def handle_follow_deleted(sender, instance, **kwargs):
    """
    Handle follow deletion - update stats
    """
    # Update user stats asynchronously
    update_user_stats_task.delay(instance.follower.id)
    update_user_stats_task.delay(instance.following.id)
    
    logger.info(f"User {instance.follower.username} unfollowed {instance.following.username}")


@receiver(post_save, sender=Like)
def handle_like_created(sender, instance, created, **kwargs):
    """
    Handle like creation - update stats and send notifications
    """
    if created:
        # Update content stats asynchronously
        update_content_stats.delay(instance.content_type, instance.content_id)
        
        # Get content owner for notification
        content_owner = None
        if instance.content_type == 'reel':
            try:
                from reels.models import Reel
                reel = Reel.objects.get(id=instance.content_id)
                content_owner = reel.user
            except Reel.DoesNotExist:
                pass
        elif instance.content_type == 'post':
            # Similar for posts when implemented
            pass
        
        # Send notification to content owner
        if content_owner and content_owner != instance.user:
            send_like_notification.delay(
                user_id=instance.user.id,
                content_type=instance.content_type,
                content_id=instance.content_id,
                content_owner_id=content_owner.id
            )
            
            # Create notification
            Notification.objects.create(
                recipient=content_owner,
                sender=instance.user,
                notification_type='like',
                content_type=instance.content_type,
                content_id=instance.content_id,
                message=f"{instance.user.username} liked your {instance.content_type}"
            )
        
        # Create activity record
        UserActivity.objects.create(
            user=instance.user,
            activity_type='like',
            content_type=instance.content_type,
            content_id=instance.content_id
        )
        
        logger.info(f"User {instance.user.username} liked {instance.content_type} {instance.content_id}")


@receiver(post_delete, sender=Like)
def handle_like_deleted(sender, instance, **kwargs):
    """
    Handle like deletion - update stats
    """
    # Update content stats asynchronously
    update_content_stats.delay(instance.content_type, instance.content_id)
    
    logger.info(f"User {instance.user.username} unliked {instance.content_type} {instance.content_id}")


@receiver(post_save, sender=Share)
def handle_share_created(sender, instance, created, **kwargs):
    """
    Handle share creation - update stats and send notifications
    """
    if created:
        # Update content stats asynchronously
        update_content_stats.delay(instance.content_type, instance.content_id)
        
        # Get content owner for notification
        content_owner = None
        if instance.content_type == 'reel':
            try:
                from reels.models import Reel
                reel = Reel.objects.get(id=instance.content_id)
                content_owner = reel.user
            except Reel.DoesNotExist:
                pass
        elif instance.content_type == 'post':
            # Similar for posts when implemented
            pass
        
        # Send notification to content owner
        if content_owner and content_owner != instance.user:
            send_share_notification.delay(
                user_id=instance.user.id,
                content_type=instance.content_type,
                content_id=instance.content_id,
                content_owner_id=content_owner.id
            )
            
            # Create notification
            Notification.objects.create(
                recipient=content_owner,
                sender=instance.user,
                notification_type='share',
                content_type=instance.content_type,
                content_id=instance.content_id,
                message=f"{instance.user.username} shared your {instance.content_type}"
            )
        
        # Create activity record
        UserActivity.objects.create(
            user=instance.user,
            activity_type='share',
            content_type=instance.content_type,
            content_id=instance.content_id
        )
        
        logger.info(f"User {instance.user.username} shared {instance.content_type} {instance.content_id}")


@receiver(post_save, sender=FollowRequest)
def handle_follow_request_created(sender, instance, created, **kwargs):
    """
    Handle follow request creation
    """
    if created and instance.status == 'pending':
        # Create notification
        Notification.objects.create(
            recipient=instance.target,
            sender=instance.requester,
            notification_type='follow_request',
            message=f"{instance.requester.username} wants to follow you"
        )
        
        logger.info(f"Follow request from {instance.requester.username} to {instance.target.username}")


@receiver(post_save, sender=FollowRequest)
def handle_follow_request_updated(sender, instance, **kwargs):
    """
    Handle follow request status updates
    """
    if instance.status in ['accepted', 'declined']:
        # Create notification for requester
        notification_type = 'follow_request_accepted' if instance.status == 'accepted' else 'follow_request_declined'
        message = f"{instance.target.username} {'accepted' if instance.status == 'accepted' else 'declined'} your follow request"
        
        Notification.objects.create(
            recipient=instance.requester,
            sender=instance.target,
            notification_type=notification_type,
            message=message
        )
        
        # Process follow request notification asynchronously
        from .tasks import process_follow_request_notification
        process_follow_request_notification.delay(str(instance.id), instance.status)
        
        logger.info(f"Follow request {instance.id} {instance.status} by {instance.target.username}")


@receiver(post_save, sender=UserActivity)
def handle_user_activity_created(sender, instance, created, **kwargs):
    """
    Handle user activity creation
    """
    if created:
        # Update user's last activity timestamp
        profile = instance.user.social_profile
        profile.last_activity = instance.created_at
        profile.save(update_fields=['last_activity'])
        
        logger.info(f"Activity recorded: {instance.user.username} {instance.activity_type}")


@receiver(post_save, sender=Notification)
def handle_notification_created(sender, instance, created, **kwargs):
    """
    Handle notification creation
    """
    if created:
        # Send real-time notification via WebSocket
        # This would be handled by the tasks system
        pass


# Comment system signals (when integrated)
# @receiver(post_save, sender=Comment)
# def handle_comment_created(sender, instance, created, **kwargs):
#     """
#     Handle comment creation
#     """
#     if created:
#         # Update content stats
#         update_content_stats.delay(instance.content_type, instance.content_id)
#         
#         # Send notification to content owner
#         content_owner = get_content_owner(instance.content_type, instance.content_id)
#         if content_owner and content_owner != instance.user:
#             send_comment_notification.delay(
#                 user_id=instance.user.id,
#                 content_type=instance.content_type,
#                 content_id=instance.content_id,
#                 content_owner_id=content_owner.id,
#                 comment_text=instance.text
#             )
#         
#         # Create activity record
#         UserActivity.objects.create(
#             user=instance.user,
#             activity_type='comment',
#             content_type=instance.content_type,
#             content_id=instance.content_id
#         )


# Content creation signals
# @receiver(post_save, sender=Reel)
# def handle_reel_created(sender, instance, created, **kwargs):
#     """
#     Handle reel creation
#     """
#     if created:
#         # Update user's content count
#         profile = instance.user.social_profile
#         profile.reels_count += 1
#         profile.last_post_at = instance.created_at
#         profile.save(update_fields=['reels_count', 'last_post_at'])
#         
#         # Create activity record
#         UserActivity.objects.create(
#             user=instance.user,
#             activity_type='reel',
#             content_type='reel',
#             content_id=instance.id
#         )


# @receiver(post_delete, sender=Reel)
# def handle_reel_deleted(sender, instance, **kwargs):
#     """
#     Handle reel deletion
#     """
#     # Update user's content count
#     profile = instance.user.social_profile
#     profile.reels_count = max(0, profile.reels_count - 1)
#     profile.save(update_fields=['reels_count'])
