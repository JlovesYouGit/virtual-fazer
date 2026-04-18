from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, F

from .models import Connection, ConnectionRequest, UserNetwork, SuggestedConnection, ConnectionAnalytics
from .serializers import (
    ConnectionSerializer, ConnectionRequestSerializer, UserNetworkSerializer,
    SuggestedConnectionSerializer, ConnectionAnalyticsSerializer,
    FollowUserSerializer, UnfollowUserSerializer, BlockUserSerializer, MuteUserSerializer
)
from users.models import User, UserActivity
from neural.models import UserNeuralProfile


class ConnectionListView(generics.ListAPIView):
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        connection_type = self.request.query_params.get('type', 'following')
        
        if connection_type == 'followers':
            return Connection.objects.filter(following=user, status=Connection.FOLLOWING)
        elif connection_type == 'following':
            return Connection.objects.filter(follower=user, status=Connection.FOLLOWING)
        elif connection_type == 'requests':
            return Connection.objects.filter(following=user, status=Connection.FOLLOW_REQUESTED)
        else:
            return Connection.objects.filter(Q(follower=user) | Q(following=user))


class SuggestedConnectionListView(generics.ListAPIView):
    serializer_class = SuggestedConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SuggestedConnection.objects.filter(
            user=self.request.user,
            is_dismissed=False,
            is_connected=False
        ).order_by('-score')[:50]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def follow_user(request):
    """Follow a user"""
    serializer = FollowUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    follower = request.user
    following_id = serializer.validated_data['user_id']
    message = serializer.validated_data.get('message', '')
    
    try:
        following = User.objects.get(id=following_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if follower == following:
        return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if already following
    existing_connection = Connection.objects.filter(
        follower=follower,
        following=following
    ).first()
    
    if existing_connection:
        if existing_connection.status == Connection.FOLLOWING:
            return Response({'error': 'Already following this user'}, status=status.HTTP_400_BAD_REQUEST)
        elif existing_connection.status == Connection.BLOCKED:
            return Response({'error': 'Cannot follow blocked user'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if target user is private
    try:
        target_profile = following.profile
        if target_profile.is_private:
            # Create follow request
            connection_request, created = ConnectionRequest.objects.get_or_create(
                from_user=follower,
                to_user=following,
                defaults={'message': message}
            )
            
            if not created:
                return Response({'error': 'Follow request already sent'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create connection with requested status
            connection, _ = Connection.objects.get_or_create(
                follower=follower,
                following=following,
                defaults={'status': Connection.FOLLOW_REQUESTED}
            )
            
            return Response({
                'message': 'Follow request sent',
                'status': 'requested'
            }, status=status.HTTP_201_CREATED)
        else:
            # Direct follow for public accounts
            connection, created = Connection.objects.get_or_create(
                follower=follower,
                following=following,
                defaults={'status': Connection.FOLLOWING}
            )
            
            if not created:
                connection.status = Connection.FOLLOWING
                connection.save()
            
            # Update network stats
            update_user_network_stats(follower)
            update_user_network_stats(following)
            
            # Log activity
            UserActivity.objects.create(
                user=follower,
                activity_type='follow',
                target_user=following,
                metadata={'direct_follow': True}
            )
            
            return Response({
                'message': 'User followed successfully',
                'status': 'following'
            }, status=status.HTTP_201_CREATED)
    
    except:
        # If profile doesn't exist, follow directly
        connection, created = Connection.objects.get_or_create(
            follower=follower,
            following=following,
            defaults={'status': Connection.FOLLOWING}
        )
        
        if not created:
            connection.status = Connection.FOLLOWING
            connection.save()
        
        return Response({
            'message': 'User followed successfully',
            'status': 'following'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unfollow_user(request):
    """Unfollow a user"""
    serializer = UnfollowUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    target_user_id = serializer.validated_data['user_id']
    
    try:
        target_user = User.objects.get(id=target_user_id)
        connection = Connection.objects.get(
            follower=user,
            following=target_user,
            status=Connection.FOLLOWING
        )
        
        connection.delete()
        
        # Update network stats
        update_user_network_stats(user)
        update_user_network_stats(target_user)
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='unfollow',
            target_user=target_user
        )
        
        return Response({'message': 'User unfollowed successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Connection.DoesNotExist:
        return Response({'error': 'Not following this user'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def block_user(request):
    """Block a user"""
    serializer = BlockUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    target_user_id = serializer.validated_data['user_id']
    
    try:
        target_user = User.objects.get(id=target_user_id)
        
        # Remove any existing connections
        Connection.objects.filter(
            Q(follower=user, following=target_user) |
            Q(follower=target_user, following=user)
        ).delete()
        
        # Create block connection
        Connection.objects.update_or_create(
            follower=user,
            following=target_user,
            defaults={'status': Connection.BLOCKED}
        )
        
        return Response({'message': 'User blocked successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mute_user(request):
    """Mute a user"""
    serializer = MuteUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    target_user_id = serializer.validated_data['user_id']
    
    try:
        target_user = User.objects.get(id=target_user_id)
        
        # Create or update mute connection
        connection, created = Connection.objects.update_or_create(
            follower=user,
            following=target_user,
            defaults={'status': Connection.MUTED}
        )
        
        return Response({'message': 'User muted successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_network(request):
    """Get user's network information"""
    user = request.user
    network, created = UserNetwork.objects.get_or_create(user=user)
    
    serializer = UserNetworkSerializer(network)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_connection_analytics(request):
    """Get connection analytics for the user"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    analytics = ConnectionAnalytics.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('-date')
    
    serializer = ConnectionAnalyticsSerializer(analytics, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_suggestions(request):
    """Generate connection suggestions using neural matching"""
    user = request.user
    
    try:
        user_profile = UserNeuralProfile.objects.get(user=user)
    except UserNeuralProfile.DoesNotExist:
        return Response({'error': 'User profile not analyzed yet'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get users not already connected
    connected_users = Connection.objects.filter(
        Q(follower=user) | Q(following=user)
    ).values_list('follower_id', 'following_id')
    
    connected_user_ids = set()
    for follower_id, following_id in connected_users:
        connected_user_ids.add(str(follower_id))
        connected_user_ids.add(str(following_id))
    
    # Get potential matches
    other_profiles = UserNeuralProfile.objects.exclude(
        user_id__in=connected_user_ids
    ).exclude(user=user)
    
    suggestions_created = 0
    for profile in other_profiles:
        # Calculate similarity
        similarity = calculate_profile_similarity(user_profile, profile)
        
        if similarity > 0.6:  # Minimum threshold
            # Get match reason
            reason = get_match_reason(user_profile, profile)
            
            # Create suggestion
            suggestion, created = SuggestedConnection.objects.get_or_create(
                user=user,
                suggested_user=profile.user,
                defaults={
                    'score': similarity,
                    'reason': reason,
                    'metadata': {
                        'similarity_score': similarity,
                        'common_categories': get_common_categories(user_profile, profile)
                    }
                }
            )
            
            if created:
                suggestions_created += 1
    
    return Response({
        'message': f'Generated {suggestions_created} new suggestions',
        'suggestions_count': suggestions_created
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def dismiss_suggestion(request):
    """Dismiss a connection suggestion"""
    suggestion_id = request.data.get('suggestion_id')
    
    try:
        suggestion = SuggestedConnection.objects.get(
            id=suggestion_id,
            user=request.user
        )
        suggestion.is_dismissed = True
        suggestion.save()
        
        return Response({'message': 'Suggestion dismissed'})
    
    except SuggestedConnection.DoesNotExist:
        return Response({'error': 'Suggestion not found'}, status=status.HTTP_404_NOT_FOUND)


# Helper functions
def update_user_network_stats(user):
    """Update user's network statistics"""
    followers_count = Connection.objects.filter(
        following=user,
        status=Connection.FOLLOWING
    ).count()
    
    following_count = Connection.objects.filter(
        follower=user,
        status=Connection.FOLLOWING
    ).count()
    
    # Calculate mutual follows
    following_ids = Connection.objects.filter(
        follower=user,
        status=Connection.FOLLOWING
    ).values_list('following_id', flat=True)
    
    mutual_follows_count = Connection.objects.filter(
        following=user,
        follower_id__in=following_ids,
        status=Connection.FOLLOWING
    ).count()
    
    network, created = UserNetwork.objects.get_or_create(user=user)
    network.followers_count = followers_count
    network.following_count = following_count
    network.mutual_follows_count = mutual_follows_count
    
    # Calculate influence and connectivity scores
    network.influence_score = calculate_influence_score(user)
    network.connectivity_score = calculate_connectivity_score(user)
    
    network.save()


def calculate_influence_score(user):
    """Calculate user's influence score"""
    followers_count = Connection.objects.filter(
        following=user,
        status=Connection.FOLLOWING
    ).count()
    
    # Simple influence calculation based on followers and engagement
    # This could be enhanced with more sophisticated metrics
    base_score = min(followers_count / 1000.0, 1.0)  # Normalize to 0-1
    
    # Add engagement factor
    recent_activities = UserActivity.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    engagement_factor = min(recent_activities / 100.0, 0.3)  # Max 0.3 boost
    
    return min(base_score + engagement_factor, 1.0)


def calculate_connectivity_score(user):
    """Calculate user's connectivity score"""
    following_count = Connection.objects.filter(
        follower=user,
        status=Connection.FOLLOWING
    ).count()
    
    followers_count = Connection.objects.filter(
        following=user,
        status=Connection.FOLLOWING
    ).count()
    
    # Connectivity based on follow ratio and network depth
    if following_count == 0:
        return 0.0
    
    follow_ratio = followers_count / following_count
    ratio_score = min(follow_ratio, 2.0) / 2.0  # Normalize to 0-1
    
    # Network depth factor (placeholder for more complex calculation)
    depth_factor = 0.5  # This would be calculated based on network analysis
    
    return (ratio_score + depth_factor) / 2.0


def calculate_profile_similarity(profile1, profile2):
    """Calculate similarity between two neural profiles"""
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
    """Get reason for profile match"""
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


def get_common_categories(profile1, profile2):
    """Get common categories between profiles"""
    categories1 = profile1.category_scores
    categories2 = profile2.category_scores
    
    common_categories = set(categories1.keys()) & set(categories2.keys())
    
    return [
        {
            'name': cat,
            'score1': categories1[cat],
            'score2': categories2[cat],
            'average': (categories1[cat] + categories2[cat]) / 2
        }
        for cat in common_categories
    ]
