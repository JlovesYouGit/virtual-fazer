from django.contrib import admin
from .models import (
    UserProfile, Follow, Like, Share, FollowRequest, 
    UserActivity, Notification
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'followers_count', 'following_count', 'posts_count',
        'reels_count', 'is_private', 'show_activity_status',
        'total_likes_received', 'last_activity', 'created_at'
    ]
    list_filter = [
        'is_private', 'show_activity_status', 'allow_follow_requests',
        'created_at', 'last_activity'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'user', 'created_at', 'updated_at', 'total_likes_received',
        'total_comments_received', 'total_shares_received'
    ]
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Social Stats', {
            'fields': (
                'followers_count', 'following_count', 'posts_count',
                'reels_count'
            )
        }),
        ('Engagement Stats', {
            'fields': (
                'total_likes_received', 'total_comments_received',
                'total_shares_received'
            )
        }),
        ('Settings', {
            'fields': (
                'is_private', 'show_activity_status', 'allow_follow_requests'
            )
        }),
        ('Activity', {
            'fields': (
                'last_activity', 'last_post_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )
    
    actions = ['reset_stats', 'make_public', 'make_private']
    
    def reset_stats(self, request, queryset):
        for profile in queryset:
            profile.followers_count = 0
            profile.following_count = 0
            profile.posts_count = 0
            profile.reels_count = 0
            profile.save()
        self.message_user(request, f"Reset stats for {queryset.count()} profiles")
    reset_stats.short_description = "Reset all stats to 0"
    
    def make_public(self, request, queryset):
        queryset.update(is_private=False)
        self.message_user(request, f"Made {queryset.count()} profiles public")
    make_public.short_description = "Make profiles public"
    
    def make_private(self, request, queryset):
        queryset.update(is_private=True)
        self.message_user(request, f"Made {queryset.count()} profiles private")
    make_private.short_description = "Make profiles private"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'follower', 'following', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'follower__username', 'follower__email',
        'following__username', 'following__email'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['follower', 'following']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('follower', 'following')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'content_type', 'content_id', 'created_at'
    ]
    list_filter = ['content_type', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'content_id'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'content_type', 'content_id', 'caption', 'created_at'
    ]
    list_filter = ['content_type', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'content_id', 'caption'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'requester', 'target', 'status', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = [
        'requester__username', 'requester__email',
        'target__username', 'target__email'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['requester', 'target']
    
    fieldsets = (
        ('Request Info', {
            'fields': (
                'requester', 'target', 'status'
            )
        }),
        ('Details', {
            'fields': (
                'message',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )
    
    actions = ['accept_requests', 'decline_requests']
    
    def accept_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='accepted')
        self.message_user(request, f"Accepted {updated} follow requests")
    accept_requests.short_description = "Accept selected requests"
    
    def decline_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='declined')
        self.message_user(request, f"Declined {updated} follow requests")
    decline_requests.short_description = "Decline selected requests"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'activity_type', 'content_type', 'content_id',
        'target_user', 'created_at'
    ]
    list_filter = [
        'activity_type', 'content_type', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email',
        'target_user__username', 'target_user__email',
        'content_id'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['user', 'target_user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'target_user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'sender', 'notification_type', 'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at'
    ]
    search_fields = [
        'recipient__username', 'recipient__email',
        'sender__username', 'sender__email',
        'message'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['recipient', 'sender']
    
    fieldsets = (
        ('Notification Info', {
            'fields': (
                'recipient', 'sender', 'notification_type'
            )
        }),
        ('Content', {
            'fields': (
                'content_type', 'content_id', 'message'
            )
        }),
        ('Status', {
            'fields': (
                'is_read',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
            )
        })
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f"Marked {updated} notifications as read")
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(is_read=False)
        self.message_user(request, f"Marked {updated} notifications as unread")
    mark_as_unread.short_description = "Mark as unread"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender')
