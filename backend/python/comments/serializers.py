from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import (
    Comment, CommentLike, CommentMention, CommentThread,
    CommentReport, CommentNotification
)


class UserSerializer(serializers.ModelSerializer):
    """Minimal user serializer for comments"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments with full details"""
    
    user = UserSerializer(read_only=True)
    parent_user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content_type', 'content_id', 'text', 'user', 'parent',
            'parent_user', 'replies', 'likes_count', 'replies_count',
            'is_liked_by_user', 'mentions', 'is_edited', 'edited_at',
            'created_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'user', 'likes_count', 'replies_count', 'is_edited',
            'edited_at', 'created_at'
        ]
    
    def get_parent_user(self, obj):
        if obj.parent:
            return UserSerializer(obj.parent.user).data
        return None
    
    def get_replies(self, obj):
        if obj.replies.exists():
            # Get only recent replies to avoid infinite recursion
            recent_replies = obj.replies.filter(
                is_deleted=False,
                moderation_status='approved'
            ).order_by('created_at')[:3]
            return CommentSerializer(
                recent_replies, 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(
                comment=obj, 
                user=request.user
            ).exists()
        return False
    
    def get_mentions(self, obj):
        mentions = obj.mentions.all()
        return UserSerializer(
            [mention.mentioned_user for mention in mentions],
            many=True
        ).data
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        import math
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = math.floor(diff.seconds / 3600)
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = math.floor(diff.seconds / 60)
            return f"{minutes}m ago"
        else:
            return "just now"


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    
    class Meta:
        model = Comment
        fields = ['text', 'parent', 'content_type', 'content_id', 'user']
    
    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment text cannot be empty")
        return value.strip()
    
    def validate_parent(self, value):
        if value:
            # Check if parent comment exists and is not deleted
            if value.is_deleted:
                raise serializers.ValidationError("Cannot reply to deleted comment")
            if value.moderation_status != 'approved':
                raise serializers.ValidationError("Cannot reply to unapproved comment")
        return value
    
    def create(self, validated_data):
        # Remove user from validated_data as it's set in the view
        user = validated_data.pop('user')
        comment = Comment.objects.create(user=user, **validated_data)
        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating comments"""
    
    class Meta:
        model = Comment
        fields = ['text']
    
    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment text cannot be empty")
        return value.strip()


class CommentLikeSerializer(serializers.ModelSerializer):
    """Serializer for comment likes"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentThreadSerializer(serializers.ModelSerializer):
    """Serializer for comment threads"""
    
    last_comment_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CommentThread
        fields = [
            'id', 'content_type', 'content_id', 'comments_count',
            'likes_count', 'participants_count', 'last_comment_at',
            'last_comment_by', 'created_at', 'updated_at'
        ]


class CommentMentionSerializer(serializers.ModelSerializer):
    """Serializer for comment mentions"""
    
    mentioned_user = UserSerializer(read_only=True)
    
    class Meta:
        model = CommentMention
        fields = ['id', 'mentioned_user', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentReportSerializer(serializers.ModelSerializer):
    """Serializer for comment reports"""
    
    reporter = UserSerializer(read_only=True)
    comment = CommentSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CommentReport
        fields = [
            'id', 'comment', 'reporter', 'reason', 'description',
            'is_reviewed', 'action_taken', 'reviewed_by', 'reviewed_at',
            'created_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'is_reviewed', 'reviewed_by', 'reviewed_at', 'created_at'
        ]


class CommentNotificationSerializer(serializers.ModelSerializer):
    """Serializer for comment notifications"""
    
    comment = CommentSerializer(read_only=True)
    
    class Meta:
        model = CommentNotification
        fields = [
            'id', 'comment', 'notification_type', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'comment', 'notification_type', 'created_at']


class CommentStatsSerializer(serializers.Serializer):
    """Serializer for comment statistics"""
    
    total_comments = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    active_threads = serializers.IntegerField()
    recent_activity = serializers.IntegerField()


class CommentModerationSerializer(serializers.ModelSerializer):
    """Serializer for comment moderation"""
    
    user = UserSerializer(read_only=True)
    reports_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content_type', 'content_id', 'text', 'user',
            'likes_count', 'replies_count', 'moderation_status',
            'is_flagged', 'reports_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'likes_count', 'replies_count', 'created_at'
        ]
    
    def get_reports_count(self, obj):
        return obj.reports.count()


class BulkCommentActionSerializer(serializers.Serializer):
    """Serializer for bulk comment actions"""
    
    comment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ])
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CommentSearchSerializer(serializers.Serializer):
    """Serializer for comment search parameters"""
    
    query = serializers.CharField(min_length=1, max_length=100)
    content_type = serializers.ChoiceField(choices=[
        ('reel', 'Reel'),
        ('post', 'Post'),
        ('all', 'All')
    ], default='all')
    user_id = serializers.UUIDField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    sort_by = serializers.ChoiceField(choices=[
        ('newest', 'Newest'),
        ('oldest', 'Oldest'),
        ('popular', 'Popular')
    ], default='newest')


class CommentExportSerializer(serializers.Serializer):
    """Serializer for comment export parameters"""
    
    content_type = serializers.ChoiceField(choices=[
        ('reel', 'Reel'),
        ('post', 'Post')
    ])
    content_id = serializers.UUIDField()
    format = serializers.ChoiceField(choices=[
        ('json', 'JSON'),
        ('csv', 'CSV')
    ], default='json')
    include_deleted = serializers.BooleanField(default=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
