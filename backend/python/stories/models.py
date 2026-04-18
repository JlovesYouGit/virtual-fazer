import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Story(models.Model):
    """
    Instagram-style stories with expiration and media support
    """
    STORY_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('text', 'Text'),
        ('reel_share', 'Reel Share'),
        ('post_share', 'Post Share'),
        ('profile_share', 'Profile Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    content_type = models.CharField(max_length=20, choices=STORY_TYPE_CHOICES)
    media_file = models.FileField(
        upload_to='stories/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm'])]
    )
    text_content = models.TextField(blank=True, null=True)
    background_color = models.CharField(max_length=7, default='#000000')  # Hex color
    text_color = models.CharField(max_length=7, default='#FFFFFF')  # Hex color
    
    # Story metadata
    caption = models.TextField(blank=True, max_length=2000)
    hashtags = models.TextField(blank=True, help_text="Comma-separated hashtags")
    mentions = models.TextField(blank=True, help_text="Comma-separated usernames")
    
    # Expiration settings
    expires_at = models.DateTimeField()
    is_expired = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stories'
        indexes = [
            models.Index(fields=['user', 'is_active', 'expires_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active', 'is_expired']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s story - {self.content_type}"
    
    def save(self, *args, **kwargs):
        # Set expiration time (24 hours from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        
        # Check if story has expired
        if timezone.now() > self.expires_at:
            self.is_expired = True
            self.is_active = False
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired_now(self):
        """Check if story is currently expired"""
        return timezone.now() > self.expires_at
    
    @property
    def time_remaining(self):
        """Get remaining time before expiration"""
        if self.is_expired_now:
            return timedelta(0)
        return self.expires_at - timezone.now()
    
    @property
    def hours_remaining(self):
        """Get hours remaining before expiration"""
        return max(0, self.time_remaining.total_seconds() / 3600)
    
    def get_media_url(self):
        """Get media file URL"""
        if self.media_file:
            return self.media_file.url
        return None
    
    def get_hashtags_list(self):
        """Get hashtags as list"""
        if self.hashtags:
            return [tag.strip() for tag in self.hashtags.split(',') if tag.strip()]
        return []
    
    def get_mentions_list(self):
        """Get mentions as list"""
        if self.mentions:
            return [mention.strip() for mention in self.mentions.split(',') if mention.strip()]
        return []


class StoryView(models.Model):
    """
    Track story views and viewers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_duration = models.PositiveIntegerField(default=0, help_text="View duration in seconds")
    
    class Meta:
        db_table = 'story_views'
        unique_together = ['story', 'viewer']
        indexes = [
            models.Index(fields=['story', 'viewer']),
            models.Index(fields=['viewer', 'viewed_at']),
        ]
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.story.user.username}'s story"


class StoryLike(models.Model):
    """
    Track story likes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='story_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_stories')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_likes'
        unique_together = ['story', 'user']
        indexes = [
            models.Index(fields=['story', 'user']),
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} liked {self.story.user.username}'s story"


class StoryReply(models.Model):
    """
    Story replies (comments on stories)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_replies')
    content = models.TextField(max_length=1000)
    
    # Reply threading
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='thread_replies')
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_deleted = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'story_replies'
        indexes = [
            models.Index(fields=['story', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} replied to {self.story.user.username}'s story"


class StoryShare(models.Model):
    """
    Track story shares
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_stories')
    share_type = models.CharField(
        max_length=20,
        choices=[
            ('direct_message', 'Direct Message'),
            ('post', 'Post'),
            ('external', 'External'),
            ('story', 'Story'),
        ]
    )
    shared_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='received_story_shares',
        help_text="User who received the share (for DMs)"
    )
    caption = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_shares'
        indexes = [
            models.Index(fields=['story', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['share_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} shared {self.story.user.username}'s story"


class StoryHighlight(models.Model):
    """
    Story highlights (saved stories that don't expire)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    title = models.CharField(max_length=100)
    cover_story = models.ForeignKey(Story, on_delete=models.SET_NULL, null=True, blank=True, related_name='highlight_covers')
    stories = models.ManyToManyField(Story, related_name='highlights')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'story_highlights'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s highlight: {self.title}"
    
    @property
    def stories_count(self):
        """Get number of stories in highlight"""
        return self.stories.filter(is_active=True, is_expired=False).count()


class StoryMention(models.Model):
    """
    Track user mentions in stories
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='story_mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_mentions')
    position_x = models.FloatField(null=True, blank=True, help_text="X position of mention in story")
    position_y = models.FloatField(null=True, blank=True, help_text="Y position of mention in story")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_mentions'
        unique_together = ['story', 'mentioned_user']
        indexes = [
            models.Index(fields=['story', 'mentioned_user']),
            models.Index(fields=['mentioned_user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.story.user.username} mentioned {self.mentioned_user.username}"


class StoryAnalytics(models.Model):
    """
    Daily analytics for stories
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Metrics
    views_count = models.PositiveIntegerField(default=0)
    unique_viewers = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0.0, help_text="Percentage of viewers who watched the full story")
    
    # Engagement metrics
    engagement_rate = models.FloatField(default=0.0, help_text="Engagement rate as percentage")
    reach = models.PositiveIntegerField(default=0, help_text="Unique users who saw the story")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_analytics'
        unique_together = ['story', 'date']
        indexes = [
            models.Index(fields=['story', 'date']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.story.user.username}'s story on {self.date}"
