from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import json

from .models import (
    NeuralModel, UserNeuralProfile, CategoryPattern, UserInteraction,
    NeuralPrediction, AutoFollowRule, AutoFollowAction
)
from .serializers import (
    NeuralModelSerializer, UserNeuralProfileSerializer, CategoryPatternSerializer,
    UserInteractionSerializer, NeuralPredictionSerializer, AutoFollowRuleSerializer,
    AutoFollowActionSerializer, UserCategorizationSerializer, UserMatchingSerializer,
    AutoFollowRequestSerializer
)
from users.models import User, UserActivity


class NeuralModelListCreateView(generics.ListCreateAPIView):
    queryset = NeuralModel.objects.all()
    serializer_class = NeuralModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryPatternListCreateView(generics.ListCreateAPIView):
    queryset = CategoryPattern.objects.all()
    serializer_class = CategoryPatternSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def analyze_user_behavior(request):
    """Analyze user behavior and categorize them using neural interface"""
    user = request.user
    
    # Get user interactions from last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    interactions = UserInteraction.objects.filter(
        user=user,
        timestamp__gte=thirty_days_ago
    )
    
    # Extract features from interactions
    features = extract_behavioral_features(interactions)
    
    # Get active category patterns
    patterns = CategoryPattern.objects.filter(is_active=True)
    
    # Calculate category scores
    category_scores = {}
    for pattern in patterns:
        score = calculate_category_score(features, pattern)
        category_scores[pattern.name] = score
    
    # Create or update neural profile
    profile, created = UserNeuralProfile.objects.get_or_create(
        user=user,
        defaults={
            'feature_vector': features,
            'category_scores': category_scores,
            'behavior_patterns': analyze_behavior_patterns(interactions),
            'model_version': '1.0'
        }
    )
    
    if not created:
        profile.feature_vector = features
        profile.category_scores = category_scores
        profile.behavior_patterns = analyze_behavior_patterns(interactions)
        profile.save()
    
    # Save predictions
    for category, score in category_scores.items():
        if score > 0.5:  # Only save significant predictions
            NeuralPrediction.objects.create(
                user=user,
                prediction_type='category',
                predicted_value=category,
                confidence_score=score,
                model_used=NeuralModel.objects.filter(model_type='categorization', is_active=True).first(),
                input_data=features
            )
    
    return Response({
        'user_id': str(user.id),
        'categories': category_scores,
        'confidence_scores': category_scores,
        'behavior_patterns': profile.behavior_patterns
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def find_matching_users(request):
    """Find users matching the current user's profile"""
    user = request.user
    
    try:
        user_profile = UserNeuralProfile.objects.get(user=user)
    except UserNeuralProfile.DoesNotExist:
        return Response({'error': 'User profile not analyzed yet'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get other users with neural profiles
    other_profiles = UserNeuralProfile.objects.exclude(user=user)
    
    # Calculate similarity scores
    matched_users = []
    match_scores = []
    match_reasons = []
    
    for profile in other_profiles:
        similarity = calculate_user_similarity(user_profile, profile)
        if similarity > 0.6:  # Minimum similarity threshold
            matched_users.append(profile.user.id)
            match_scores.append(similarity)
            match_reasons.append(get_match_reason(user_profile, profile))
    
    # Sort by similarity score
    sorted_matches = sorted(zip(matched_users, match_scores, match_reasons), 
                           key=lambda x: x[1], reverse=True)
    
    if sorted_matches:
        matched_users, match_scores, match_reasons = zip(*sorted_matches)
    else:
        matched_users, match_scores, match_reasons = [], [], []
    
    return Response({
        'user_id': str(user.id),
        'matched_users': [str(uid) for uid in matched_users],
        'match_scores': list(match_scores),
        'match_reasons': list(match_reasons)
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def auto_follow_users(request):
    """Automatically follow users based on matching rules"""
    serializer = AutoFollowRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    max_follows = serializer.validated_data['max_follows']
    min_confidence = serializer.validated_data['min_confidence']
    rule_ids = serializer.validated_data.get('rule_ids')
    
    # Get rules to apply
    if rule_ids:
        rules = AutoFollowRule.objects.filter(id__in=rule_ids, is_active=True)
    else:
        rules = AutoFollowRule.objects.filter(is_active=True)
    
    # Check daily limit
    today = timezone.now().date()
    today_follows = AutoFollowAction.objects.filter(
        user=user,
        executed_at__date=today
    ).count()
    
    if today_follows >= max_follows:
        return Response({'error': 'Daily follow limit reached'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get matching users
    try:
        user_profile = UserNeuralProfile.objects.get(user=user)
    except UserNeuralProfile.DoesNotExist:
        return Response({'error': 'User profile not analyzed yet'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Find potential users to follow
    other_profiles = UserNeuralProfile.objects.exclude(user=user)
    followed_count = 0
    
    for profile in other_profiles:
        if followed_count >= max_follows:
            break
        
        # Check each rule
        for rule in rules:
            if evaluate_auto_follow_rule(user_profile, profile, rule, min_confidence):
                # Create auto-follow action
                AutoFollowAction.objects.create(
                    user=user,
                    target_user=profile.user,
                    rule=rule,
                    confidence_score=calculate_user_similarity(user_profile, profile)
                )
                
                # Log the follow activity
                UserActivity.objects.create(
                    user=user,
                    activity_type='follow',
                    target_user=profile.user,
                    metadata={'auto_follow': True, 'rule': rule.name}
                )
                
                followed_count += 1
                break
    
    return Response({
        'message': f'Auto-followed {followed_count} users',
        'followed_count': followed_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_neural_profile(request):
    """Get the current user's neural profile"""
    try:
        profile = UserNeuralProfile.objects.get(user=request.user)
        serializer = UserNeuralProfileSerializer(profile)
        return Response(serializer.data)
    except UserNeuralProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_interactions(request):
    """Get user's interaction history"""
    interactions = UserInteraction.objects.filter(user=request.user).order_by('-timestamp')[:100]
    serializer = UserInteractionSerializer(interactions, many=True)
    return Response(serializer.data)


# Helper functions
def extract_behavioral_features(interactions):
    """Extract behavioral features from user interactions"""
    features = {
        'total_interactions': interactions.count(),
        'like_ratio': 0,
        'comment_ratio': 0,
        'share_ratio': 0,
        'follow_ratio': 0,
        'message_ratio': 0,
        'view_duration_avg': 0,
        'activity_frequency': 0,
        'content_preferences': {},
        'time_patterns': {}
    }
    
    if not interactions.exists():
        return features
    
    total = interactions.count()
    like_count = interactions.filter(interaction_type='like').count()
    comment_count = interactions.filter(interaction_type='comment').count()
    share_count = interactions.filter(interaction_type='share').count()
    follow_count = interactions.filter(interaction_type='follow').count()
    message_count = interactions.filter(interaction_type='message').count()
    
    features['like_ratio'] = like_count / total
    features['comment_ratio'] = comment_count / total
    features['share_ratio'] = share_count / total
    features['follow_ratio'] = follow_count / total
    features['message_ratio'] = message_count / total
    
    # Average view duration
    view_interactions = interactions.filter(duration__isnull=False)
    if view_interactions.exists():
        features['view_duration_avg'] = view_interactions.aggregate(
            avg_duration=models.Avg('duration')
        )['avg_duration'] or 0
    
    # Content preferences
    content_types = interactions.values('content_type').annotate(count=models.Count('id'))
    features['content_preferences'] = {
        item['content_type']: item['count'] / total 
        for item in content_types
    }
    
    return features


def calculate_category_score(features, pattern):
    """Calculate category score based on pattern matching"""
    score = 0.0
    
    # Match behavior weights
    behavior_weights = pattern.behavior_weights
    for behavior, weight in behavior_weights.items():
        if behavior in features:
            score += features[behavior] * weight
    
    # Match keywords (if available in metadata)
    # This would be enhanced with NLP processing
    
    return min(score, 1.0)


def analyze_behavior_patterns(interactions):
    """Analyze user behavior patterns"""
    patterns = {
        'peak_activity_hours': [],
        'content_consumption_rate': 0,
        'engagement_rate': 0,
        'social_interaction_level': 'low'
    }
    
    if not interactions.exists():
        return patterns
    
    # Peak activity hours
    hour_counts = {}
    for interaction in interactions:
        hour = interaction.timestamp.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    if hour_counts:
        peak_hour = max(hour_counts, key=hour_counts.get)
        patterns['peak_activity_hours'] = [peak_hour]
    
    # Engagement rate (likes + comments) / total views
    total_views = interactions.filter(interaction_type='view').count()
    total_engagements = interactions.filter(
        interaction_type__in=['like', 'comment']
    ).count()
    
    if total_views > 0:
        patterns['engagement_rate'] = total_engagements / total_views
    
    # Social interaction level
    social_interactions = interactions.filter(
        interaction_type__in=['follow', 'message', 'comment']
    ).count()
    
    social_ratio = social_interactions / interactions.count()
    if social_ratio > 0.3:
        patterns['social_interaction_level'] = 'high'
    elif social_ratio > 0.1:
        patterns['social_interaction_level'] = 'medium'
    
    return patterns


def calculate_user_similarity(profile1, profile2):
    """Calculate similarity between two user profiles"""
    # Simple cosine similarity on category scores
    categories1 = profile1.category_scores
    categories2 = profile2.category_scores
    
    # Get common categories
    common_categories = set(categories1.keys()) & set(categories2.keys())
    
    if not common_categories:
        return 0.0
    
    # Calculate cosine similarity
    dot_product = sum(categories1[cat] * categories2[cat] for cat in common_categories)
    norm1 = sum(categories1[cat] ** 2 for cat in common_categories) ** 0.5
    norm2 = sum(categories2[cat] ** 2 for cat in common_categories) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def get_match_reason(profile1, profile2):
    """Get reason for user match"""
    categories1 = profile1.category_scores
    categories2 = profile2.category_scores
    
    # Find top matching categories
    common_categories = set(categories1.keys()) & set(categories2.keys())
    category_scores = []
    
    for cat in common_categories:
        avg_score = (categories1[cat] + categories2[cat]) / 2
        category_scores.append((cat, avg_score))
    
    category_scores.sort(key=lambda x: x[1], reverse=True)
    
    if category_scores:
        return f"Similar interest in {category_scores[0][0]}"
    else:
        return "General similarity"


def evaluate_auto_follow_rule(user_profile, target_profile, rule, min_confidence):
    """Evaluate if auto-follow rule should be applied"""
    similarity = calculate_user_similarity(user_profile, target_profile)
    
    if similarity < min_confidence:
        return False
    
    # Check category match
    if rule.category_match:
        for category, threshold in rule.category_match.items():
            user_score = user_profile.category_scores.get(category, 0)
            target_score = target_profile.category_scores.get(category, 0)
            
            if user_score < threshold or target_score < threshold:
                return False
    
    # Check behavior threshold
    if similarity < rule.behavior_threshold:
        return False
    
    # Check follower counts (would need to be implemented)
    # This is a placeholder for follower count logic
    
    return True
