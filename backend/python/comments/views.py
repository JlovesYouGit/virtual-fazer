from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import (
    Comment, CommentLike, CommentMention, CommentThread, 
    CommentReport, CommentNotification
)
from .serializers import (
    CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer,
    CommentLikeSerializer, CommentThreadSerializer
)
from .utils import extract_mentions, send_comment_notification
from .permissions import CanCommentContent, CanModerateComments


class CommentPagination(PageNumberPagination):
    """Custom pagination for comments"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comments(request, content_type, content_id):
    """
    Get comments for a specific content (reel/post)
    """
    try:
        # Validate content type
        if content_type not in ['reel', 'post']:
            return Response({
                'error': 'Invalid content type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get query parameters
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        sort_by = request.GET.get('sort_by', 'newest')
        thread_id = request.GET.get('thread_id')
        
        # Build queryset
        queryset = Comment.objects.filter(
            content_type=content_type,
            content_id=content_id,
            is_deleted=False,
            moderation_status='approved'
        )
        
        # Filter by thread if specified
        if thread_id:
            try:
                root_comment = Comment.objects.get(id=thread_id)
                queryset = queryset.filter(
                    models.Q(id=thread_id) | models.Q(parent_id=thread_id)
                )
            except Comment.DoesNotExist:
                return Response({
                    'error': 'Thread not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Sort comments
        if sort_by == 'newest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-likes_count', '-created_at')
        else:
            queryset = queryset.order_by('created_at')
        
        # Paginate
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Serialize
        serializer = CommentSerializer(page, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get comments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanCommentContent])
def create_comment(request, content_type, content_id):
    """
    Create a new comment
    """
    try:
        # Validate content type
        if content_type not in ['reel', 'post']:
            return Response({
                'error': 'Invalid content type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['content_type'] = content_type
        data['content_id'] = content_id
        data['user'] = request.user.id
        
        # Validate and create comment
        serializer = CommentCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Create comment
            comment = serializer.save()
            
            # Update or create thread
            thread, created = CommentThread.objects.get_or_create(
                content_type=content_type,
                content_id=content_id
            )
            thread.update_statistics()
            
            # Extract and create mentions
            mentions = extract_mentions(comment.text)
            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    if mentioned_user != request.user:
                        CommentMention.objects.create(
                            comment=comment,
                            mentioned_user=mentioned_user
                        )
                        # Send notification
                        send_comment_notification(
                            mentioned_user, 
                            comment, 
                            'mention'
                        )
                except User.DoesNotExist:
                    continue
            
            # Send reply notification if this is a reply
            if comment.parent and comment.parent.user != request.user:
                send_comment_notification(
                    comment.parent.user,
                    comment,
                    'reply'
                )
            
            # Update content's comment count (signal will handle this)
            
            return Response(
                CommentSerializer(comment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
            
    except Exception as e:
        return Response({
            'error': f'Failed to create comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_comment(request, comment_id):
    """
    Update an existing comment
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        
        # Check if comment can be edited (not too old, not deleted)
        if comment.is_deleted:
            return Response({
                'error': 'Cannot edit deleted comment'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check time limit (e.g., 15 minutes)
        time_limit = timezone.now() - timezone.timedelta(minutes=15)
        if comment.created_at < time_limit:
            return Response({
                'error': 'Comment can only be edited within 15 minutes'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        
        # Validate and update
        serializer = CommentUpdateSerializer(comment, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        updated_comment = serializer.save()
        
        return Response(
            CommentSerializer(updated_comment, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to update comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """
    Delete a comment (soft delete)
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        
        if comment.is_deleted:
            return Response({
                'error': 'Comment already deleted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete
        comment.delete()
        
        # Update thread statistics
        try:
            thread = CommentThread.objects.get(
                content_type=comment.content_type,
                content_id=comment.content_id
            )
            thread.update_statistics()
        except CommentThread.DoesNotExist:
            pass
        
        return Response({
            'message': 'Comment deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to delete comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_comment(request, comment_id):
    """
    Like a comment
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if already liked
        if CommentLike.objects.filter(comment=comment, user=request.user).exists():
            return Response({
                'error': 'Comment already liked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create like
        like = CommentLike.objects.create(comment=comment, user=request.user)
        
        # Update comment's like count
        comment.likes_count = CommentLike.objects.filter(comment=comment).count()
        comment.save(update_fields=['likes_count'])
        
        # Send notification to comment author (if not self)
        if comment.user != request.user:
            send_comment_notification(comment.user, comment, 'like')
        
        return Response(
            CommentLikeSerializer(like).data,
            status=status.HTTP_201_CREATED
        )
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to like comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unlike_comment(request, comment_id):
    """
    Unlike a comment
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Get and delete like
        like = CommentLike.objects.filter(comment=comment, user=request.user).first()
        if not like:
            return Response({
                'error': 'Comment not liked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        like.delete()
        
        # Update comment's like count
        comment.likes_count = CommentLike.objects.filter(comment=comment).count()
        comment.save(update_fields=['likes_count'])
        
        return Response({
            'message': 'Comment unliked successfully'
        }, status=status.HTTP_200_OK)
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to unlike comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_thread(request, content_type, content_id):
    """
    Get comment thread information
    """
    try:
        if content_type not in ['reel', 'post']:
            return Response({
                'error': 'Invalid content type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        thread = get_object_or_404(
            CommentThread, 
            content_type=content_type, 
            content_id=content_id
        )
        
        serializer = CommentThreadSerializer(thread)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except CommentThread.DoesNotExist:
        return Response({
            'error': 'Thread not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to get thread: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    """
    Report a comment for moderation
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if already reported
        if CommentReport.objects.filter(
            comment=comment, 
            reporter=request.user
        ).exists():
            return Response({
                'error': 'Comment already reported'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        reason = data.get('reason')
        description = data.get('description', '')
        
        if not reason:
            return Response({
                'error': 'Reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create report
        report = CommentReport.objects.create(
            comment=comment,
            reporter=request.user,
            reason=reason,
            description=description
        )
        
        return Response({
            'message': 'Comment reported successfully',
            'report_id': report.id
        }, status=status.HTTP_201_CREATED)
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to report comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notifications(request):
    """
    Get user's comment notifications
    """
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        
        # Build queryset
        queryset = CommentNotification.objects.filter(recipient=request.user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Order by creation date
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Serialize
        from .serializers import CommentNotificationSerializer
        serializer = CommentNotificationSerializer(page, many=True)
        
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
            CommentNotification.objects.filter(
                id__in=notification_ids,
                recipient=request.user
            ).update(is_read=True)
        else:
            # Mark all notifications as read
            CommentNotification.objects.filter(
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
@permission_classes([IsAuthenticated, CanModerateComments])
def get_moderation_queue(request):
    """
    Get comments in moderation queue
    """
    try:
        # Get query parameters
        status_filter = request.GET.get('status', 'pending')
        
        # Build queryset
        queryset = Comment.objects.filter(
            moderation_status=status_filter,
            is_deleted=False
        ).order_by('-created_at')
        
        # Paginate
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Serialize
        serializer = CommentSerializer(page, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get moderation queue: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanModerateComments])
def moderate_comment(request, comment_id):
    """
    Moderate a comment (approve/reject)
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        data = request.data
        action = data.get('action')  # 'approve' or 'reject'
        reason = data.get('reason', '')
        
        if action not in ['approve', 'reject']:
            return Response({
                'error': 'Invalid action'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update moderation status
        comment.moderation_status = 'approved' if action == 'approve' else 'rejected'
        if action == 'reject' and reason:
            comment.moderation_status = 'rejected'
            comment.is_deleted = True
            comment.text = f"[removed by moderator: {reason}]"
        
        comment.save()
        
        return Response({
            'message': f'Comment {action}d successfully'
        }, status=status.HTTP_200_OK)
        
    except Comment.DoesNotExist:
        return Response({
            'error': 'Comment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to moderate comment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
