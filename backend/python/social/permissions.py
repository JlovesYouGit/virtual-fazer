from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User
from django.utils import timezone


class CanFollowUser(BasePermission):
    """
    Permission to check if user can follow another user
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
        # obj would be the target user
        target_user = obj
        
        # Cannot follow yourself
        if target_user == request.user:
            return False
        
        # Check if already following
        from .models import Follow
        if Follow.objects.filter(follower=request.user, following=target_user).exists():
            return False
        
        # Check target user's privacy settings
        if hasattr(target_user, 'social_profile'):
            profile = target_user.social_profile
            if profile.is_private and not profile.allow_follow_requests:
                return False
        
        return True


class CanViewPrivateProfile(BasePermission):
    """
    Permission to check if user can view private profile
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj would be the target user
        target_user = obj
        
        # Users can always view their own profile
        if target_user == request.user:
            return True
        
        # Check if target profile is private
        if hasattr(target_user, 'social_profile'):
            profile = target_user.social_profile
            if not profile.is_private:
                return True
            
            # Check if request user follows target user
            from .models import Follow
            if Follow.objects.filter(follower=request.user, following=target_user).exists():
                return True
        
        return False


class CanManageFollowRequest(BasePermission):
    """
    Permission to manage follow requests
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj would be the follow request
        # Only target user can manage follow requests
        return obj.target == request.user


class CanLikeContent(BasePermission):
    """
    Permission to like content
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


class CanShareContent(BasePermission):
    """
    Permission to share content
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


class IsOwnerOrStaff(BasePermission):
    """
    Permission to check if user is owner or staff
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user owns the object
        if hasattr(obj, 'user'):
            if obj.user == request.user:
                return True
        
        # Check if user is staff
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return False


class IsProfileOwner(BasePermission):
    """
    Permission to check if user owns the profile
    """
    
    def has_object_permission(self, request, view, obj):
        # obj would be the user profile or user
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class IsNotBlocked(BasePermission):
    """
    Permission to check if user is not blocked by target user
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj would be the target user
        target_user = obj
        
        # Check if target user has blocked request user
        # This would need to be implemented based on your block system
        # For now, return True
        return True


class HasValidProfile(BasePermission):
    """
    Permission to check if user has valid profile
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a profile
        if not hasattr(request.user, 'social_profile'):
            return False
        
        # Check if profile is complete enough
        profile = request.user.social_profile
        if not request.user.first_name or not request.user.last_name:
            return False
        
        return True


class CanViewSocialStats(BasePermission):
    """
    Permission to view social statistics
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj would be the target user
        target_user = obj
        
        # Users can always view their own stats
        if target_user == request.user:
            return True
        
        # Check if target profile is private
        if hasattr(target_user, 'social_profile'):
            profile = target_user.social_profile
            if profile.is_private:
                # Check if request user follows target user
                from .models import Follow
                if Follow.objects.filter(follower=request.user, following=target_user).exists():
                    return True
                return False
        
        return True


class CanManageNotifications(BasePermission):
    """
    Permission to manage notifications
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj would be the notification
        # Only recipient can manage their notifications
        return obj.recipient == request.user


class RateLimitFollows(BasePermission):
    """
    Permission to check follow rate limits
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check follow rate limit (e.g., max 50 follows per hour)
        from django.utils import timezone
        from .models import Follow
        
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_follows = Follow.objects.filter(
            follower=request.user,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_follows >= 50:
            return False
        
        return True


class RateLimitLikes(BasePermission):
    """
    Permission to check like rate limits
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check like rate limit (e.g., max 100 likes per hour)
        from django.utils import timezone
        from .models import Like
        
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_likes = Like.objects.filter(
            user=request.user,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_likes >= 100:
            return False
        
        return True


class CanViewAnalytics(BasePermission):
    """
    Permission to view analytics
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can view all analytics
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users can view their own analytics
        return True
    
    def has_object_permission(self, request, view, obj):
        # obj would be the target user
        # Users can only view their own analytics unless they're staff
        if obj == request.user:
            return True
        
        return request.user.is_staff or request.user.is_superuser
