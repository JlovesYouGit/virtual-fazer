from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import UploadedFile, UserUploadQuota, ContentModerationLog
from .tasks import process_uploaded_file, update_user_storage_stats
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_upload_quota(sender, instance, created, **kwargs):
    """
    Create upload quota when new user is created
    """
    if created:
        UserUploadQuota.objects.get_or_create(user=instance)
        logger.info(f"Created upload quota for user {instance.username}")


@receiver(post_save, sender=UploadedFile)
def handle_file_upload(sender, instance, created, **kwargs):
    """
    Handle file upload events
    """
    if created and instance.upload_status == 'pending':
        # Trigger processing for new uploads
        try:
            process_uploaded_file.delay(instance.id)
            logger.info(f"Started processing for file {instance.file_id}")
        except Exception as e:
            logger.error(f"Failed to start processing for file {instance.file_id}: {e}")
    
    # Update user storage stats when file status changes
    if not created and instance.upload_status in ['completed', 'deleted']:
        try:
            update_user_storage_stats.delay()
        except Exception as e:
            logger.error(f"Failed to update storage stats: {e}")


@receiver(post_delete, sender=UploadedFile)
def handle_file_deletion(sender, instance, **kwargs):
    """
    Handle file deletion events
    """
    try:
        # Update user quota
        quota = UserUploadQuota.objects.filter(user=instance.user).first()
        if quota:
            quota.free_storage(instance.file_size / (1024 * 1024))
            logger.info(f"Freed {instance.file_size / (1024 * 1024):.2f}MB for user {instance.user.username}")
        
        # Update storage stats
        update_user_storage_stats.delay()
        
    except Exception as e:
        logger.error(f"Failed to handle file deletion: {e}")


@receiver(post_save, sender=ContentModerationLog)
def handle_moderation_action(sender, instance, created, **kwargs):
    """
    Handle content moderation actions
    """
    if created:
        logger.info(f"Content moderation action: {instance.get_action_display()} for file {instance.uploaded_file.file_id}")
        
        # If content was rejected or deleted, update file status
        if instance.action in ['reject', 'delete']:
            try:
                instance.uploaded_file.is_approved = False
                instance.uploaded_file.upload_status = 'failed'
                instance.uploaded_file.error_message = f"Content {instance.action}: {instance.reason}"
                instance.uploaded_file.save()
            except Exception as e:
                logger.error(f"Failed to update file status after moderation: {e}")
