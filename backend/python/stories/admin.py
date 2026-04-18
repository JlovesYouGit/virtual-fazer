from django.contrib import admin
from .models import (
    Story, StoryView, StoryLike, StoryReply, StoryShare,
    StoryHighlight, StoryMention, StoryAnalytics
)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'content_type', 'caption', 'view_count',
        'likes_count', 'shares_count', 'replies_count',
        'is_active', 'is_expired', 'expires_at', 'created_at'
    ]
    list_filter = [
        'content_type', 'is_active', 'is_expired', 'is_archived',
        'is_reported', 'created_at', 'expires_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'caption', 'hashtags', 'mentions'
    ]
    readonly_fields = [
        'id', 'view_count', 'likes_count', 'shares_count', 
        'replies_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Story Info', {
            'fields': ('user', 'content_type', 'caption')
        }),
        ('Content', {
            'fields': (
                'media_file', 'text_content', 'background_color', 'text_color'
            )
        }),
        ('Metadata', {
            'fields': ('hashtags', 'mentions')
        }),
        ('Engagement', {
            'fields': (
                'view_count', 'likes_count', 'shares_count', 'replies_count'
            )
        }),
        ('Status', {
            'fields': (
                'is_active', 'is_expired', 'is_archived', 'is_reported'
            )
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    actions = ['mark_as_expired', 'mark_as_archived', 'reset_engagement']
    
    def mark_as_expired(self, request, queryset):
        updated = queryset.filter(is_expired=False).update(is_expired=True, is_active=False)
        self.message_user(request, f"Marked {updated} stories as expired")
    mark_as_expired.short_description = "Mark selected stories as expired"
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f"Archived {updated} stories")
    mark_as_archived.short_description = "Archive selected stories"
    
    def reset_engagement(self, request, queryset):
        updated = queryset.update(
            view_count=0, likes_count=0, shares_count=0, replies_count=0
        )
        self.message_user(request, f"Reset engagement for {updated} stories")
    reset_engagement.short_description = "Reset engagement metrics"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'viewer', 'viewed_at', 'view_duration'
    ]
    list_filter = [
        'viewed_at', 'view_duration'
    ]
    search_fields = [
        'story__user__username', 'viewer__username', 'viewer__email'
    ]
    readonly_fields = [
        'id', 'viewed_at'
    ]
    raw_id_fields = ['story', 'viewer']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story', 'viewer')


@admin.register(StoryLike)
class StoryLikeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'user', 'created_at'
    ]
    list_filter = [
        'created_at'
    ]
    search_fields = [
        'story__user__username', 'user__username', 'user__email'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    raw_id_fields = ['story', 'user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story', 'user')


@admin.register(StoryReply)
class StoryReplyAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'user', 'content_preview', 'likes_count',
        'is_deleted', 'is_reported', 'created_at'
    ]
    list_filter = [
        'is_deleted', 'is_reported', 'created_at'
    ]
    search_fields = [
        'story__user__username', 'user__username', 'content'
    ]
    readonly_fields = [
        'id', 'likes_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['story', 'user', 'parent']
    
    fieldsets = (
        ('Reply Info', {
            'fields': ('story', 'user', 'parent')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Engagement', {
            'fields': ('likes_count',)
        }),
        ('Status', {
            'fields': ('is_deleted', 'is_reported')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    actions = ['mark_as_deleted', 'mark_as_not_deleted']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def mark_as_deleted(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(is_deleted=True)
        self.message_user(request, f"Marked {updated} replies as deleted")
    mark_as_deleted.short_description = "Mark as deleted"
    
    def mark_as_not_deleted(self, request, queryset):
        updated = queryset.filter(is_deleted=True).update(is_deleted=False)
        self.message_user(request, f"Marked {updated} replies as not deleted")
    mark_as_not_deleted.short_description = "Mark as not deleted"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story', 'user', 'parent')


@admin.register(StoryShare)
class StoryShareAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'user', 'share_type', 'shared_to', 'created_at'
    ]
    list_filter = [
        'share_type', 'created_at'
    ]
    search_fields = [
        'story__user__username', 'user__username', 'shared_to__username'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    raw_id_fields = ['story', 'user', 'shared_to']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story', 'user', 'shared_to')


@admin.register(StoryHighlight)
class StoryHighlightAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'title', 'stories_count', 'is_active',
        'is_archived', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_archived', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'title'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'cover_story']
    filter_horizontal = ['stories']
    
    fieldsets = (
        ('Highlight Info', {
            'fields': ('user', 'title', 'cover_story')
        }),
        ('Stories', {
            'fields': ('stories',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_archived')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    actions = ['mark_as_active', 'mark_as_archived']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"Marked {updated} highlights as active")
    mark_as_active.short_description = "Mark as active"
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.filter(is_archived=False).update(is_archived=True)
        self.message_user(request, f"Archived {updated} highlights")
    mark_as_archived.short_description = "Archive highlights"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'cover_story')


@admin.register(StoryMention)
class StoryMentionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'mentioned_user', 'position_x', 'position_y', 'created_at'
    ]
    list_filter = [
        'created_at'
    ]
    search_fields = [
        'story__user__username', 'mentioned_user__username', 'mentioned_user__email'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    raw_id_fields = ['story', 'mentioned_user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story', 'mentioned_user')


@admin.register(StoryAnalytics)
class StoryAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'date', 'views_count', 'unique_viewers',
        'likes_count', 'shares_count', 'replies_count',
        'engagement_rate', 'reach'
    ]
    list_filter = [
        'date', 'engagement_rate'
    ]
    search_fields = [
        'story__user__username', 'story__caption'
    ]
    readonly_fields = [
        'id', 'date'
    ]
    raw_id_fields = ['story']
    
    fieldsets = (
        ('Analytics Info', {
            'fields': ('story', 'date')
        }),
        ('Views', {
            'fields': ('views_count', 'unique_viewers', 'reach')
        }),
        ('Engagement', {
            'fields': ('likes_count', 'shares_count', 'replies_count')
        }),
        ('Metrics', {
            'fields': ('completion_rate', 'engagement_rate')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story')
