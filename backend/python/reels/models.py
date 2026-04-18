from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import json

User = get_user_model()


class Reel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reels')
    caption = models.TextField(max_length=2200, blank=True)
    video_file = models.FileField(upload_to='reels/videos/')
    thumbnail = models.ImageField(upload_to='reels/thumbnails/', null=True, blank=True)
    duration = models.FloatField(help_text="Duration in seconds")
    width = models.IntegerField(default=720)
    height = models.IntegerField(default=1280)
    is_private = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    allow_duet = models.BooleanField(default=True)
    allow_share = models.BooleanField(default=True)
    music_track = models.CharField(max_length=200, blank=True)
    hashtags = models.JSONField(default=list)
    mentions = models.JSONField(default=list)
    location = models.CharField(max_length=200, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', '-created_at']),
            models.Index(fields=['is_trending', '-view_count']),
            models.Index(fields=['is_featured', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.creator.username}'s Reel: {self.caption[:50]}..."


class ReelInteraction(models.Model):
    LIKE = 'like'
    COMMENT = 'comment'
    SHARE = 'share'
    SAVE = 'save'
    DUET = 'duet'
    VIEW = 'view'
    
    INTERACTION_TYPES = [
        (LIKE, 'Like'),
        (COMMENT, 'Comment'),
        (SHARE, 'Share'),
        (SAVE, 'Save'),
        (DUET, 'Duet'),
        (VIEW, 'View'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='interactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['reel', 'user', 'interaction_type']
        indexes = [
            models.Index(fields=['reel', 'interaction_type', '-created_at']),
            models.Index(fields=['user', 'interaction_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.reel.id}"


class ReelComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField(max_length=1000)
    is_deleted = models.BooleanField(default=False)
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['reel', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} on {self.reel.id}: {self.content[:50]}..."


class ReelHashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    usage_count = models.PositiveIntegerField(default=0)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-usage_count']
    
    def __str__(self):
        return f"#{self.name}"


class ReelMusic(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='reels/music/')
    duration = models.FloatField()
    usage_count = models.PositiveIntegerField(default=0)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['title', 'artist']
        ordering = ['-usage_count']
    
    def __str__(self):
        return f"{self.title} by {self.artist}"


class ReelAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_analytics')
    date = models.DateField()
    reels_created = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    reach = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class ReelRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_recommendations')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField()
    reason = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)
    is_liked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'reel']
        indexes = [
            models.Index(fields=['user', '-score', '-created_at']),
            models.Index(fields=['reel', '-score']),
        ]
    
    def __str__(self):
        return f"Recommend {self.reel.id} to {self.user.username} ({self.score})"


class ReelChallenge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    hashtag = models.CharField(max_length=100, unique=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    prize = models.CharField(max_length=200, blank=True)
    rules = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    participant_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ReelChallengeEntry(models.Model):
    challenge = models.ForeignKey(ReelChallenge, on_delete=models.CASCADE, related_name='entries')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_entries')
    score = models.FloatField(default=0.0)
    votes = models.PositiveIntegerField(default=0)
    is_winner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['challenge', 'reel']
        ordering = ['-score', '-votes']
    
    def __str__(self):
        return f"{self.user.username}'s entry for {self.challenge.name}"


class ReelForward(models.Model):
    """Track forwarded reels and save status"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='forwards')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_reel_forwards')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reel_forwards')
    message = models.TextField(max_length=500, blank=True, help_text="Optional message from sender")
    is_saved = models.BooleanField(default=False, help_text="Whether recipient has saved the reel")
    created_at = models.DateTimeField(auto_now_add=True)
    saved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['reel', 'sender', 'recipient']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['reel', '-created_at']),
            models.Index(fields=['is_saved', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} forwarded {self.reel.id} to {self.recipient.username}"
    
    def mark_as_saved(self):
        """Mark the forwarded reel as saved"""
        if not self.is_saved:
            self.is_saved = True
            self.saved_at = timezone.now()
            self.save()
