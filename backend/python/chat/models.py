from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class ChatRoom(models.Model):
    DIRECT = 'direct'
    GROUP = 'group'
    
    ROOM_TYPE_CHOICES = [
        (DIRECT, 'Direct Message'),
        (GROUP, 'Group Chat'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default=DIRECT)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    participants = models.ManyToManyField(User, related_name='chat_rooms', through='ChatParticipant')
    is_active = models.BooleanField(default=True)
    last_message = models.TextField(blank=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['room_type', 'is_active']),
            models.Index(fields=['last_message_time']),
        ]
    
    def __str__(self):
        if self.room_type == self.DIRECT:
            participants = self.participants.all()[:2]
            return f"DM: {' - '.join([p.username for p in participants])}"
        return self.name or f"Group {self.id}"


class ChatParticipant(models.Model):
    ADMIN = 'admin'
    MEMBER = 'member'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['room', 'user']
        indexes = [
            models.Index(fields=['user', 'room']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name or self.room.id}"


class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    FILE = 'file'
    REEL_SHARE = 'reel_share'
    PROFILE_SHARE = 'profile_share'
    
    MESSAGE_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (FILE, 'File'),
        (REEL_SHARE, 'Reel Share'),
        (PROFILE_SHARE, 'Profile Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default=TEXT)
    media_file = models.FileField(upload_to='chat_media/', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..." if len(self.content) > 50 else f"{self.sender.username}: {self.content}"


class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'emoji']
    
    def __str__(self):
        return f"{self.user.username} {self.emoji} on {self.message.id}"


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} read {self.message.id}"


class ChatCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class RoomCategory(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='room_categories')
    category = models.ForeignKey(ChatCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'category']
    
    def __str__(self):
        return f"{self.room.name or self.room.id} - {self.category.name}"


class TypingIndicator(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['room', 'user']
    
    def __str__(self):
        return f"{self.user.username} typing in {self.room.name or self.room.id}"


class ChatAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_analytics')
    date = models.DateField()
    messages_sent = models.PositiveIntegerField(default=0)
    messages_received = models.PositiveIntegerField(default=0)
    active_rooms = models.PositiveIntegerField(default=0)
    response_time_avg = models.FloatField(default=0.0)  # in seconds
    engagement_score = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
