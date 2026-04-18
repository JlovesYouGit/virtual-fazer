from rest_framework import serializers
from .models import (
    ChatRoom, ChatParticipant, Message, MessageReaction, MessageRead,
    ChatCategory, RoomCategory, TypingIndicator, ChatAnalytics
)
from users.serializers import UserSerializer


class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = '__all__'


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(source='chatparticipant_set', many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = '__all__'


class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reply_to = MessageSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'


class MessageReadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = '__all__'


class ChatCategorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatCategory
        fields = '__all__'


class RoomCategorySerializer(serializers.ModelSerializer):
    category = ChatCategorySerializer(read_only=True)
    
    class Meta:
        model = RoomCategory
        fields = '__all__'


class TypingIndicatorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TypingIndicator
        fields = '__all__'


class ChatAnalyticsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatAnalytics
        fields = '__all__'


class CreateRoomSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    room_type = serializers.ChoiceField(choices=ChatRoom.ROOM_TYPE_CHOICES, default=ChatRoom.DIRECT)
    participant_ids = serializers.ListField(child=serializers.UUIDField())


class SendMessageSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()
    content = serializers.CharField(max_length=2000)
    message_type = serializers.ChoiceField(choices=Message.MESSAGE_TYPE_CHOICES, default=Message.TEXT)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)


class MarkAsReadSerializer(serializers.Serializer):
    message_id = serializers.UUIDField()


class ReactToMessageSerializer(serializers.Serializer):
    message_id = serializers.UUIDField()
    emoji = serializers.CharField(max_length=50)
