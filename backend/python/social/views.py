from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import (
    Follow, UserProfile, Like, Share, FollowRequest, 
    UserActivity, Notification
)
from .serializers import (
    UserProfileSerializer, FollowSerializer, LikeSerializer,
    ShareSerializer, FollowRequestSerializer, NotificationSerializer,
    UserActivitySerializer
)
from .utils import update_user_stats, send_social_notification
from .permissions import CanFollowUser, CanViewPrivateProfile


class SocialPagination(PageNumberPagination):
    """Custom pagination for social data"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    """
    Get user profile with social stats
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(UserProfile, user=target_user)
        
        # Check if profile is private and user is not following
        if profile.is_private:
            if target_user != request.user:
                is_following = Follow.objects.filter(
                    follower=request.user,
                    following=target_user
                ).exists()
                if not is_following:
                    return Response({
                        'error': 'Private profile - follow to see content'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Get profile data
        serializer = UserProfileSerializer(profile)
        data = serializer.data
        
        # Add follow status
        if target_user != request.user:
            data['is_following'] = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            
            # Check if follow request exists
            data['follow_request_sent'] = FollowRequest.objects.filter(
                requester=request.user,
                target=target_user,
                status='pending'
            ).exists()
        else:
            data['is_following'] = None
            data['follow_request_sent'] = None
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get user profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanFollowUser])
def follow_user(request, user_id):
    """
    Follow a user
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user == request.user:
            return Response({
                'error': 'Cannot follow yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already following
        if Follow.objects.filter(follower=request.user, following=target_user).exists():
            return Response({
                'error': 'Already following this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        target_profile = get_object_or_404(UserProfile, user=target_user)
        
        with transaction.atomic():
            if target_profile.is_private and target_profile.allow_follow_requests:
                # Create follow request for private accounts
                follow_request = FollowRequest.objects.create(
                    requester=request.user,
                    target=target_user,
                    message=request.data.get('message', '')
                )
                
                # Send notification
                Notification.objects.create(
                    recipient=target_user,
                    sender=request.user,
                    notification_type='follow_request',
                    message=f"{request.user.username} wants to follow you"
                )
                
                return Response({
                    'message': 'Follow request sent',
                    'request_id': follow_request.id
                }, status=status.HTTP_201_CREATED)
            else:
                # Direct follow for public accounts
                follow = Follow.objects.create(
                    follower=request.user,
                    following=target_user
                )
                
                # Update stats
                target_profile.update_follow_counts()
                request.user.social_profile.update_follow_counts()
                
                # Send notification
                Notification.objects.create(
                    recipient=target_user,
                    sender=request.user,
                    notification_type='follow',
                    message=f"{request.user.username} started following you"
                )
                
                # Send real-time update
                send_social_notification.delay(
                    recipient_id=target_user.id,
                    notification_type='follow',
                    sender_id=request.user.id,
                    sender_username=request.user.username
                )
                
                return Response({
                    'message': 'User followed successfully',
                    'followers_count': target_profile.followers_count
                }, status=status.HTTP_201_CREATED)
                
    except Exception as e:
        return Response({
            'error': f'Failed to follow user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    """
    Unfollow a user
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        follow = Follow.objects.filter(
            follower=request.user,
            following=target_user
        ).first()
        
        if not follow:
            return Response({
                'error': 'Not following this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            follow.delete()
            
            # Update stats
            target_user.social_profile.update_follow_counts()
            request.user.social_profile.update_follow_counts()
            
            return Response({
                'message': 'User unfollowed successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': f'Failed to unfollow user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request, user_id):
    """
    Get user's followers
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Check privacy
        target_profile = target_user.social_profile
        if target_profile.is_private and target_user != request.user:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            if not is_following:
                return Response({
                    'error': 'Private profile - follow to see followers'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get followers
        followers = Follow.objects.filter(following=target_user).select_related('follower')
        
        # Paginate
        paginator = SocialPagination()
        page = paginator.paginate_queryset(followers, request)
        
        # Serialize
        from django.contrib.auth.models import User
        follower_data = []
        for follow in page:
            follower_data.append({
                'id': follow.follower.id,
                'username': follow.follower.username,
                'first_name': follow.follower.first_name,
                'last_name': follow.follower.last_name,
                'followed_at': follow.created_at
            })
        
        return paginator.get_paginated_response({
            'results': follower_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to get followers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, user_id):
    """
    Get users that this user follows
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Check privacy
        target_profile = target_user.social_profile
        if target_profile.is_private and target_user != request.user:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            if not is_following:
                return Response({
                    'error': 'Private profile - follow to see following'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get following
        following = Follow.objects.filter(follower=target_user).select_related('following')
        
        # Paginate
        paginator = SocialPagination()
        page = paginator.paginate_queryset(following, request)
        
        # Serialize
        following_data = []
        for follow in page:
            following_data.append({
                'id': follow.following.id,
                'username': follow.following.username,
                'first_name': follow.following.first_name,
                'last_name': follow.following.last_name,
                'followed_at': follow.created_at
            })
        
        return paginator.get_paginated_response({
            'results': following_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to get following: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_content(request):
    """
    Like a post or reel
    """
    try:
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        
        if content_type not in ['post', 'reel']:
            return Response({
                'error': 'Invalid content type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already liked
        if Like.objects.filter(
            user=request.user,
            content_type=content_type,
            content_id=content_id
        ).exists():
            return Response({
                'error': 'Already liked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create like
        like = Like.objects.create(
            user=request.user,
            content_type=content_type,
            content_id=content_id
        )
        
        # Get content owner for notification
        content_owner = None
        if content_type == 'reel':
            from reels.models import Reel
            try:
                reel = Reel.objects.get(id=content_id)
                content_owner = reel.user
            except Reel.DoesNotExist:
                pass
        elif content_type == 'post':
            # Similar for posts
            pass
        
        # Send notification to content owner
        if content_owner and content_owner != request.user:
            Notification.objects.create(
                recipient=content_owner,
                sender=request.user,
                notification_type='like',
                content_type=content_type,
                content_id=content_id,
                message=f"{request.user.username} liked your {content_type}"
            )
            
            # Send real-time update
            send_social_notification.delay(
                recipient_id=content_owner.id,
                notification_type='like',
                sender_id=request.user.id,
                sender_username=request.user.username,
                content_type=content_type,
                content_id=content_id
            )
        
        # Get updated like count
        like_count = Like.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        return Response({
            'message': 'Content liked successfully',
            'like_count': like_count,
            'is_liked': True
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to like content: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unlike_content(request):
    """
    Unlike a post or reel
    """
    try:
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        
        if content_type not in ['post', 'reel']:
            return Response({
                'error': 'Invalid content type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get and delete like
        like = Like.objects.filter(
            user=request.user,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if not like:
            return Response({
                'error': 'Not liked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        like.delete()
        
        # Get updated like count
        like_count = Like.objects.filter(
            content_type=content_type,
            content_id=content_id
        ).count()
        
        return Response({
            'message': 'Content unliked successfully',
            'like_count': like_count,
            'is_liked': False
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to unlike content: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get user's notifications
    """
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        
        # Build queryset
        queryset = Notification.objects.filter(recipient=request.user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Order by creation date
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = SocialPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Serialize
        serializer = NotificationSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get notifications: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    """
    Mark notifications as read
    """
    try:
        notification_ids = request.data.get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            Notification.objects.filter(
                id__in=notification_ids,
                recipient=request.user
            ).update(is_read=True)
        else:
            # Mark all notifications as read
            Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True)
        
        return Response({
            'message': 'Notifications marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to mark notifications as read: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_follow_requests(request):
    """
    Get user's follow requests
    """
    try:
        # Get pending requests
        requests = FollowRequest.objects.filter(
            target=request.user,
            status='pending'
        ).select_related('requester')
        
        # Paginate
        paginator = SocialPagination()
        page = paginator.paginate_queryset(requests, request)
        
        # Serialize
        serializer = FollowRequestSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get follow requests: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_follow_request(request, request_id):
    """
    Accept or decline follow request
    """
    try:
        follow_request = get_object_or_404(
            FollowRequest, 
            id=request_id, 
            target=request.user,
            status='pending'
        )
        
        action = request.data.get('action')  # 'accept' or 'decline'
        
        if action not in ['accept', 'decline']:
            return Response({
                'error': 'Invalid action'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            if action == 'accept':
                # Create follow relationship
                Follow.objects.create(
                    follower=follow_request.requester,
                    following=request.user
                )
                
                # Update stats
                request.user.social_profile.update_follow_counts()
                follow_request.requester.social_profile.update_follow_counts()
                
                # Update request status
                follow_request.status = 'accepted'
                follow_request.save()
                
                # Send notification
                Notification.objects.create(
                    recipient=follow_request.requester,
                    sender=request.user,
                    notification_type='follow',
                    message=f"{request.user.username} accepted your follow request"
                )
                
                return Response({
                    'message': 'Follow request accepted'
                }, status=status.HTTP_200_OK)
                
            else:  # decline
                follow_request.status = 'declined'
                follow_request.save()
                
                return Response({
                    'message': 'Follow request declined'
                }, status=status.HTTP_200_OK)
                
    except Exception as e:
        return Response({
            'error': f'Failed to respond to follow request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity(request, user_id):
    """
    Get user's activity feed
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Check privacy
        target_profile = target_user.social_profile
        if target_profile.is_private and target_user != request.user:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            if not is_following:
                return Response({
                    'error': 'Private profile - follow to see activity'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get activities
        activities = UserActivity.objects.filter(user=target_user)
        
        # Paginate
        paginator = SocialPagination()
        page = paginator.paginate_queryset(activities, request)
        
        # Serialize
        serializer = UserActivitySerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get user activity: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
