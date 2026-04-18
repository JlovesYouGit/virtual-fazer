from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from io import BytesIO
import os
import tempfile
import shutil

from .models import UploadedFile, FileProcessingTask
from .utils import (
    get_file_metadata,
    generate_thumbnail,
    compress_image,
    compress_video,
    apply_image_filter,
    scan_file_for_malware,
    detect_inappropriate_content,
    cleanup_expired_uploads
)


@shared_task(bind=True, max_retries=3)
def process_uploaded_file(self, file_id):
    """
    Process uploaded file: extract metadata, generate thumbnails, scan for malware
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        # Create processing task record
        task = FileProcessingTask.objects.create(
            uploaded_file=uploaded_file,
            task_type='analysis',
            celery_task_id=self.request.id
        )
        
        task.mark_started()
        
        # Get file from storage
        if not uploaded_file.file_path:
            raise Exception("File path not set")
        
        # Download file to temporary location
        with tempfile.NamedTemporaryFile() as temp_file:
            # Copy file from storage to temp location
            with default_storage.open(uploaded_file.file_path, 'rb') as storage_file:
                shutil.copyfileobj(storage_file, temp_file)
            
            temp_file.flush()
            
            # Extract metadata
            task.update_progress(10)
            metadata = get_file_metadata(temp_file.name)
            
            # Update file metadata
            uploaded_file.width = metadata.get('width')
            uploaded_file.height = metadata.get('height')
            uploaded_file.duration = metadata.get('duration')
            uploaded_file.mime_type = metadata.get('mime_type', uploaded_file.mime_type)
            uploaded_file.save()
            
            # Generate thumbnail
            task.update_progress(30)
            thumbnail_path = f"thumbnails/{uploaded_file.user.id}/{uploaded_file.file_id}_thumb.jpg"
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as thumb_file:
                if generate_thumbnail(temp_file.name, thumb_file.name):
                    # Upload thumbnail to storage
                    with open(thumb_file.name, 'rb') as thumb_data:
                        default_storage.save(thumbnail_path, ContentFile(thumb_data.read()))
                    
                    uploaded_file.thumbnail_path = thumbnail_path
                    uploaded_file.thumbnail_url = default_storage.url(thumbnail_path)
                    uploaded_file.save()
                
                os.unlink(thumb_file.name)
            
            # Scan for malware
            task.update_progress(60)
            scan_result, scan_details = scan_file_for_malware(temp_file.name)
            uploaded_file.is_scanned = True
            uploaded_file.scan_result = scan_result
            
            if scan_result == 'infected':
                uploaded_file.upload_status = 'failed'
                uploaded_file.error_message = f"Malware detected: {scan_details}"
                uploaded_file.save()
                task.mark_failed(f"Malware detected: {scan_details}")
                return
            
            # Detect inappropriate content
            task.update_progress(80)
            content_analysis = detect_inappropriate_content(temp_file.name)
            
            if not content_analysis['is_appropriate']:
                uploaded_file.is_approved = False
                uploaded_file.upload_status = 'failed'
                uploaded_file.error_message = "Inappropriate content detected"
                uploaded_file.save()
                task.mark_failed("Inappropriate content detected")
                return
            
            # Mark as completed
            task.update_progress(100)
            uploaded_file.upload_status = 'completed'
            uploaded_file.is_approved = True
            uploaded_file.processed_at = timezone.now()
            uploaded_file.save()
            
            task.mark_completed({
                'metadata': metadata,
                'scan_result': scan_result,
                'content_analysis': content_analysis
            })
            
            return {
                'file_id': uploaded_file.file_id,
                'status': 'completed',
                'metadata': metadata
            }
            
    except UploadedFile.DoesNotExist:
        raise Exception(f"Uploaded file with ID {file_id} not found")
    except Exception as e:
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Mark as failed
        try:
            uploaded_file = UploadedFile.objects.get(id=file_id)
            uploaded_file.upload_status = 'failed'
            uploaded_file.error_message = str(e)
            uploaded_file.save()
        except UploadedFile.DoesNotExist:
            pass
        
        raise Exception(f"Failed to process uploaded file: {str(e)}")


@shared_task(bind=True, max_retries=2)
def process_file_with_options(self, file_id, compress=False, quality=0.8, filters=None, format_type=None):
    """
    Process file with specific options (compression, filters, etc.)
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        if uploaded_file.upload_status != 'completed':
            raise Exception("File must be completed before additional processing")
        
        # Create processing task
        task = FileProcessingTask.objects.create(
            uploaded_file=uploaded_file,
            task_type='filter',
            parameters={
                'compress': compress,
                'quality': quality,
                'filters': filters or [],
                'format_type': format_type
            },
            celery_task_id=self.request.id
        )
        
        task.mark_started()
        
        # Get original file
        with tempfile.NamedTemporaryFile() as temp_file:
            # Download original file
            with default_storage.open(uploaded_file.file_path, 'rb') as storage_file:
                shutil.copyfileobj(storage_file, temp_file)
            
            temp_file.flush()
            
            # Apply filters
            if filters:
                task.update_progress(20)
                for filter_name in filters:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as filter_file:
                        if apply_image_filter(temp_file.name, filter_file.name, filter_name):
                            # Replace temp file with filtered version
                            shutil.copyfile(filter_file.name, temp_file.name)
                        os.unlink(filter_file.name)
            
            # Apply compression
            if compress and uploaded_file.is_image:
                task.update_progress(60)
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as compressed_file:
                    if compress_image(temp_file.name, compressed_file.name, quality=int(quality * 100)):
                        # Replace temp file with compressed version
                        shutil.copyfile(compressed_file.name, temp_file.name)
                    os.unlink(compressed_file.name)
            
            # Upload processed file
            task.update_progress(80)
            processed_path = f"processed/{uploaded_file.user.id}/{uploaded_file.file_id}_processed.jpg"
            
            with open(temp_file.name, 'rb') as processed_data:
                default_storage.save(processed_path, ContentFile(processed_data.read()))
            
            # Update file record
            uploaded_file.file_path = processed_path
            uploaded_file.file_url = default_storage.url(processed_path)
            uploaded_file.is_processed = True
            uploaded_file.compress_applied = compress
            uploaded_file.filters_applied = filters or []
            uploaded_file.save()
            
            task.update_progress(100)
            task.mark_completed({
                'processed_path': processed_path,
                'filters_applied': filters,
                'compress_applied': compress
            })
            
            return {
                'file_id': uploaded_file.file_id,
                'processed_path': processed_path,
                'status': 'completed'
            }
            
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        try:
            uploaded_file = UploadedFile.objects.get(id=file_id)
            uploaded_file.upload_status = 'failed'
            uploaded_file.error_message = str(e)
            uploaded_file.save()
        except UploadedFile.DoesNotExist:
            pass
        
        raise Exception(f"Failed to process file with options: {str(e)}")


