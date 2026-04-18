from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, F, Sum, Avg
from django.utils.timesince import timesince
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Story, StoryView, StoryLike, StoryReply, StoryShare, 
    StoryHighlight, StoryMention, StoryAnalytics
)
from .serializers import (
    StorySerializer, StoryViewSerializer, StoryLikeSerializer,
    StoryReplySerializer, StoryShareSerializer, StoryHighlightSerializer,
    StoryMentionSerializer, StoryAnalyticsSerializer, CreateStorySerializer,
    StoryReplyCreateSerializer, StoryShareCreateSerializer
)
from users.models import User, UserActivity
from social.models import Notification


class StoryListView(generics.ListAPIView):
    """
    Get active stories from users that the current user follows
    """
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get users that current user follows
        following_users = User.objects.filter(
            followers__follower=user,
            followers__is_active=True
        )
        
        # Get active stories from following users and current user
        queryset = Story.objects.filter(
            Q(user__in=following_users) | Q(user=user),
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        ).select_related('user').prefetch_related(
            'story_likes', 'views', 'replies'
        ).order_by('-created_at')
        
        return queryset


class UserStoryListView(generics.ListAPIView):
    """
    Get stories for a specific user
    """
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Story.objects.filter(
            user_id=user_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        ).select_related('user').prefetch_related(
            'story_likes', 'views', 'replies'
        ).order_by('-created_at')


