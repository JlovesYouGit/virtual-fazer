from rest_framework import serializers
from .models import (
    Story, StoryView, StoryLike, StoryReply, StoryShare,
    StoryHighlight, StoryMention, StoryAnalytics
)
from users.serializers import UserSerializer


class StorySerializer(serializers.ModelSerializer):
    """
    Serializer for Story model
    """
    user = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    hashtags_list = serializers.SerializerMethodField()
    mentions_list = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    hours_remaining = serializers.SerializerMethodField()
    is_expired_now = serializers.SerializerMethodField()
    viewer_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'content_type', 'media_file', 'media_url',
            'text_content', 'background_color', 'text_color', 'caption',
            'hashtags', 'mentions', 'hashtags_list', 'mentions_list',
            'expires_at', 'is_expired', 'view_count', 'viewer_count',
            'likes_count', 'shares_count', 'replies_count',
            'is_active', 'is_archived', 'is_reported',
            'time_remaining', 'hours_remaining', 'is_expired_now',
            'is_liked', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'view_count', 'likes_count', 'shares_count',
            'replies_count', 'expires_at', 'is_expired', 'created_at', 'updated_at'
        ]
    
    def get_media_url(self, obj):
        """Get media file URL"""
        if obj.media_file:
            return obj.media_file.url
        return None
    
    def get_hashtags_list(self, obj):
        """Get hashtags as list"""
        return obj.get_hashtags_list()
    
    def get_mentions_list(self, obj):
        """Get mentions as list"""
        return obj.get_mentions_list()
    
    def get_time_remaining(self, obj):
        """Get remaining time before expiration"""
        remaining = obj.time_remaining
        return {
            'days': remaining.days,
            'hours': remaining.seconds // 3600,
            'minutes': (remaining.seconds % 3600) // 60,
            'seconds': remaining.seconds % 60
        }
    
    def get_hours_remaining(self, obj):
        """Get hours remaining before expiration"""
        return round(obj.hours_remaining, 2)
    
    def get_is_expired_now(self, obj):
        """Check if story is currently expired"""
        return obj.is_expired_now
    
    def get_viewer_count(self, obj):
        """Get unique viewer count"""
        return obj.views.count()
    
    def get_is_liked(self, obj):
        """Check if current user has liked the story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryLike.objects.filter(story=obj, user=request.user).exists()
        return False


class CreateStorySerializer(serializers.Serializer):
    """
    Serializer for creating stories
    """
    content_type = serializers.ChoiceField(choices=Story.STORY_TYPE_CHOICES)
    media_file = serializers.FileField(required=False, allow_null=True)
    text_content = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    caption = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    hashtags = serializers.CharField(required=False, allow_blank=True, max_length=500)
    mentions = serializers.CharField(required=False, allow_blank=True, max_length=500)
    background_color = serializers.CharField(required=False, default='#000000', max_length=7)
    text_color = serializers.CharField(required=False, default='#FFFFFF', max_length=7)
    
    def validate(self, attrs):
        content_type = attrs.get('content_type')
        media_file = attrs.get('media_file')
        text_content = attrs.get('text_content')
        
        # Validate content type and required fields
        if content_type in ['image', 'video'] and not media_file:
            raise serializers.ValidationError("Media file is required for image/video stories")
        
        if content_type == 'text' and not text_content:
            raise serializers.ValidationError("Text content is required for text stories")
        
        if content_type not in ['image', 'video'] and media_file:
            raise serializers.ValidationError("Media file is only allowed for image/video stories")
        
        return attrs


class StoryViewSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryView model
    """
    viewer = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryView
        fields = [
            'id', 'viewer', 'viewed_at', 'view_duration', 'time_ago'
        ]
        read_only_fields = ['id', 'viewer', 'viewed_at']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.viewed_at)


class StoryLikeSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryLike model
    """
    user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryLike
        fields = [
            'id', 'user', 'created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class StoryReplySerializer(serializers.ModelSerializer):
    """
    Serializer for StoryReply model
    """
    user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    thread_replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryReply
        fields = [
            'id', 'story', 'user', 'content', 'parent',
            'likes_count', 'replies_count', 'thread_replies',
            'is_deleted', 'is_reported', 'is_liked',
            'created_at', 'updated_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'story', 'user', 'likes_count', 'replies_count',
            'created_at', 'updated_at'
        ]
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)
    
    def get_replies_count(self, obj):
        """Get number of thread replies"""
        return obj.thread_replies.filter(is_deleted=False).count()
    
    def get_thread_replies(self, obj):
        """Get thread replies"""
        if obj.thread_replies.exists():
            replies = obj.thread_replies.filter(is_deleted=False).select_related('user')
            return StoryReplySerializer(replies, many=True, context=self.context).data
        return []
    
    def get_is_liked(self, obj):
        """Check if current user has liked the reply"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # This would need a StoryReplyLike model if we want to implement reply likes
            return False
        return False


class StoryReplyCreateSerializer(serializers.Serializer):
    """
    Serializer for creating story replies
    """
    content = serializers.CharField(max_length=1000)
    parent_id = serializers.UUIDField(required=False, allow_null=True)


class StoryShareSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryShare model
    """
    user = UserSerializer(read_only=True)
    shared_to_user = UserSerializer(source='shared_to', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryShare
        fields = [
            'id', 'user', 'share_type', 'shared_to', 'shared_to_user',
            'caption', 'created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class StoryShareCreateSerializer(serializers.Serializer):
    """
    Serializer for creating story shares
    """
    share_type = serializers.ChoiceField(choices=StoryShare.SHARE_TYPE_CHOICES)
    shared_to = serializers.UUIDField(required=False, allow_null=True)
    caption = serializers.CharField(required=False, allow_blank=True, max_length=500)


class StoryHighlightSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryHighlight model
    """
    user = UserSerializer(read_only=True)
    cover_story = StorySerializer(read_only=True)
    stories = StorySerializer(many=True, read_only=True)
    stories_count = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryHighlight
        fields = [
            'id', 'user', 'title', 'cover_story', 'stories',
            'stories_count', 'is_active', 'is_archived',
            'created_at', 'updated_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at'
        ]
    
    def get_stories_count(self, obj):
        """Get number of active stories in highlight"""
        return obj.stories_count
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class StoryMentionSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryMention model
    """
    mentioned_user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryMention
        fields = [
            'id', 'story', 'mentioned_user', 'position_x', 'position_y',
            'created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'story', 'mentioned_user', 'created_at']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class StoryAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryAnalytics model
    """
    date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryAnalytics
        fields = [
            'id', 'story', 'date', 'date_formatted',
            'views_count', 'unique_viewers', 'likes_count',
            'shares_count', 'replies_count', 'completion_rate',
            'engagement_rate', 'reach'
        ]
        read_only_fields = [
            'id', 'story', 'date'
        ]
    
    def get_date_formatted(self, obj):
        """Get formatted date"""
        return obj.date.strftime('%B %d, %Y')


class StoryBatchSerializer(serializers.Serializer):
    """
    Serializer for batch story operations
    """
    story_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=['delete', 'archive', 'unarchive'])


class StorySearchSerializer(serializers.Serializer):
    """
    Serializer for story search
    """
    query = serializers.CharField(min_length=1, max_length=100)
    content_type = serializers.ChoiceField(
        choices=Story.STORY_TYPE_CHOICES,
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    user_id = serializers.UUIDField(required=False)


class StoryTrendingSerializer(serializers.Serializer):
    """
    Serializer for trending stories
    """
    time_range = serializers.ChoiceField(
        choices=['hour', 'day', 'week', 'month'],
        default='day'
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)


class StoryStatsSerializer(serializers.Serializer):
    """
    Serializer for story statistics
    """
    date_range = serializers.ChoiceField(
        choices=['today', 'week', 'month', 'year', 'all'],
        default='week'
    )
