from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, F, Avg, Sum
from django.db.models.functions import Trunc
from django.core.files.storage import default_storage
from django.conf import settings
import random

from .models import (
    Reel, ReelInteraction, ReelComment, ReelHashtag, ReelMusic,
    ReelAnalytics, ReelRecommendation, ReelChallenge, ReelChallengeEntry,
    ReelForward
)
from .serializers import (
    ReelSerializer, ReelInteractionSerializer, ReelCommentSerializer,
    ReelHashtagSerializer, ReelMusicSerializer, ReelAnalyticsSerializer,
    ReelRecommendationSerializer, ReelChallengeSerializer, ReelChallengeEntrySerializer,
    CreateReelSerializer, ReelInteractionSerializer as ReelActionSerializer,
    ReelCommentCreateSerializer, ReelSearchSerializer, TrendingReelsSerializer
)
from users.models import UserActivity
from neural.models import UserInteraction


class ReelListView(generics.ListCreateAPIView):
    serializer_class = ReelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Reel.objects.filter(is_private=False).select_related('creator').prefetch_related('interactions')
        
        # Filter by user if requested
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(creator_id=user_id)
        
        # Filter by hashtags if requested
        hashtags = self.request.query_params.getlist('hashtags')
        if hashtags:
            queryset = queryset.filter(hashtags__contains=hashtags)
        
        # Sort by
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        sort_order = self.request.query_params.get('sort_order', 'desc')
        
        if sort_by == 'view_count':
            queryset = queryset.order_by(F('view_count').desc() if sort_order == 'desc' else 'view_count')
        elif sort_by == 'like_count':
            queryset = queryset.order_by(F('like_count').desc() if sort_order == 'desc' else 'like_count')
        elif sort_by == 'comment_count':
            queryset = queryset.order_by(F('comment_count').desc() if sort_order == 'desc' else 'comment_count')
        else:
            queryset = queryset.order_by(F('created_at').desc() if sort_order == 'desc' else 'created_at')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateReelSerializer
        return ReelSerializer


class ReelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Reel.objects.select_related('creator').prefetch_related('interactions')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        Reel.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        
        # Log view interaction
        ReelInteraction.objects.get_or_create(
            reel=instance,
            user=request.user,
            interaction_type=ReelInteraction.VIEW,
            defaults={'timestamp': timezone.now()}
        )
        
        # Update neural interaction tracking
        UserInteraction.objects.get_or_create(
            user=request.user,
            interaction_type='view',
            content_type='reel',
            content_id=str(instance.id),
            defaults={'timestamp': timezone.now()}
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def interact_with_reel(request):
    """Handle user interactions with reels (like, comment, share, save, duet)"""
    serializer = ReelActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    reel_id = serializer.validated_data['reel_id']
    interaction_type = serializer.validated_data['interaction_type']
    metadata = serializer.validated_data.get('metadata', {})
    
    try:
        reel = Reel.objects.get(id=reel_id)
    except Reel.DoesNotExist:
        return Response({'error': 'Reel not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user can interact
    if reel.is_private and reel.creator != request.user:
        return Response({'error': 'Cannot interact with private reel'}, status=status.HTTP_403_FORBIDDEN)
    
    # Create or update interaction
    interaction, created = ReelInteraction.objects.get_or_create(
        reel=reel,
        user=request.user,
        interaction_type=interaction_type,
        defaults={'metadata': metadata, 'timestamp': timezone.now()}
    )
    
    if not created:
        # For like/save, toggle the interaction
        if interaction_type in [ReelInteraction.LIKE, ReelInteraction.SAVE]:
            interaction.delete()
            return Response({'status': 'removed', 'interaction_type': interaction_type})
        else:
            # Update metadata for other interactions
            interaction.metadata = metadata
            interaction.save()
    
    # Update reel counts
    if interaction_type == ReelInteraction.LIKE:
        Reel.objects.filter(id=reel_id).update(like_count=F('like_count') + 1)
    elif interaction_type == ReelInteraction.COMMENT:
        Reel.objects.filter(id=reel_id).update(comment_count=F('comment_count') + 1)
    elif interaction_type == ReelInteraction.SHARE:
        Reel.objects.filter(id=reel_id).update(share_count=F('share_count') + 1)
    
    # Log user activity
    UserActivity.objects.create(
        user=request.user,
        activity_type=interaction_type.lower(),
        metadata={
            'reel_id': str(reel_id),
            'interaction_type': interaction_type
        }
    )
    
    # Update neural interaction tracking
    UserInteraction.objects.update_or_create(
        user=request.user,
        interaction_type=interaction_type.lower(),
        content_type='reel',
        content_id=str(reel_id),
        defaults={'timestamp': timezone.now()}
    )
    
    return Response({
        'status': 'success',
        'interaction_type': interaction_type,
        'created': created
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_reel_comments(request, reel_id):
    """Get comments for a specific reel"""
    try:
        reel = Reel.objects.get(id=reel_id)
    except Reel.DoesNotExist:
        return Response({'error': 'Reel not found'}, status=status.HTTP_404_NOT_FOUND)
    
    comments = reel.comments.filter(parent=None, is_deleted=False).order_by('created_at')
    serializer = ReelCommentSerializer(comments, many=True, context={'request': request})
    
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_reel_comment(request):
    """Create a comment on a reel"""
    serializer = ReelCommentCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    comment = serializer.save()
    
    # Update reel comment count
    Reel.objects.filter(id=comment.reel.id).update(comment_count=F('comment_count') + 1)
    
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='comment',
        target_user=comment.reel.creator,
        metadata={
            'reel_id': str(comment.reel.id),
            'comment_id': str(comment.id)
        }
    )
    
    return Response(ReelCommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_reels(request):
    """Search reels based on various criteria"""
    serializer = ReelSearchSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    
    query = serializer.validated_data.get('query', '')
    hashtags = serializer.validated_data.get('hashtags', [])
    music_track = serializer.validated_data.get('music_track', '')
    min_duration = serializer.validated_data.get('min_duration')
    max_duration = serializer.validated_data.get('max_duration')
    sort_by = serializer.validated_data['sort_by']
    sort_order = serializer.validated_data['sort_order']
    
    # Build queryset
    queryset = Reel.objects.filter(is_private=False).select_related('creator')
    
    # Text search in caption
    if query:
        queryset = queryset.filter(caption__icontains=query)
    
    # Hashtag filter
    if hashtags:
        for hashtag in hashtags:
            queryset = queryset.filter(hashtags__contains=[hashtag])
    
    # Music track filter
    if music_track:
        queryset = queryset.filter(music_track__icontains=music_track)
    
    # Duration filter
    if min_duration is not None:
        queryset = queryset.filter(duration__gte=min_duration)
    if max_duration is not None:
        queryset = queryset.filter(duration__lte=max_duration)
    
    # Sorting
    if sort_by == 'view_count':
        queryset = queryset.order_by(F('view_count').desc() if sort_order == 'desc' else 'view_count')
    elif sort_by == 'like_count':
        queryset = queryset.order_by(F('like_count').desc() if sort_order == 'desc' else 'like_count')
    elif sort_by == 'comment_count':
        queryset = queryset.order_by(F('comment_count').desc() if sort_order == 'desc' else 'comment_count')
    else:
        queryset = queryset.order_by(F('created_at').desc() if sort_order == 'desc' else 'created_at')
    
    # Limit results
    queryset = queryset[:50]
    
    serializer = ReelSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_trending_reels(request):
    """Get trending reels based on engagement and views"""
    serializer = TrendingReelsSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    
    time_range = serializer.validated_data['time_range']
    limit = serializer.validated_data['limit']
    
    # Calculate time threshold
    if time_range == 'hour':
        time_threshold = timezone.now() - timedelta(hours=1)
    elif time_range == 'day':
        time_threshold = timezone.now() - timedelta(days=1)
    elif time_range == 'week':
        time_threshold = timezone.now() - timedelta(weeks=1)
    else:  # month
        time_threshold = timezone.now() - timedelta(days=30)
    
    # Get trending reels based on recent engagement
    queryset = Reel.objects.filter(
        is_private=False,
        created_at__gte=time_threshold
    ).annotate(
        engagement_rate=(F('like_count') + F('comment_count') + F('share_count')) / F('view_count')
    ).filter(
        view_count__gt=0
    ).order_by('-engagement_rate', '-view_count')[:limit]
    
    serializer = ReelSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_reel_recommendations(request):
    """Get personalized reel recommendations"""
    user = request.user
    
    # Get user's recent interactions
    recent_interactions = ReelInteraction.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).select_related('reel')
    
    if not recent_interactions.exists():
        # If no interactions, return popular reels
        popular_reels = Reel.objects.filter(
            is_private=False
        ).order_by('-view_count', '-like_count')[:20]
        
        serializer = ReelSerializer(popular_reels, many=True, context={'request': request})
        return Response(serializer.data)
    
    # Analyze user preferences
    liked_hashtags = []
    liked_music = []
    
    for interaction in recent_interactions:
        if interaction.interaction_type == ReelInteraction.LIKE:
            liked_hashtags.extend(interaction.reel.hashtags)
            if interaction.reel.music_track:
                liked_music.append(interaction.reel.music_track)
    
    # Get recommendations based on preferences
    queryset = Reel.objects.filter(is_private=False).exclude(
        interactions__user=user,
        interactions__interaction_type=ReelInteraction.VIEW
    )
    
    # Filter by hashtags
    if liked_hashtags:
        queryset = queryset.filter(hashtags__overlap=liked_hashtags[:10])
    
    # Filter by music
    if liked_music:
        queryset = queryset.filter(music_track__in=liked_music[:5])
    
    # Order by engagement and randomness
    queryset = queryset.order_by('-view_count', '?')[:20]
    
    serializer = ReelSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_reel_analytics(request):
    """Get analytics data for user's reels"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get or create analytics records
    analytics = ReelAnalytics.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('-date')
    
    # If no analytics data, calculate on the fly
    if not analytics.exists():
        reels = Reel.objects.filter(creator=user, created_at__gte=start_date)
        
        daily_data = {}
        for reel in reels:
            reel_date = reel.created_at.date()
            if reel_date not in daily_data:
                daily_data[reel_date] = {
                    'reels_created': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'total_shares': 0
                }
            
            daily_data[reel_date]['reels_created'] += 1
            daily_data[reel_date]['total_views'] += reel.view_count
            daily_data[reel_date]['total_likes'] += reel.like_count
            daily_data[reel_date]['total_comments'] += reel.comment_count
            daily_data[reel_date]['total_shares'] += reel.share_count
        
        # Convert to response format
        analytics_data = []
        for date, data in sorted(daily_data.items()):
            total_interactions = data['total_likes'] + data['total_comments'] + data['total_shares']
            engagement_rate = (total_interactions / max(data['total_views'], 1)) * 100
            
            analytics_data.append({
                'date': date,
                'reels_created': data['reels_created'],
                'total_views': data['total_views'],
                'total_likes': data['total_likes'],
                'total_comments': data['total_comments'],
                'total_shares': data['total_shares'],
                'engagement_rate': round(engagement_rate, 2),
                'reach': data['total_views'],  # Simplified reach calculation
                'impressions': data['total_views'] * 2  # Estimated impressions
            })
        
        return Response(analytics_data)
    
    serializer = ReelAnalyticsSerializer(analytics, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_trending_hashtags(request):
    """Get trending hashtags"""
    time_range = request.query_params.get('time_range', 'day')
    limit = int(request.query_params.get('limit', 20))
    
    # Calculate time threshold
    if time_range == 'hour':
        time_threshold = timezone.now() - timedelta(hours=1)
    elif time_range == 'day':
        time_threshold = timezone.now() - timedelta(days=1)
    elif time_range == 'week':
        time_threshold = timezone.now() - timedelta(weeks=1)
    else:  # month
        time_threshold = timezone.now() - timedelta(days=30)
    
    # Get trending hashtags
    trending = Reel.objects.filter(
        created_at__gte=time_threshold,
        hashtags__len__gt=0
    ).annotate(
        hashtag_count=Count('hashtags')
    ).values('hashtags').annotate(
        usage_count=Count('id'),
        unique_users=Count('creator', distinct=True)
    ).order_by('-usage_count', '-unique_users')[:limit]
    
    # Flatten hashtags and calculate trends
    hashtag_trends = {}
    for item in trending:
        for hashtag in item['hashtags']:
            if hashtag not in hashtag_trends:
                hashtag_trends[hashtag] = {
                    'hashtag': hashtag,
                    'usage_count': 0,
                    'unique_users': set()
                }
            hashtag_trends[hashtag]['usage_count'] += item['usage_count']
            hashtag_trends[hashtag]['unique_users'].update(
                Reel.objects.filter(
                    hashtags__contains=[hashtag],
                    created_at__gte=time_threshold
                ).values_list('creator_id', flat=True)
            )
    
    # Convert to list and sort
    result = []
    for hashtag, data in hashtag_trends.items():
        result.append({
            'hashtag': hashtag,
            'usage_count': data['usage_count'],
            'unique_users': len(data['unique_users'])
        })
    
    result.sort(key=lambda x: (x['usage_count'], x['unique_users']), reverse=True)
    
    return Response(result[:limit])


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_challenges(request):
    """Get active reel challenges"""
    challenges = ReelChallenge.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).order_by('-created_at')
    
    serializer = ReelChallengeSerializer(challenges, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enter_challenge(request, challenge_id):
    """Enter a reel into a challenge"""
    try:
        challenge = ReelChallenge.objects.get(id=challenge_id, is_active=True)
    except ReelChallenge.DoesNotExist:
        return Response({'error': 'Challenge not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reel_id = request.data.get('reel_id')
    
    try:
        reel = Reel.objects.get(id=reel_id, creator=request.user)
    except Reel.DoesNotExist:
        return Response({'error': 'Reel not found or not owned by user'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already entered
    if ReelChallengeEntry.objects.filter(challenge=challenge, reel=reel).exists():
        return Response({'error': 'Reel already entered in this challenge'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create entry
    entry = ReelChallengeEntry.objects.create(
        challenge=challenge,
        reel=reel,
        user=request.user
    )
    
    # Update challenge participant count
    ReelChallenge.objects.filter(id=challenge_id).update(
        participant_count=F('participant_count') + 1
    )
    
    serializer = ReelChallengeEntrySerializer(entry)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def forward_reel(request):
    """Forward a reel to one or more users"""
    reel_id = request.data.get('reel_id')
    recipient_ids = request.data.get('recipient_ids', [])
    message = request.data.get('message', '')
    
    if not reel_id:
        return Response({'error': 'Reel ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not recipient_ids:
        return Response({'error': 'At least one recipient is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reel = Reel.objects.get(id=reel_id)
    except Reel.DoesNotExist:
        return Response({'error': 'Reel not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user can forward this reel
    if reel.is_private and reel.creator != request.user:
        return Response({'error': 'Cannot forward private reel'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get recipients
    recipients = User.objects.filter(id__in=recipient_ids, is_active=True)
    
    if len(recipients) != len(recipient_ids):
        return Response({'error': 'One or more recipients not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create forwards
    forwards = []
    for recipient in recipients:
        # Check if already forwarded
        if ReelForward.objects.filter(reel=reel, sender=request.user, recipient=recipient).exists():
            continue
        
        forward = ReelForward.objects.create(
            reel=reel,
            sender=request.user,
            recipient=recipient,
            message=message
        )
        forwards.append(forward)
        
        # Update reel share count
        Reel.objects.filter(id=reel_id).update(share_count=F('share_count') + 1)
        
        # Create notification for recipient
        from social.models import Notification
        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type='reel_forward',
            content_type='reel',
            content_id=str(reel.id),
            message=f"{request.user.username} sent you a reel: {reel.caption[:50]}..."
        )
        
        # Send WebSocket notification
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{recipient.id}',
            {
                'type': 'reel_forwarded',
                'reel_id': str(reel.id),
                'sender_id': str(request.user.id),
                'sender_username': request.user.username,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='forward_reel',
        metadata={
            'reel_id': str(reel.id),
            'recipient_count': len(forwards),
            'message': message[:100]
        }
    )
    
    return Response({
        'status': 'success',
        'forwarded_count': len(forwards),
        'message': f'Reel forwarded to {len(forwards)} users'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_forwardable_users(request):
    """Get list of users that can receive forwarded reels"""
    user = request.user
    reel_id = request.query_params.get('reel_id')
    
    # Get users that current user follows, users that follow current user, and users in inbox
    following = User.objects.filter(followers__follower=user, is_active=True)
    followers = User.objects.filter(following__following=user, is_active=True)
    
    # Get users from chat rooms (inbox users)
    from chat.models import ChatRoom, ChatParticipant
    chat_users = User.objects.filter(
        chatparticipant__room__participants__user=user,
        is_active=True
    ).distinct()
    
    # Combine all users and remove duplicates
    all_users = (following | followers | chat_users).distinct()
    
    # Remove current user
    all_users = all_users.exclude(id=user.id)
    
    # If reel_id is provided, check if user can forward this reel
    if reel_id:
        try:
            reel = Reel.objects.get(id=reel_id)
            if reel.is_private and reel.creator != user:
                # For private reels, only allow forwarding to creator
                all_users = all_users.filter(id=reel.creator.id)
        except Reel.DoesNotExist:
            return Response({'error': 'Reel not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Serialize users
    from users.serializers import UserSerializer
    serializer = UserSerializer(all_users, many=True)
    
    return Response({
        'users': serializer.data,
        'total_count': all_users.count()
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_received_forwards(request):
    """Get reels that have been forwarded to the current user"""
    user = request.user
    
    forwards = ReelForward.objects.filter(
        recipient=user
    ).select_related(
        'reel', 'sender', 'reel__creator'
    ).order_by('-created_at')
    
    # Serialize forwards
    forward_data = []
    for forward in forwards:
        forward_data.append({
            'id': str(forward.id),
            'reel': {
                'id': str(forward.reel.id),
                'creator': {
                    'id': str(forward.reel.creator.id),
                    'username': forward.reel.creator.username,
                    'first_name': forward.reel.creator.first_name,
                    'last_name': forward.reel.creator.last_name
                },
                'caption': forward.reel.caption,
                'video_file': forward.reel.video_file.url if forward.reel.video_file else None,
                'thumbnail': forward.reel.thumbnail.url if forward.reel.thumbnail else None,
                'duration': forward.reel.duration,
                'view_count': forward.reel.view_count,
                'like_count': forward.reel.like_count,
                'comment_count': forward.reel.comment_count,
                'created_at': forward.reel.created_at
            },
            'sender': {
                'id': str(forward.sender.id),
                'username': forward.sender.username,
                'first_name': forward.sender.first_name,
                'last_name': forward.sender.last_name
            },
            'message': forward.message,
            'is_saved': forward.is_saved,
            'created_at': forward.created_at,
            'saved_at': forward.saved_at
        })
    
    return Response({
        'forwards': forward_data,
        'total_count': forwards.count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_forwarded_reel(request, forward_id):
    """Mark a forwarded reel as saved"""
    user = request.user
    
    try:
        forward = ReelForward.objects.get(id=forward_id, recipient=user)
    except ReelForward.DoesNotExist:
        return Response({'error': 'Forward not found'}, status=status.HTTP_404_NOT_FOUND)
    
    forward.mark_as_saved()
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='save_forwarded_reel',
        metadata={
            'forward_id': str(forward.id),
            'reel_id': str(forward.reel.id)
        }
    )
    
    return Response({
        'status': 'success',
        'message': 'Reel saved successfully',
        'is_saved': True,
        'saved_at': forward.saved_at
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unsave_forwarded_reel(request, forward_id):
    """Unsave a forwarded reel"""
    user = request.user
    
    try:
        forward = ReelForward.objects.get(id=forward_id, recipient=user)
    except ReelForward.DoesNotExist:
        return Response({'error': 'Forward not found'}, status=status.HTTP_404_NOT_FOUND)
    
    forward.is_saved = False
    forward.saved_at = None
    forward.save()
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='unsave_forwarded_reel',
        metadata={
            'forward_id': str(forward.id),
            'reel_id': str(forward.reel.id)
        }
    )
    
    return Response({
        'status': 'success',
        'message': 'Reel unsaved successfully',
        'is_saved': False
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_saved_forwards(request):
    """Get saved forwarded reels"""
    user = request.user
    
    forwards = ReelForward.objects.filter(
        recipient=user,
        is_saved=True
    ).select_related(
        'reel', 'sender', 'reel__creator'
    ).order_by('-saved_at')
    
    # Serialize forwards
    forward_data = []
    for forward in forwards:
        forward_data.append({
            'id': str(forward.id),
            'reel': {
                'id': str(forward.reel.id),
                'creator': {
                    'id': str(forward.reel.creator.id),
                    'username': forward.reel.creator.username,
                    'first_name': forward.reel.creator.first_name,
                    'last_name': forward.reel.creator.last_name
                },
                'caption': forward.reel.caption,
                'video_file': forward.reel.video_file.url if forward.reel.video_file else None,
                'thumbnail': forward.reel.thumbnail.url if forward.reel.thumbnail else None,
                'duration': forward.reel.duration,
                'view_count': forward.reel.view_count,
                'like_count': forward.reel.like_count,
                'comment_count': forward.reel.comment_count,
                'created_at': forward.reel.created_at
            },
            'sender': {
                'id': str(forward.sender.id),
                'username': forward.sender.username,
                'first_name': forward.sender.first_name,
                'last_name': forward.sender.last_name
            },
            'message': forward.message,
            'saved_at': forward.saved_at
        })
    
    return Response({
        'forwards': forward_data,
        'total_count': forwards.count()
    })
