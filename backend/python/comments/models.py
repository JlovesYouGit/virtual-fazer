from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.utils import timezone
import uuid
from django.core.validators import MinLengthValidator, MaxLengthValidator


class Comment(models.Model):
    """
    Model for comments on posts/reels
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content relationship
    content_type = models.CharField(max_length=20, choices=[
        ('reel', 'Reel'),
        ('post', 'Post'),
    ])
    content_id = models.UUIDField(db_index=True)
    
    # Comment content
    text = models.TextField(
        validators=[MinLengthValidator(1), MaxLengthValidator(2000)]
    )
    
    # Author
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    
    # Thread structure (for replies)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    
    # Moderation
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    moderation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='approved'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['content_type', 'content_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} on {self.content_type} {self.content_id}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    @property
    def root_comment(self):
        """Get the root comment of this thread"""
        if self.parent is None:
            return self
        return self.parent.root_comment
    
    def save(self, *args, **kwargs):
        # Update parent's replies count if this is a reply
        if self.parent and not self.id:  # New comment
            self.parent.replies_count += 1
            self.parent.save(update_fields=['replies_count'])
        
        # Set edited timestamp if comment is being edited
        if self.id and 'text' in kwargs:
            self.is_edited = True
            self.edited_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Soft delete
        self.is_deleted = True
        self.text = "[deleted]"
        self.save(update_fields=['is_deleted', 'text'])
    
    def get_absolute_url(self):
        return f"/{self.content_type}/{self.content_id}#comment-{self.id}"


class CommentLike(models.Model):
    """
    Model for likes on comments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='likes'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_likes'
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class CommentMention(models.Model):
    """
    Model for user mentions in comments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='mentions'
    )
    mentioned_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_mentions'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_mentions'
        unique_together = ['comment', 'mentioned_user']
        indexes = [
            models.Index(fields=['mentioned_user', 'is_read', 'created_at']),
            models.Index(fields=['comment', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.comment.user.username} mentioned {self.mentioned_user.username}"


class CommentThread(models.Model):
    """
    Model for tracking comment threads on content
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content relationship
    content_type = models.CharField(max_length=20, choices=[
        ('reel', 'Reel'),
        ('post', 'Post'),
    ])
    content_id = models.UUIDField(db_index=True)
    
    # Thread statistics
    comments_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    participants_count = models.PositiveIntegerField(default=0)
    
    # Last activity tracking
    last_comment_at = models.DateTimeField(null=True, blank=True)
    last_comment_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='last_threads'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comment_threads'
        unique_together = ['content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['last_comment_at']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Thread for {self.content_type} {self.content_id}"
    
    def update_statistics(self):
        """Update thread statistics based on comments"""
        comments = Comment.objects.filter(
            content_type=self.content_type,
            content_id=self.content_id,
            is_deleted=False
        )
        
        self.comments_count = comments.count()
        self.likes_count = CommentLike.objects.filter(
            comment__in=comments
        ).count()
        self.participants_count = comments.values('user').distinct().count()
        
        # Update last activity
        last_comment = comments.order_by('-created_at').first()
        if last_comment:
            self.last_comment_at = last_comment.created_at
            self.last_comment_by = last_comment.user
        
        self.save()


class CommentReport(models.Model):
    """
    Model for reporting inappropriate comments
    """
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('inappropriate', 'Inappropriate Content'),
        ('off_topic', 'Off-topic'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_reports'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)
    action_taken = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('deleted', 'Deleted'),
            ('user_warned', 'User Warned'),
            ('user_suspended', 'User Suspended'),
        ],
        default='none'
    )
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_reports'
        unique_together = ['comment', 'reporter']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['is_reviewed', 'created_at']),
        ]
    
    def __str__(self):
        return f"Report on comment {self.comment.id} by {self.reporter.username}"


class CommentNotification(models.Model):
    """
    Model for comment notifications
    """
    NOTIFICATION_TYPES = [
        ('reply', 'Reply to Comment'),
        ('mention', 'Mention in Comment'),
        ('like', 'Like on Comment'),
        ('thread_update', 'Thread Update'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_notifications'
    )
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_notifications'
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"
