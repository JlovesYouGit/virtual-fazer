from django.contrib import admin
from .models import UploadedFile, UploadSession, UserUploadQuota, ContentModerationLog, FileProcessingTask


@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    list_display = ['file_id', 'user', 'original_name', 'file_type', 'file_size', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['file_id', 'original_name', 'user__username']
    readonly_fields = ['file_id', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status not in ['initialized', 'uploading']:
            readonly.extend(['file_type', 'file_size', 'file_key'])
        return readonly


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file_id', 'user', 'original_name', 'file_type', 'file_size_mb', 'upload_status', 'is_approved', 'created_at']
    list_filter = ['upload_status', 'file_type', 'is_approved', 'is_scanned', 'created_at']
    search_fields = ['file_id', 'original_name', 'user__username']
    readonly_fields = ['file_id', 'created_at', 'updated_at', 'processed_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'file_id', 'original_name', 'file_type', 'file_size', 'mime_type')
        }),
        ('Media Properties', {
            'fields': ('width', 'height', 'duration')
        }),
        ('Storage', {
            'fields': ('file_path', 'file_url', 'thumbnail_path', 'thumbnail_url')
        }),
        ('Processing', {
            'fields': ('upload_status', 'processing_progress', 'is_processed', 'compress_applied', 'filters_applied')
        }),
        ('Security', {
            'fields': ('is_scanned', 'scan_result', 'is_approved')
        }),
        ('Analytics', {
            'fields': ('download_count', 'view_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        })
    )
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'File Size'
    
    actions = ['approve_files', 'reject_files']
    
    def approve_files(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"Approved {queryset.count()} files")
    approve_files.short_description = "Approve selected files"
    
    def reject_files(self, request, queryset):
        queryset.update(is_approved=False, upload_status='failed')
        self.message_user(request, f"Rejected {queryset.count()} files")
    reject_files.short_description = "Reject selected files"


@admin.register(UserUploadQuota)
class UserUploadQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'files_today', 'storage_used_mb', 'max_storage_mb', 'storage_used_percentage', 'last_reset_date']
    list_filter = ['last_reset_date']
    search_fields = ['user__username']
    readonly_fields = ['last_reset_date']
    raw_id_fields = ['user']
    
    def storage_used_percentage(self, obj):
        if obj.max_storage_mb > 0:
            return f"{(obj.storage_used_mb / obj.max_storage_mb) * 100:.1f}%"
        return "0%"
    storage_used_percentage.short_description = 'Storage Used'
    
    actions = ['reset_daily_counters', 'increase_quota']
    
    def reset_daily_counters(self, request, queryset):
        for quota in queryset:
            quota.files_today = 0
            quota.save()
        self.message_user(request, f"Reset daily counters for {queryset.count()} users")
    reset_daily_counters.short_description = "Reset daily counters"
    
    def increase_quota(self, request, queryset):
        for quota in queryset:
            quota.max_storage_mb += 1000  # Add 1GB
            quota.save()
        self.message_user(request, f"Increased quota by 1GB for {queryset.count()} users")
    increase_quota.short_description = "Increase quota by 1GB"


@admin.register(ContentModerationLog)
class ContentModerationLogAdmin(admin.ModelAdmin):
    list_display = ['uploaded_file', 'action', 'moderator', 'ai_confidence', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['uploaded_file__original_name', 'uploaded_file__user__username', 'moderator__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['uploaded_file', 'moderator']
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # If editing existing object
            readonly.extend(['uploaded_file', 'action', 'reason', 'details', 'moderator'])
        return readonly


@admin.register(FileProcessingTask)
class FileProcessingTaskAdmin(admin.ModelAdmin):
    list_display = ['uploaded_file', 'task_type', 'status', 'progress', 'started_at', 'completed_at']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['uploaded_file__original_name', 'uploaded_file__user__username', 'celery_task_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'started_at', 'completed_at']
    raw_id_fields = ['uploaded_file']
    
    fieldsets = (
        ('Task Info', {
            'fields': ('uploaded_file', 'task_type', 'status', 'progress')
        }),
        ('Processing', {
            'fields': ('celery_task_id', 'started_at', 'completed_at')
        }),
        ('Data', {
            'fields': ('parameters', 'result', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
