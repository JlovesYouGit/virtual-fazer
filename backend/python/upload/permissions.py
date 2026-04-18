from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import UserUploadQuota


class CanUploadContent(BasePermission):
    """
    Permission class to check if user can upload content
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get or create user quota
        quota, created = UserUploadQuota.objects.get_or_create(user=request.user)
        
        # Check if user is suspended or banned
        if hasattr(request.user, 'profile'):
            if request.user.profile.is_suspended:
                return False
            if request.user.profile.is_banned:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # For file-specific operations, check if user owns the file
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return True


class CanDeleteFile(BasePermission):
    """
    Permission class to check if user can delete files
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # User can only delete their own files
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For upload sessions
        if hasattr(obj, 'uploaded_file'):
            return obj.uploaded_file.user == request.user
        
        return False


class CanModerateContent(BasePermission):
    """
    Permission class for content moderation
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is moderator or admin
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check custom moderator role
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['moderator', 'admin']
        
        return False


class HasUploadQuota(BasePermission):
    """
    Permission class to check if user has remaining upload quota
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get user quota
        quota, created = UserUploadQuota.objects.get_or_create(user=request.user)
        
        # Reset daily counters if needed
        quota.reset_daily_counters()
        
        # Check if user has exceeded daily limits
        if quota.files_today >= quota.max_files_per_day:
            return False
        
        # Check if user has exceeded storage quota
        if quota.storage_used_mb >= quota.max_storage_mb:
            return False
        
        return True


class IsFileOwner(BasePermission):
    """
    Permission class to check if user owns the file
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsContentApproved(BasePermission):
    """
    Permission class to check if content is approved for public viewing
    """
    
    def has_object_permission(self, request, view, obj):
        # Owner can always view their own content
        if obj.user == request.user:
            return True
        
        # Staff and moderators can view all content
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if content is approved
        if hasattr(obj, 'is_approved'):
            return obj.is_approved
        
        return True


class CanViewAnalytics(BasePermission):
    """
    Permission class to check if user can view analytics
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Users can view their own analytics
        return True
    
    def has_object_permission(self, request, view, obj):
        # Users can only view their own analytics
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return True
