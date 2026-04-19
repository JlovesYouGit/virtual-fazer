from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()


class Follow(models.Model):
    """
    Model for user follow relationships
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class UserProfile(models.Model):
    """
    Extended user profile with social stats
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='social_profile'
    )
    
    # Social statistics
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    reels_count = models.PositiveIntegerField(default=0)
    
    # Profile settings
    is_private = models.BooleanField(default=False)
    show_activity_status = models.BooleanField(default=True)
    allow_follow_requests = models.BooleanField(default=True)
    
    # Engagement tracking
    total_likes_received = models.PositiveIntegerField(default=0)
    total_comments_received = models.PositiveIntegerField(default=0)
    total_shares_received = models.PositiveIntegerField(default=0)
    
    # Last activity
    last_activity = models.DateTimeField(null=True, blank=True)
    last_post_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['followers_count']),
            models.Index(fields=['following_count']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} Profile"
    
    def update_follow_counts(self):
        """Update follower and following counts"""
        self.followers_count = self.user.followers.count()
        self.following_count = self.user.following.count()
        self.save(update_fields=['followers_count', 'following_count'])
    
    def update_content_counts(self):
        """Update posts and reels counts"""
        from reels.models import Reel
        # This would be updated when posts/reels are created/deleted
        pass


class Like(models.Model):
    """
    Generic like model for posts and reels
    """
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('reel', 'Reel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='likes'
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'likes'
        unique_together = ['user', 'content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes {self.content_type} {self.content_id}"


class Share(models.Model):
    """
    Model for sharing posts and reels
    """
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('reel', 'Reel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='shares'
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_id = models.UUIDField(db_index=True)
    caption = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shares'
        unique_together = ['user', 'content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} shared {self.content_type} {self.content_id}"


class FollowRequest(models.Model):
    """
    Model for follow requests (for private accounts)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='follow_requests_sent'
    )
    target = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='follow_requests_received'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'follow_requests'
        unique_together = ['requester', 'target']
        indexes = [
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['target', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.requester.username} -> {self.target.username} ({self.status})"


class UserActivity(models.Model):
    """
    Track user activity for feed algorithm
    """
    ACTIVITY_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
        ('post', 'Post'),
        ('reel', 'Reel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    content_type = models.CharField(max_length=10, blank=True)
    content_id = models.UUIDField(null=True, blank=True, db_index=True)
    target_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='targeted_activities'
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['target_user', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} {self.activity_type} at {self.created_at}"


class Notification(models.Model):
    """
    User notifications for social interactions
    """
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
        ('follow_request', 'Follow Request'),
        ('mention', 'Mention'),
        ('reel_comment', 'Reel Comment'),
        ('post_comment', 'Post Comment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content_type = models.CharField(max_length=10, blank=True)
    content_id = models.UUIDField(null=True, blank=True)
    message = models.TextField(blank=True, max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.notification_type}"


# Signal handlers
@receiver(post_save, sender=Follow)
def handle_follow_created(sender, instance, created, **kwargs):
    """Handle follow creation"""
    if created:
        # Update follower counts
        if hasattr(instance.following, 'social_profile'):
            instance.following.social_profile.update_follow_counts()
        if hasattr(instance.follower, 'social_profile'):
            instance.follower.social_profile.update_follow_counts()
        
        # Create activity
        UserActivity.objects.create(
            user=instance.follower,
            activity_type='follow',
            target_user=instance.following
        )
        
        # Create notification
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow'
        )


@receiver(post_delete, sender=Follow)
def handle_follow_deleted(sender, instance, **kwargs):
    """Handle follow deletion"""
    # Update follower counts
    if hasattr(instance.following, 'social_profile'):
        instance.following.social_profile.update_follow_counts()
    if hasattr(instance.follower, 'social_profile'):
        instance.follower.social_profile.update_follow_counts()


@receiver(post_save, sender=Like)
def handle_like_created(sender, instance, created, **kwargs):
    """Handle like creation"""
    if created:
        # Create activity
        UserActivity.objects.create(
            user=instance.user,
            activity_type='like',
            content_type=instance.content_type,
            content_id=instance.content_id
        )
        
        # Create notification for content owner
        # This would need to get the content owner based on content_type and content_id


@receiver(post_delete, sender=Like)
def handle_like_deleted(sender, instance, **kwargs):
    """Handle like deletion"""
    # Update like counts on content
    pass


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
