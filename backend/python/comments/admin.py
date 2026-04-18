from django.contrib import admin
from .models import (
    Comment, CommentLike, CommentMention, CommentThread,
    CommentReport, CommentNotification
)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'content_type', 'content_id', 'text_preview', 
        'parent', 'likes_count', 'replies_count', 'moderation_status',
        'is_deleted', 'created_at'
    ]
    list_filter = [
        'content_type', 'moderation_status', 'is_deleted', 'is_flagged',
        'created_at', 'user'
    ]
    search_fields = [
        'text', 'user__username', 'user__email', 'content_id'
    ]
    readonly_fields = [
        'id', 'likes_count', 'replies_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'parent']
    
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'user', 'content_type', 'content_id', 'text', 'parent'
            )
        }),
        ('Engagement', {
            'fields': (
                'likes_count', 'replies_count'
            )
        }),
        ('Moderation', {
            'fields': (
                'moderation_status', 'is_deleted', 'is_flagged'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'edited_at'
            )
        })
    )
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'
    
    actions = ['approve_comments', 'reject_comments', 'soft_delete_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(moderation_status='approved')
        self.message_user(request, f"Approved {queryset.count()} comments")
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        queryset.update(moderation_status='rejected')
        self.message_user(request, f"Rejected {queryset.count()} comments")
    reject_comments.short_description = "Reject selected comments"
    
    def soft_delete_comments(self, request, queryset):
        queryset.update(is_deleted=True, text="[deleted]")
        self.message_user(request, f"Deleted {queryset.count()} comments")
    soft_delete_comments.short_description = "Soft delete selected comments"


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment__text', 'user__username']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['comment', 'user']


@admin.register(CommentMention)
class CommentMentionAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'mentioned_user', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['comment__text', 'mentioned_user__username']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['comment', 'mentioned_user']


@admin.register(CommentThread)
class CommentThreadAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'content_type', 'content_id', 'comments_count',
        'likes_count', 'participants_count', 'last_comment_at',
        'last_comment_by', 'created_at'
    ]
    list_filter = ['content_type', 'created_at', 'last_comment_at']
    search_fields = ['content_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['last_comment_by']
    
    fieldsets = (
        ('Content Info', {
            'fields': (
                'content_type', 'content_id'
            )
        }),
        ('Statistics', {
            'fields': (
                'comments_count', 'likes_count', 'participants_count'
            )
        }),
        ('Activity', {
            'fields': (
                'last_comment_at', 'last_comment_by'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'comment', 'reporter', 'reason', 'is_reviewed',
        'action_taken', 'reviewed_by', 'created_at'
    ]
    list_filter = [
        'reason', 'is_reviewed', 'action_taken', 'created_at'
    ]
    search_fields = [
        'comment__text', 'reporter__username', 'description'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['comment', 'reporter', 'reviewed_by']
    
    fieldsets = (
        ('Report Info', {
            'fields': (
                'comment', 'reporter', 'reason', 'description'
            )
        }),
        ('Review', {
            'fields': (
                'is_reviewed', 'action_taken', 'reviewed_by', 'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
            )
        })
    )
    
    actions = ['mark_as_reviewed', 'delete_comment_reports']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(is_reviewed=True)
        self.message_user(request, f"Marked {queryset.count()} reports as reviewed")
    mark_as_reviewed.short_description = "Mark as reviewed"
    
    def delete_comment_reports(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Deleted {count} reports")
    delete_comment_reports.short_description = "Delete reports"


@admin.register(CommentNotification)
class CommentNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'comment', 'notification_type',
        'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at'
    ]
    search_fields = [
        'recipient__username', 'comment__text'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['recipient', 'comment']
    
    actions = ['mark_as_read', 'delete_notifications']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"Marked {queryset.count()} notifications as read")
    mark_as_read.short_description = "Mark as read"
    
    def delete_notifications(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Deleted {count} notifications")
    delete_notifications.short_description = "Delete notifications"