@shared_task
def cleanup_old_uploads():
    """
    Clean up old and expired uploads
    """
    try:
        # Clean up expired upload sessions
        cleanup_expired_uploads()
        
        # Clean up files marked as deleted
        from .models import UploadedFile
        deleted_files = UploadedFile.objects.filter(upload_status='deleted')
        
        for file in deleted_files:
            try:
                if file.file_path:
                    default_storage.delete(file.file_path)
                if file.thumbnail_path:
                    default_storage.delete(file.thumbnail_path)
            except Exception as e:
                print(f"Error cleaning up deleted file {file.file_id}: {e}")
        
        # Delete old processing tasks
        from .models import FileProcessingTask
        old_tasks = FileProcessingTask.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(days=7),
            status__in=['completed', 'failed']
        )
        old_tasks.delete()
        
        return {
            'cleaned_sessions': UploadSession.objects.filter(status='expired').count(),
            'cleaned_files': deleted_files.count(),
            'cleaned_tasks': old_tasks.count()
        }
        
    except Exception as e:
        print(f"Error in cleanup task: {e}")
        return {'error': str(e)}


@shared_task
def update_user_storage_stats():
    """
    Update storage usage statistics for all users
    """
    try:
        from django.contrib.auth.models import User
        from .models import UserUploadQuota
        
        users = User.objects.all()
        
        for user in users:
            # Get storage usage
            from .utils import get_storage_usage
            usage = get_storage_usage(user.id)
            
            # Update quota
            quota, created = UserUploadQuota.objects.get_or_create(user=user)
            quota.storage_used_mb = usage['total_size_mb']
            quota.save()
        
        return {
            'updated_users': users.count()
        }
        
    except Exception as e:
        print(f"Error updating storage stats: {e}")
        return {'error': str(e)}


@shared_task
def moderate_pending_content():
    """
    Moderate content that is pending approval
    """
    try:
        from .models import UploadedFile, ContentModerationLog
        
        pending_files = UploadedFile.objects.filter(
            upload_status='completed',
            is_approved=False,
            is_scanned=True
        )
        
        moderated_count = 0
        
        for file in pending_files:
            # Auto-approve if no issues found
            if file.scan_result == 'clean':
                file.is_approved = True
                file.save()
                
                # Log moderation action
                ContentModerationLog.objects.create(
                    uploaded_file=file,
                    action='auto_approve',
                    reason='Clean scan result',
                    ai_confidence=1.0
                )
                
                moderated_count += 1
        
        return {
            'moderated_count': moderated_count,
            'pending_count': pending_files.count()
        }
        
    except Exception as e:
        print(f"Error in moderation task: {e}")
        return {'error': str(e)}


# Schedule periodic tasks
from celery.schedules import crontab

# Schedule cleanup tasks
cleanup_old_uploads.schedule = crontab(hour=2, minute=0)  # Daily at 2 AM
update_user_storage_stats.schedule = crontab(hour=1, minute=0)  # Daily at 1 AM
moderate_pending_content.schedule = crontab(minute='*/30')  # Every 30 minutes
