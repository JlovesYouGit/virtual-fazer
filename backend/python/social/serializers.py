from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import (
    UserProfile, Follow, Like, Share, FollowRequest, 
    UserActivity, Notification
)


class UserSerializer(serializers.ModelSerializer):
    """Minimal user serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles with social stats"""
    
    user = UserSerializer(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    reels_count = serializers.IntegerField(read_only=True)
    total_likes_received = serializers.IntegerField(read_only=True)
    total_comments_received = serializers.IntegerField(read_only=True)
    total_shares_received = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'followers_count', 'following_count', 'posts_count',
            'reels_count', 'is_private', 'show_activity_status',
            'allow_follow_requests', 'total_likes_received',
            'total_comments_received', 'total_shares_received',
            'last_activity', 'last_post_at', 'created_at'
        ]
        read_only_fields = [
            'user', 'followers_count', 'following_count', 'posts_count',
            'reels_count', 'total_likes_received', 'total_comments_received',
            'total_shares_received', 'last_activity', 'last_post_at',
            'created_at'
        ]


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for follow relationships"""
    
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    
    class Meta:
        model = Follow
        fields = [
            'id', 'follower', 'following', 'follower_username', 
            'following_username', 'created_at'
        ]
        read_only_fields = ['id', 'follower', 'following', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for likes"""
    
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'username', 'content_type', 'content_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ShareSerializer(serializers.ModelSerializer):
    """Serializer for shares"""
    
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Share
        fields = [
            'id', 'user', 'username', 'content_type', 'content_id', 
            'caption', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class FollowRequestSerializer(serializers.ModelSerializer):
    """Serializer for follow requests"""
    
    requester = UserSerializer(read_only=True)
    target = UserSerializer(read_only=True)
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    target_username = serializers.CharField(source='target.username', read_only=True)
    
    class Meta:
        model = FollowRequest
        fields = [
            'id', 'requester', 'target', 'requester_username', 
            'target_username', 'status', 'message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'requester', 'target', 'status', 'created_at', 'updated_at'
        ]


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities"""
    
    user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    target_username = serializers.CharField(source='target_user.username', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_username', 'activity_type', 'content_type',
            'content_id', 'target_user', 'target_username', 'metadata',
            'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'target_user', 'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    
    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'recipient_username', 
            'sender_username', 'notification_type', 'content_type',
            'content_id', 'message', 'is_read', 'created_at'
        ]
        read_only_fields = [
            'id', 'recipient', 'sender', 'created_at'
        ]


class FollowStatsSerializer(serializers.Serializer):
    """Serializer for follow statistics"""
    
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    mutual_followers = serializers.ListField(child=serializers.DictField())
    recent_followers = serializers.ListField(child=serializers.DictField())
    follow_growth = serializers.ListField(child=serializers.DictField())


class UserStatsSerializer(serializers.Serializer):
    """Serializer for comprehensive user statistics"""
    
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    posts_count = serializers.IntegerField()
    reels_count = serializers.IntegerField()
    total_likes_received = serializers.IntegerField()
    total_comments_received = serializers.IntegerField()
    total_shares_received = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    average_likes_per_post = serializers.FloatField()
    average_comments_per_post = serializers.FloatField()
    top_performing_content = serializers.ListField(child=serializers.DictField())
    follower_growth = serializers.ListField(child=serializers.DictField())
    activity_heatmap = serializers.ListField(child=serializers.DictField())


class ContentStatsSerializer(serializers.Serializer):
    """Serializer for content statistics"""
    
    likes_count = serializers.IntegerField()
    comments_count = serializers.IntegerField()
    shares_count = serializers.IntegerField()
    views_count = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    reach_estimate = serializers.IntegerField()
    top_demographics = serializers.ListField(child=serializers.DictField())
    performance_over_time = serializers.ListField(child=serializers.DictField())


class SocialFeedSerializer(serializers.Serializer):
    """Serializer for social feed items"""
    
    id = serializers.CharField()
    type = serializers.ChoiceField(choices=['post', 'reel', 'like', 'comment', 'follow'])
    user = UserSerializer()
    content = serializers.DictField()
    metadata = serializers.DictField()
    created_at = serializers.DateTimeField()
    interactions = serializers.DictField()


class TrendingUsersSerializer(serializers.Serializer):
    """Serializer for trending users"""
    
    user = UserSerializer()
    follower_growth = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    trending_score = serializers.FloatField()
    categories = serializers.ListField(child=serializers.CharField())


class SocialSearchSerializer(serializers.Serializer):
    """Serializer for social search results"""
    
    users = serializers.ListField(child=UserSerializer())
    posts = serializers.ListField(child=serializers.DictField())
    reels = serializers.ListField(child=serializers.DictField())
    hashtags = serializers.ListField(child=serializers.CharField())
    total_results = serializers.IntegerField()


class SocialAnalyticsSerializer(serializers.Serializer):
    """Serializer for social analytics"""
    
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year'])
    follower_growth = serializers.ListField(child=serializers.DictField())
    engagement_metrics = serializers.ListField(child=serializers.DictField())
    content_performance = serializers.ListField(child=serializers.DictField())
    audience_demographics = serializers.DictField()
    top_performing_content = serializers.ListField(child=serializers.DictField())
    competitor_analysis = serializers.DictField()


class RecommendationSerializer(serializers.Serializer):
    """Serializer for user recommendations"""
    
    users = serializers.ListField(child=UserSerializer())
    reason = serializers.CharField()
    confidence_score = serializers.FloatField()
    mutual_connections = serializers.ListField(child=UserSerializer())
    similar_interests = serializers.ListField(child=serializers.CharField())


class SocialSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user social settings"""
    
    class Meta:
        model = UserProfile
        fields = [
            'is_private', 'show_activity_status', 'allow_follow_requests'
        ]
    
    def validate(self, data):
        # Custom validation for social settings
        if data.get('is_private') and not data.get('allow_follow_requests'):
            raise serializers.ValidationError(
                "Private accounts must allow follow requests"
            )
        return data


class BulkFollowSerializer(serializers.Serializer):
    """Serializer for bulk follow operations"""
    
    user_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=['follow', 'unfollow'])
    
    def validate_user_ids(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Cannot process more than 50 users at once")
        return value


class SocialExportSerializer(serializers.Serializer):
    """Serializer for social data export"""
    
    data_type = serializers.ChoiceField(choices=[
        'followers', 'following', 'likes', 'comments', 'activity'
    ])
    format = serializers.ChoiceField(choices=['json', 'csv', 'xlsx'])
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    include_private = serializers.BooleanField(default=False)
