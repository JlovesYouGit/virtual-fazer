from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class NeuralModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20)
    model_type = models.CharField(max_length=50, choices=[
        ('categorization', 'User Categorization'),
        ('recommendation', 'Content Recommendation'),
        ('behavior_analysis', 'Behavior Analysis'),
        ('connection_matching', 'Connection Matching'),
    ])
    model_path = models.CharField(max_length=500)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    accuracy_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class UserNeuralProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='neural_profile')
    feature_vector = models.JSONField(default=list)
    category_scores = models.JSONField(default=dict)
    behavior_patterns = models.JSONField(default=dict)
    last_analyzed = models.DateTimeField(auto_now=True)
    model_version = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.user.username}'s Neural Profile"


class CategoryPattern(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    keywords = models.JSONField(default=list)
    behavior_weights = models.JSONField(default=dict)
    threshold_score = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='neural_interactions')
    interaction_type = models.CharField(max_length=50, choices=[
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('save', 'Save'),
        ('follow', 'Follow'),
        ('unfollow', 'Unfollow'),
        ('message', 'Message'),
        ('view', 'View'),
        ('skip', 'Skip'),
    ])
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='target_interactions')
    content_type = models.CharField(max_length=50, choices=[
        ('post', 'Post'),
        ('reel', 'Reel'),
        ('story', 'Story'),
        ('profile', 'Profile'),
        ('message', 'Message'),
    ], null=True, blank=True)
    content_id = models.CharField(max_length=100, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # in seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['interaction_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} at {self.timestamp}"


class NeuralPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='neural_predictions')
    prediction_type = models.CharField(max_length=50, choices=[
        ('category', 'Category Prediction'),
        ('connection', 'Connection Prediction'),
        ('content', 'Content Prediction'),
        ('behavior', 'Behavior Prediction'),
    ])
    predicted_value = models.CharField(max_length=200)
    confidence_score = models.FloatField()
    model_used = models.ForeignKey(NeuralModel, on_delete=models.CASCADE)
    input_data = models.JSONField(default=dict)
    is_correct = models.BooleanField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.prediction_type}: {self.predicted_value} ({self.confidence_score})"


class AutoFollowRule(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category_match = models.JSONField(default=dict)
    behavior_threshold = models.FloatField(default=0.8)
    min_followers = models.IntegerField(default=0)
    max_followers = models.IntegerField(null=True, blank=True)
    follow_ratio_min = models.FloatField(default=0.0)
    follow_ratio_max = models.FloatField(default=10.0)
    activity_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    is_active = models.BooleanField(default=True)
    max_follows_per_day = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class AutoFollowAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_follow_actions')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_followed_by')
    rule = models.ForeignKey(AutoFollowRule, on_delete=models.CASCADE)
    confidence_score = models.FloatField()
    executed_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'target_user']
    
    def __str__(self):
        return f"{self.user.username} -> {self.target_user.username}"
