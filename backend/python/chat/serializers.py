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
    reply_to = serializers.StringRelatedField(read_only=True)
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


class InboxRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for chat rooms in inbox view with additional metadata
    """
    participants = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    last_message_content = serializers.CharField(read_only=True)
    last_message_time = serializers.DateTimeField(read_only=True)
    last_message_sender = serializers.CharField(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'created_by', 'is_active',
            'last_message', 'last_message_time', 'created_at', 'updated_at',
            'participants', 'unread_count', 'last_message_content', 
            'last_message_sender'
        ]
    
    def get_participants(self, obj):
        """Get participant details for inbox display"""
        participants = obj.participants.all()
        return [
            {
                'id': str(p.id),
                'username': p.username,
                'first_name': p.first_name,
                'last_name': p.last_name
            }
            for p in participants
        ]


class InboxMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for messages in inbox view with additional metadata
    """
    sender = UserSerializer(read_only=True)
    reply_to = MessageSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    read_receipts = MessageReadSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'content', 'message_type', 'media_file',
            'reply_to', 'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'metadata', 'created_at', 'updated_at', 'reactions', 'is_read',
            'read_receipts'
        ]
    
    def get_is_read(self, obj):
        """Check if message is read by current user"""
        request = self.context.get('request')
        if request and request.user:
            return MessageRead.objects.filter(message=obj, user=request.user).exists()
        return False


class DirectMessageSerializer(serializers.Serializer):
    """Serializer for creating direct messages"""
    recipient_id = serializers.UUIDField()
    initial_message = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class RoomActionSerializer(serializers.Serializer):
    """Serializer for room actions (mute, archive, etc.)"""
    action = serializers.ChoiceField(choices=['mute', 'unmute', 'archive', 'unarchive', 'leave', 'delete'])
    is_muted = serializers.BooleanField(required=False)  # For mute/unmute action


class MessageSearchSerializer(serializers.Serializer):
    """Serializer for message search"""
    query = serializers.CharField(min_length=1, max_length=100)
    room_id = serializers.UUIDField(required=False)
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPE_CHOICES, 
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
