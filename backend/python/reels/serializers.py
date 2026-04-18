from rest_framework import serializers
from .models import (
    Reel, ReelInteraction, ReelComment, ReelHashtag, ReelMusic,
    ReelAnalytics, ReelRecommendation, ReelChallenge, ReelChallengeEntry
)
from users.serializers import UserSerializer


class ReelSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    interactions_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Reel
        fields = '__all__'
        read_only_fields = ('id', 'creator', 'view_count', 'like_count', 
                          'comment_count', 'share_count', 'created_at', 'updated_at')
    
    def get_interactions_count(self, obj):
        return obj.interactions.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.interactions.filter(
                user=request.user,
                interaction_type=ReelInteraction.LIKE
            ).exists()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.interactions.filter(
                user=request.user,
                interaction_type=ReelInteraction.SAVE
            ).exists()
        return False


class ReelInteractionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reel = ReelSerializer(read_only=True)
    
    class Meta:
        model = ReelInteraction
        fields = '__all__'


class ReelCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reel = ReelSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = ReelComment
        fields = '__all__'
        read_only_fields = ('id', 'user', 'reel', 'like_count', 'created_at', 'updated_at')
    
    def get_replies(self, obj):
        if obj.parent is None:  # Only get replies for top-level comments
            replies = obj.replies.filter(is_deleted=False).order_by('created_at')
            return ReelCommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_like_count(self, obj):
        return obj.reactions.filter(emoji='like').count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(
                user=request.user,
                emoji='like'
            ).exists()
        return False


class ReelHashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReelHashtag
        fields = '__all__'


class ReelMusicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReelMusic
        fields = '__all__'


class ReelAnalyticsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ReelAnalytics
        fields = '__all__'


class ReelRecommendationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reel = ReelSerializer(read_only=True)
    
    class Meta:
        model = ReelRecommendation
        fields = '__all__'


class ReelChallengeSerializer(serializers.ModelSerializer):
    entries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReelChallenge
        fields = '__all__'
    
    def get_entries_count(self, obj):
        return obj.entries.count()


class ReelChallengeEntrySerializer(serializers.ModelSerializer):
    challenge = ReelChallengeSerializer(read_only=True)
    reel = ReelSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ReelChallengeEntry
        fields = '__all__'


class CreateReelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ('caption', 'video_file', 'thumbnail', 'duration', 'width', 'height',
                 'is_private', 'allow_comments', 'allow_duet', 'allow_share',
                 'music_track', 'hashtags', 'mentions', 'location')
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['creator'] = request.user
        return super().create(validated_data)


class ReelInteractionSerializer(serializers.Serializer):
    reel_id = serializers.UUIDField()
    interaction_type = serializers.ChoiceField(choices=ReelInteraction.INTERACTION_TYPES)
    metadata = serializers.JSONField(default=dict)


class ReelCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReelComment
        fields = ('reel', 'content', 'parent')
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ReelSearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=100, required=False)
    hashtags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    music_track = serializers.CharField(max_length=200, required=False)
    min_duration = serializers.IntegerField(required=False)
    max_duration = serializers.IntegerField(required=False)
    sort_by = serializers.ChoiceField(
        choices=['created_at', 'view_count', 'like_count', 'comment_count'],
        default='created_at'
    )
    sort_order = serializers.ChoiceField(choices=['asc', 'desc'], default='desc')


class TrendingReelsSerializer(serializers.Serializer):
    time_range = serializers.ChoiceField(
        choices=['hour', 'day', 'week', 'month'],
        default='day'
    )
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)
