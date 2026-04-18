from rest_framework import serializers
from .models import UploadedFile, UploadSession, UserUploadQuota, ContentModerationLog, FileProcessingTask
from django.contrib.auth.models import User


class UploadSessionSerializer(serializers.ModelSerializer):
    """Serializer for upload sessions"""
    
    class Meta:
        model = UploadSession
        fields = [
            'id', 'file_id', 'original_name', 'file_type', 'file_size',
            'status', 'error_message', 'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = ['id', 'file_id', 'created_at', 'updated_at', 'expires_at']


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files"""
    
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    aspect_ratio = serializers.SerializerMethodField()
    is_landscape = serializers.SerializerMethodField()
    is_portrait = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = [
            'id', 'file_id', 'original_name', 'file_type', 'file_size', 'file_size_mb',
            'mime_type', 'width', 'height', 'duration', 'file_url', 'thumbnail_url',
            'upload_status', 'processing_progress', 'error_message', 'is_processed',
            'compress_applied', 'filters_applied', 'is_scanned', 'scan_result',
            'is_approved', 'download_count', 'view_count', 'created_at',
            'updated_at', 'processed_at', 'aspect_ratio', 'is_landscape', 'is_portrait'
        ]
        read_only_fields = [
            'id', 'file_id', 'file_url', 'thumbnail_url', 'upload_status',
            'processing_progress', 'is_processed', 'compress_applied',
            'filters_applied', 'is_scanned', 'scan_result', 'is_approved',
            'download_count', 'view_count', 'created_at', 'updated_at', 'processed_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file_url:
            return obj.file_url
        return f"/api/upload/file/{obj.file_id}/"
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail_url:
            return obj.thumbnail_url
        if obj.is_image:
            return self.get_file_url(obj)
        return None
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
    
    def get_aspect_ratio(self, obj):
        if obj.width and obj.height:
            return round(obj.width / obj.height, 2)
        return None
    
    def get_is_landscape(self, obj):
        if obj.width and obj.height:
            return obj.width > obj.height
        return None
    
    def get_is_portrait(self, obj):
        if obj.width and obj.height:
            return obj.height > obj.width
        return None


class UserUploadQuotaSerializer(serializers.ModelSerializer):
    """Serializer for user upload quotas"""
    
    storage_used_percentage = serializers.SerializerMethodField()
    daily_files_percentage = serializers.SerializerMethodField()
    remaining_storage_mb = serializers.SerializerMethodField()
    remaining_daily_files = serializers.SerializerMethodField()
    
    class Meta:
        model = UserUploadQuota
        fields = [
            'max_files_per_day', 'max_storage_mb', 'max_file_size_mb',
            'files_today', 'storage_used_mb', 'last_reset_date',
            'storage_used_percentage', 'daily_files_percentage',
            'remaining_storage_mb', 'remaining_daily_files'
        ]
        read_only_fields = ['files_today', 'storage_used_mb', 'last_reset_date']
    
    def get_storage_used_percentage(self, obj):
        if obj.max_storage_mb > 0:
            return round((obj.storage_used_mb / obj.max_storage_mb) * 100, 1)
        return 0
    
    def get_daily_files_percentage(self, obj):
        if obj.max_files_per_day > 0:
            return round((obj.files_today / obj.max_files_per_day) * 100, 1)
        return 0
    
    def get_remaining_storage_mb(self, obj):
        return max(0, obj.max_storage_mb - obj.storage_used_mb)
    
    def get_remaining_daily_files(self, obj):
        return max(0, obj.max_files_per_day - obj.files_today)


class ContentModerationLogSerializer(serializers.ModelSerializer):
    """Serializer for content moderation logs"""
    
    moderator_username = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentModerationLog
        fields = [
            'id', 'action', 'reason', 'details', 'moderator', 'moderator_username',
            'ai_confidence', 'ai_flags', 'created_at'
        ]
        read_only_fields = ['id', 'moderator', 'created_at']
    
    def get_moderator_username(self, obj):
        if obj.moderator:
            return obj.moderator.username
        return None


class FileProcessingTaskSerializer(serializers.ModelSerializer):
    """Serializer for file processing tasks"""
    
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FileProcessingTask
        fields = [
            'id', 'uploaded_file', 'task_type', 'task_type_display',
            'status', 'status_display', 'progress', 'started_at',
            'completed_at', 'parameters', 'result', 'error_message',
            'celery_task_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploaded_file', 'task_type_display', 'status_display',
            'started_at', 'completed_at', 'result', 'error_message',
            'celery_task_id', 'created_at', 'updated_at'
        ]


class UploadInitRequestSerializer(serializers.Serializer):
    """Serializer for upload initialization request"""
    
    file_type = serializers.ChoiceField(choices=['image', 'video'])
    file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=1)
    content_type = serializers.CharField(max_length=100, required=False)
    
    def validate_file_size(self, value):
        max_size = 100 * 1024 * 1024  # 100MB
        if value > max_size:
            raise serializers.ValidationError(f"File size exceeds maximum limit of {max_size // (1024*1024)}MB")
        return value
    
    def validate_file_name(self, value):
        # Check for valid file extensions
        allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'],
            'video': ['.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv', '.wmv']
        }
        
        file_ext = '.' + value.split('.')[-1].lower() if '.' in value else ''
        
        # Will be validated against file_type in the view
        return value


class UploadConfirmRequestSerializer(serializers.Serializer):
    """Serializer for upload confirmation request"""
    
    original_name = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=100)
    dimensions = serializers.DictField(required=False)
    duration = serializers.FloatField(required=False)
    
    def validate_dimensions(self, value):
        if value:
            if 'width' in value and not isinstance(value['width'], int):
                raise serializers.ValidationError("Width must be an integer")
            if 'height' in value and not isinstance(value['height'], int):
                raise serializers.ValidationError("Height must be an integer")
        return value


class FileProcessRequestSerializer(serializers.Serializer):
    """Serializer for file processing request"""
    
    compress = serializers.BooleanField(default=False)
    quality = serializers.FloatField(min_value=0.1, max_value=1.0, default=0.8)
    filters = serializers.ListField(child=serializers.CharField(), required=False)
    format_type = serializers.CharField(max_length=10, required=False)
    
    def validate_quality(self, value):
        if value < 0.1 or value > 1.0:
            raise serializers.ValidationError("Quality must be between 0.1 and 1.0")
        return value
    
    def validate_filters(self, value):
        allowed_filters = ['vintage', 'dramatic', 'warm', 'cool']
        for filter_name in value:
            if filter_name not in allowed_filters:
                raise serializers.ValidationError(f"Filter '{filter_name}' is not allowed")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for upload responses"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
