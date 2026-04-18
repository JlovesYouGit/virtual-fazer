from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Connection(models.Model):
    FOLLOWING = 'following'
    FOLLOW_REQUESTED = 'follow_requested'
    BLOCKED = 'blocked'
    MUTED = 'muted'
    
    STATUS_CHOICES = [
        (FOLLOWING, 'Following'),
        (FOLLOW_REQUESTED, 'Follow Requested'),
        (BLOCKED, 'Blocked'),
        (MUTED, 'Muted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_connections')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_connections')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=FOLLOWING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'status']),
            models.Index(fields=['following', 'status']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} -> {self.following.username} ({self.status})"


class ConnectionRequest(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class UserNetwork(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='network')
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    mutual_follows_count = models.PositiveIntegerField(default=0)
    network_depth = models.PositiveIntegerField(default=1)
    influence_score = models.FloatField(default=0.0)
    connectivity_score = models.FloatField(default=0.0)
    last_analyzed = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Network"


class SuggestedConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggested_connections')
    suggested_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggested_by')
    score = models.FloatField()
    reason = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    is_dismissed = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'suggested_user']
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Suggest {self.suggested_user.username} to {self.user.username} ({self.score})"


class ConnectionAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connection_analytics')
    date = models.DateField()
    new_followers = models.PositiveIntegerField(default=0)
    lost_followers = models.PositiveIntegerField(default=0)
    new_following = models.PositiveIntegerField(default=0)
    unfollowed = models.PositiveIntegerField(default=0)
    profile_views = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    growth_rate = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
