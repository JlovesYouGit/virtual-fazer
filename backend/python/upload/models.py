from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.utils import timezone
import uuid
import os


class UploadSession(models.Model):
    """
    Tracks upload sessions for direct-to-cloud uploads
    """
    STATUS_CHOICES = [
        ('initialized', 'Initialized'),
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    file_id = models.CharField(max_length=255, unique=True, db_index=True)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initialized')
    error_message = models.TextField(blank=True)
    
    # Cloud storage info
    file_key = models.CharField(max_length=500, blank=True)
    upload_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'upload_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['file_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.original_name}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 24 hours from creation
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_active(self):
        return self.status in ['initialized', 'uploading'] and not self.is_expired


class UploadedFile(models.Model):
    """
    Stores information about uploaded files
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # File information
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    
    # Media properties
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # For videos
    
    # Storage information
    file_path = models.CharField(max_length=500, blank=True)
    file_url = models.URLField(blank=True)
    thumbnail_path = models.CharField(max_length=500, blank=True)
    thumbnail_url = models.URLField(blank=True)
    
    # Processing status
    upload_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_progress = models.IntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True)
    
    # Processing options
    is_processed = models.BooleanField(default=False)
    compress_applied = models.BooleanField(default=False)
    filters_applied = models.JSONField(default=list, blank=True)
    
    # Security and moderation
    is_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=True)  # Auto-approve, can be moderated
    
    # Analytics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'uploaded_files'
        indexes = [
            models.Index(fields=['user', 'upload_status']),
            models.Index(fields=['file_id']),
            models.Index(fields=['file_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['upload_status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.original_name}"
    
    @property
    def file_extension(self):
        return os.path.splitext(self.original_name)[1].lower()
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_image(self):
        return self.file_type == 'image'
    
    @property
    def is_video(self):
        return self.file_type == 'video'
    
    @property
    def aspect_ratio(self):
        if self.width and self.height:
            return self.width / self.height
        return None
    
    @property
    def is_landscape(self):
        if self.width and self.height:
            return self.width > self.height
        return None
    
    @property
    def is_portrait(self):
        if self.width and self.height:
            return self.height > self.width
        return None
    
    def get_absolute_url(self):
        if self.file_url:
            return self.file_url
        return f"/api/upload/file/{self.file_id}/"
    
    def get_thumbnail_url(self):
        if self.thumbnail_url:
            return self.thumbnail_url
        if self.is_image:
            return self.get_absolute_url()
        return None
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])


class FileProcessingTask(models.Model):
    """
    Tracks background processing tasks for uploaded files
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('thumbnail', 'Thumbnail Generation'),
        ('compression', 'Compression'),
        ('filter', 'Filter Application'),
        ('analysis', 'Content Analysis'),
        ('moderation', 'Content Moderation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='processing_tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # 0-100
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Task parameters and results
    parameters = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Task ID for background processing system
    celery_task_id = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'file_processing_tasks'
        indexes = [
            models.Index(fields=['uploaded_file', 'task_type']),
            models.Index(fields=['status']),
            models.Index(fields=['celery_task_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.uploaded_file.original_name} - {self.get_task_type_display()}"
    
    def mark_started(self):
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, result_data=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress = 100
        if result_data:
            self.result = result_data
        self.save(update_fields=['status', 'completed_at', 'progress', 'result'])
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    def update_progress(self, progress):
        self.progress = max(0, min(100, progress))
        self.save(update_fields=['progress'])


class UserUploadQuota(models.Model):
    """
    Manages upload quotas and limits for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='upload_quota')
    
    # Storage quotas
    max_files_per_day = models.PositiveIntegerField(default=50)
    max_storage_mb = models.PositiveIntegerField(default=1000)  # 1GB
    max_file_size_mb = models.PositiveIntegerField(default=100)
    
    # Current usage
    files_today = models.PositiveIntegerField(default=0)
    storage_used_mb = models.PositiveIntegerField(default=0)
    
    # Reset counters
    last_reset_date = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_upload_quota'
    
    def __str__(self):
        return f"{self.user.username} - {self.storage_used_mb}/{self.max_storage_mb}MB"
    
    def reset_daily_counters(self):
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.files_today = 0
            self.last_reset_date = today
            self.save(update_fields=['files_today', 'last_reset_date'])
    
    def can_upload_file(self, file_size_mb):
        self.reset_daily_counters()
        
        # Check daily file limit
        if self.files_today >= self.max_files_per_day:
            return False, "Daily file upload limit exceeded"
        
        # Check storage quota
        if self.storage_used_mb + file_size_mb > self.max_storage_mb:
            return False, "Storage quota exceeded"
        
        # Check individual file size
        if file_size_mb > self.max_file_size_mb:
            return False, f"File size exceeds maximum limit of {self.max_file_size_mb}MB"
        
        return True, "Upload allowed"
    
    def update_usage(self, file_size_mb):
        self.reset_daily_counters()
        self.files_today += 1
        self.storage_used_mb += file_size_mb
        self.save(update_fields=['files_today', 'storage_used_mb'])
    
    def free_storage(self, file_size_mb):
        self.storage_used_mb = max(0, self.storage_used_mb - file_size_mb)
        self.save(update_fields=['storage_used_mb'])


class ContentModerationLog(models.Model):
    """
    Logs content moderation actions
    """
    ACTION_CHOICES = [
        ('auto_approve', 'Auto Approve'),
        ('manual_approve', 'Manual Approve'),
        ('reject', 'Reject'),
        ('flag', 'Flag for Review'),
        ('delete', 'Delete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='moderation_logs')
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    
    # Who performed the action
    moderator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='moderation_actions'
    )
    
    # AI analysis results
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_flags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'content_moderation_logs'
        indexes = [
            models.Index(fields=['uploaded_file', 'action']),
            models.Index(fields=['moderator']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.uploaded_file.original_name} - {self.get_action_display()}"
