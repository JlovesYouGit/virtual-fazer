from rest_framework import serializers
from .models import Connection, ConnectionRequest, UserNetwork, SuggestedConnection, ConnectionAnalytics
from users.serializers import UserSerializer


class ConnectionSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Connection
        fields = '__all__'


class ConnectionRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConnectionRequest
        fields = '__all__'


class UserNetworkSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserNetwork
        fields = '__all__'


class SuggestedConnectionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    suggested_user = UserSerializer(read_only=True)
    
    class Meta:
        model = SuggestedConnection
        fields = '__all__'


class ConnectionAnalyticsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConnectionAnalytics
        fields = '__all__'


class FollowUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)


class UnfollowUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class BlockUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class MuteUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
