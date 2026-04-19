from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class CanCommentContent(BasePermission):
    """
    Permission to check if user can comment on content
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is suspended or banned
        if hasattr(request.user, 'profile'):
            if request.user.profile.is_suspended:
                return False
            if request.user.profile.is_banned:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # For content-specific permissions
        return self.has_permission(request, view)


class CanEditComment(BasePermission):
    """
    Permission to check if user can edit comment
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # User can edit their own comments
        if obj.user == request.user:
            # Check time limit (e.g., 15 minutes)
            from django.utils import timezone
            time_limit = timezone.now() - timezone.timedelta(minutes=15)
            if obj.created_at >= time_limit:
                return True
        
        return False


class CanDeleteComment(BasePermission):
    """
    Permission to check if user can delete comment
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # User can delete their own comments
        if obj.user == request.user:
            return True
        
        # Moderators and admins can delete any comment
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check custom moderator role
        if hasattr(request.user, 'profile'):
            if request.user.profile.role in ['moderator', 'admin']:
                return True
        
        return False


class CanModerateComments(BasePermission):
    """
    Permission to check if user can moderate comments
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can moderate
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check custom moderator role
        if hasattr(request.user, 'profile'):
            if request.user.profile.role in ['moderator', 'admin']:
                return True
        
        return False


class CanViewComment(BasePermission):
    """
    Permission to check if user can view comment
    """
    
    def has_permission(self, request, view):
        # All authenticated users can view comments
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Additional checks for private content
        if hasattr(obj, 'content') and obj.content:
            content = obj.content
            if hasattr(content, 'is_private') and content.is_private:
                # Only owner and followers can view comments on private content
                if content.user == request.user:
                    return True
                
                if hasattr(content, 'followers') and request.user in content.followers.all():
                    return True
                
                return False
        
        return True


class CanLikeComment(BasePermission):
    """
    Permission to check if user can like comment
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is suspended or banned
        if hasattr(request.user, 'profile'):
            if request.user.profile.is_suspended:
                return False
            if request.user.profile.is_banned:
                return False
        
        return True


class CanReportComment(BasePermission):
    """
    Permission to check if user can report comment
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is suspended or banned
        if hasattr(request.user, 'profile'):
            if request.user.profile.is_suspended:
                return False
            if request.user.profile.is_banned:
                return False
        
        return True


class IsCommentOwner(BasePermission):
    """
    Permission to check if user owns the comment
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsNotDeleted(BasePermission):
    """
    Permission to check if comment is not deleted
    """
    
    def has_object_permission(self, request, view, obj):
        return not obj.is_deleted


class IsApproved(BasePermission):
    """
    Permission to check if comment is approved
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.moderation_status == 'approved'