class StoryDetailView(generics.RetrieveAPIView):
    """
    Get detailed story information
    """
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Story.objects.filter(
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        ).select_related('user').prefetch_related(
            'story_likes', 'views', 'replies', 'story_mentions'
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_story(request):
    """
    Create a new story
    """
    serializer = CreateStorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    content_type = serializer.validated_data['content_type']
    media_file = serializer.validated_data.get('media_file')
    text_content = serializer.validated_data.get('text_content')
    caption = serializer.validated_data.get('caption', '')
    hashtags = serializer.validated_data.get('hashtags', '')
    mentions = serializer.validated_data.get('mentions', '')
    background_color = serializer.validated_data.get('background_color', '#000000')
    text_color = serializer.validated_data.get('text_color', '#FFFFFF')
    
    # Create story
    story = Story.objects.create(
        user=user,
        content_type=content_type,
        media_file=media_file,
        text_content=text_content,
        caption=caption,
        hashtags=hashtags,
        mentions=mentions,
        background_color=background_color,
        text_color=text_color,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    
    # Process mentions
    if mentions:
        mentioned_usernames = [username.strip() for username in mentions.split(',') if username.strip()]
        for username in mentioned_usernames:
            try:
                mentioned_user = User.objects.get(username=username)
                StoryMention.objects.create(
                    story=story,
                    mentioned_user=mentioned_user
                )
                
                # Create notification for mentioned user
                Notification.objects.create(
                    recipient=mentioned_user,
                    sender=user,
                    notification_type='mention',
                    content_type='story',
                    content_id=str(story.id),
                    message=f"{user.username} mentioned you in their story"
                )
                
                # Send WebSocket notification
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'user_{mentioned_user.id}',
                    {
                        'type': 'story_mention',
                        'story_id': str(story.id),
                        'sender_id': str(user.id),
                        'sender_username': user.username,
                        'timestamp': story.created_at.isoformat()
                    }
                )
            except User.DoesNotExist:
                continue
    
    # Log activity
    UserActivity.objects.create(
        user=user,
        activity_type='story',
        metadata={
            'story_id': str(story.id),
            'content_type': content_type,
            'caption': caption[:100]
        }
    )
    
    # Send WebSocket notification to followers
    followers = User.objects.filter(following__following=user, following__is_active=True)
    for follower in followers:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{follower.id}',
            {
                'type': 'new_story',
                'story_id': str(story.id),
                'user_id': str(user.id),
                'username': user.username,
                'content_type': content_type,
                'timestamp': story.created_at.isoformat()
            }
        )
    
    return Response({
        'story': StorySerializer(story).data,
        'message': 'Story created successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def view_story(request, story_id):
    """
    Record a story view
    """
    user = request.user
    
    try:
        story = Story.objects.get(
            id=story_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or expired'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create or update view record
    story_view, created = StoryView.objects.get_or_create(
        story=story,
        viewer=user,
        defaults={'view_duration': 0}
    )
    
    if not created:
        # Update view duration if needed
        story_view.viewed_at = timezone.now()
        story_view.save()
    
    # Update story view count
    Story.objects.filter(id=story_id).update(view_count=F('view_count') + 1)
    
    # Send WebSocket notification to story owner
    if story.user != user:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{story.user.id}',
            {
                'type': 'story_viewed',
                'story_id': str(story.id),
                'viewer_id': str(user.id),
                'viewer_username': user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    return Response({
        'status': 'view recorded',
        'view_count': story.view_count + 1
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_story(request, story_id):
    """
    Like or unlike a story
    """
    user = request.user
    
    try:
        story = Story.objects.get(
            id=story_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or expired'}, status=status.HTTP_404_NOT_FOUND)
    
    # Toggle like
    story_like, created = StoryLike.objects.get_or_create(
        story=story,
        user=user
    )
    
    if not created:
        # Unlike
        story_like.delete()
        Story.objects.filter(id=story_id).update(likes_count=F('likes_count') - 1)
        like_count = story.likes_count - 1
        is_liked = False
    else:
        # Like
        Story.objects.filter(id=story_id).update(likes_count=F('likes_count') + 1)
        like_count = story.likes_count + 1
        is_liked = True
        
        # Create notification for story owner
        if story.user != user:
            Notification.objects.create(
                recipient=story.user,
                sender=user,
                notification_type='like',
                content_type='story',
                content_id=str(story.id),
                message=f"{user.username} liked your story"
            )
            
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{story.user.id}',
                {
                    'type': 'story_liked',
                    'story_id': str(story.id),
                    'liker_id': str(user.id),
                    'liker_username': user.username,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    return Response({
        'status': 'unliked' if not is_liked else 'liked',
        'like_count': like_count,
        'is_liked': is_liked
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_story_viewers(request, story_id):
    """
    Get list of story viewers
    """
    user = request.user
    
    try:
        story = Story.objects.get(
            id=story_id,
            user=user,  # Only story owner can see viewers
            is_active=True
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get viewers with view times
    viewers = StoryView.objects.filter(
        story=story
    ).select_related('viewer').order_by('-viewed_at')
    
    serializer = StoryViewSerializer(viewers, many=True)
    
    return Response({
        'viewers': serializer.data,
        'total_views': story.view_count,
        'unique_viewers': viewers.count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reply_to_story(request, story_id):
    """
    Reply to a story
    """
    user = request.user
    serializer = StoryReplyCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        story = Story.objects.get(
            id=story_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or expired'}, status=status.HTTP_404_NOT_FOUND)
    
    content = serializer.validated_data['content']
    parent_id = serializer.validated_data.get('parent_id')
    
    # Create reply
    reply = StoryReply.objects.create(
        story=story,
        user=user,
        content=content,
        parent_id=parent_id
    )
    
    # Update story replies count
    Story.objects.filter(id=story_id).update(replies_count=F('replies_count') + 1)
    
    # Create notification for story owner
    if story.user != user:
        Notification.objects.create(
            recipient=story.user,
            sender=user,
            notification_type='story_reply',
            content_type='story',
            content_id=str(story.id),
            message=f"{user.username} replied to your story: {content[:50]}..."
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{story.user.id}',
            {
                'type': 'story_replied',
                'story_id': str(story.id),
                'replier_id': str(user.id),
                'replier_username': user.username,
                'reply_id': str(reply.id),
                'content': content,
                'timestamp': reply.created_at.isoformat()
            }
        )
    
    return Response({
        'reply': StoryReplySerializer(reply).data,
        'message': 'Reply posted successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_story_replies(request, story_id):
    """
    Get replies for a story
    """
    try:
        story = Story.objects.get(
            id=story_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or expired'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get replies
    replies = StoryReply.objects.filter(
        story=story,
        is_deleted=False,
        parent=None  # Only top-level replies
    ).select_related('user').prefetch_related('thread_replies').order_by('created_at')
    
    serializer = StoryReplySerializer(replies, many=True)
    
    return Response({
        'replies': serializer.data,
        'total_replies': story.replies_count
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def share_story(request, story_id):
    """
    Share a story
    """
    user = request.user
    serializer = StoryShareCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        story = Story.objects.get(
            id=story_id,
            is_active=True,
            is_expired=False,
            expires_at__gt=timezone.now()
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or expired'}, status=status.HTTP_404_NOT_FOUND)
    
    share_type = serializer.validated_data['share_type']
    shared_to = serializer.validated_data.get('shared_to')
    caption = serializer.validated_data.get('caption', '')
    
    # Create share record
    share = StoryShare.objects.create(
        story=story,
        user=user,
        share_type=share_type,
        shared_to=shared_to,
        caption=caption
    )
    
    # Update story shares count
    Story.objects.filter(id=story_id).update(shares_count=F('shares_count') + 1)
    
    # Create notification for story owner
    if story.user != user:
        Notification.objects.create(
            recipient=story.user,
            sender=user,
            notification_type='share',
            content_type='story',
            content_id=str(story.id),
            message=f"{user.username} shared your story"
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{story.user.id}',
            {
                'type': 'story_shared',
                'story_id': str(story.id),
                'sharer_id': str(user.id),
                'sharer_username': user.username,
                'share_type': share_type,
                'timestamp': share.created_at.isoformat()
            }
        )
    
    return Response({
        'share': StoryShareSerializer(share).data,
        'message': 'Story shared successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_highlights(request, user_id):
    """
    Get user's story highlights
    """
    highlights = StoryHighlight.objects.filter(
        user_id=user_id,
        is_active=True,
        is_archived=False
    ).select_related('cover_story').prefetch_related('stories').order_by('-created_at')
    
    serializer = StoryHighlightSerializer(highlights, many=True)
    
    return Response({
        'highlights': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_highlight(request):
    """
    Create a new story highlight
    """
    user = request.user
    title = request.data.get('title')
    story_ids = request.data.get('story_ids', [])
    cover_story_id = request.data.get('cover_story_id')
    
    if not title:
        return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create highlight
    highlight = StoryHighlight.objects.create(
        user=user,
        title=title
    )
    
    # Add stories to highlight
    if story_ids:
        stories = Story.objects.filter(
            id__in=story_ids,
            user=user,
            is_active=True
        )
        highlight.stories.add(stories)
    
    # Set cover story
    if cover_story_id:
        try:
            cover_story = Story.objects.get(id=cover_story_id, user=user)
            highlight.cover_story = cover_story
            highlight.save()
        except Story.DoesNotExist:
            pass
    
    return Response({
        'highlight': StoryHighlightSerializer(highlight).data,
        'message': 'Highlight created successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_story_analytics(request, story_id):
    """
    Get analytics for a story (story owner only)
    """
    user = request.user
    
    try:
        story = Story.objects.get(
            id=story_id,
            user=user,  # Only story owner can see analytics
            is_active=True
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get analytics data
    analytics = StoryAnalytics.objects.filter(
        story=story
    ).order_by('-date')
    
    # Get basic stats
    total_views = story.view_count
    unique_viewers = StoryView.objects.filter(story=story).count()
    total_likes = story.likes_count
    total_shares = story.shares_count
    total_replies = story.replies_count
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_views > 0:
        engagement_rate = ((total_likes + total_shares + total_replies) / total_views) * 100
    
    return Response({
        'basic_stats': {
            'total_views': total_views,
            'unique_viewers': unique_viewers,
            'total_likes': total_likes,
            'total_shares': total_shares,
            'total_replies': total_replies,
            'engagement_rate': round(engagement_rate, 2)
        },
        'daily_analytics': StoryAnalyticsSerializer(analytics, many=True).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_story(request, story_id):
    """
    Delete a story (story owner only)
    """
    user = request.user
    
    try:
        story = Story.objects.get(
            id=story_id,
            user=user,  # Only story owner can delete
            is_active=True
        )
    except Story.DoesNotExist:
        return Response({'error': 'Story not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    # Soft delete
    story.is_active = False
    story.is_archived = True
    story.save()
    
    return Response({
        'message': 'Story deleted successfully'
    })
