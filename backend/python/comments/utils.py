import re
from django.contrib.auth.models import User
from django.utils import timezone
from .models import CommentNotification


def extract_mentions(text):
    """
    Extract @username mentions from comment text
    """
    # Pattern to match @username (letters, numbers, underscores, dots)
    pattern = r'@([a-zA-Z0-9_.]+)'
    matches = re.findall(pattern, text)
    return list(set(matches))  # Remove duplicates


def send_comment_notification(recipient, comment, notification_type):
    """
    Send notification to user about comment activity
    """
    # Create notification in database
    notification = CommentNotification.objects.create(
        recipient=recipient,
        comment=comment,
        notification_type=notification_type
    )
    
    # Send realtime update via WebSocket
    send_realtime_comment_update.delay(
        recipient_id=recipient.id,
        notification_type=notification_type,
        comment_id=comment.id,
        comment_text=comment.text[:100],  # First 100 chars
        comment_user=comment.user.username,
        content_type=comment.content_type,
        content_id=comment.content_id
    )
    
    return notification


def format_comment_text(text, mentions=None):
    """
    Format comment text with proper mention links and line breaks
    """
    if mentions is None:
        mentions = extract_mentions(text)
    
    # Replace @username with clickable links
    for username in mentions:
        text = re.sub(
            f'@{username}',
            f'[@{username}](/profile/{username})',
            text
        )
    
    # Convert line breaks to <br> for HTML display
    text = text.replace('\n', '<br>')
    
    return text


def get_comment_stats(content_type=None, content_id=None, user_id=None, date_range=None):
    """
    Get comment statistics
    """
    from .models import Comment, CommentLike
    
    queryset = Comment.objects.filter(is_deleted=False, moderation_status='approved')
    
    if content_type and content_id:
        queryset = queryset.filter(content_type=content_type, content_id=content_id)
    elif content_type:
        queryset = queryset.filter(content_type=content_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if date_range:
        queryset = queryset.filter(created_at__range=date_range)
    
    stats = {
        'total_comments': queryset.count(),
        'total_likes': CommentLike.objects.filter(comment__in=queryset).count(),
        'active_threads': queryset.filter(parent=None).count(),
        'recent_activity': queryset.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
    }
    
    return stats


def validate_comment_permissions(user, content_type, content_id, action='create'):
    """
    Validate if user can perform action on content
    """
    # Check if user is authenticated
    if not user.is_authenticated:
        return False, "Authentication required"
    
    # Check if user is suspended or banned
    if hasattr(user, 'profile'):
        if user.profile.is_suspended:
            return False, "Account suspended"
        if user.profile.is_banned:
            return False, "Account banned"
    
    # Check if content exists and user can access it
    # This would depend on your content models
    try:
        if content_type == 'reel':
            from reels.models import Reel
            content = Reel.objects.get(id=content_id)
            if not content.is_public and content.user != user:
                return False, "Cannot comment on private content"
        elif content_type == 'post':
            # Similar check for posts
            pass
    except:
        return False, "Content not found"
    
    # Check rate limiting (e.g., max 10 comments per minute)
    recent_comments = Comment.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
    ).count()
    
    if recent_comments >= 10:
        return False, "Rate limit exceeded"
    
    return True, "Allowed"


def cleanup_old_notifications():
    """
    Clean up old notifications (older than 30 days)
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    deleted_count = CommentNotification.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return deleted_count


def get_trending_comments(content_type=None, hours=24):
    """
    Get trending comments based on likes and recent activity
    """
    from .models import Comment, CommentLike
    
    since = timezone.now() - timezone.timedelta(hours=hours)
    
    queryset = Comment.objects.filter(
        is_deleted=False,
        moderation_status='approved',
        created_at__gte=since
    )
    
    if content_type:
        queryset = queryset.filter(content_type=content_type)
    
    # Order by likes count and recent activity
    trending = queryset.annotate(
        like_score=models.Count('likes')
    ).order_by('-like_score', '-created_at')[:20]
    
    return trending


def detect_spam_comment(text, user):
    """
    Simple spam detection for comments
    """
    spam_indicators = [
        # Check for excessive links
        len(re.findall(r'http[s]?://\S+', text)) > 2,
        # Check for excessive caps
        sum(1 for c in text if c.isupper()) / len(text) > 0.7 if text else False,
        # Check for repeated characters
        bool(re.search(r'(.)\1{4,}', text)),
        # Check for spam keywords
        any(keyword in text.lower() for keyword in ['buy now', 'free money', 'click here', 'limited offer']),
        # Check new user spam (less than 1 day old)
        (timezone.now() - user.date_joined).days < 1
    ]
    
    spam_score = sum(spam_indicators)
    
    return {
        'is_spam': spam_score >= 2,
        'spam_score': spam_score,
        'indicators': spam_indicators
    }


def auto_moderate_comment(comment):
    """
    Automatically moderate comment based on content
    """
    spam_result = detect_spam_comment(comment.text, comment.user)
    
    if spam_result['is_spam']:
        comment.moderation_status = 'rejected'
        comment.is_flagged = True
        comment.save()
        return {
            'action': 'rejected',
            'reason': 'Spam detected',
            'spam_score': spam_result['spam_score']
        }
    
    # Check for inappropriate content (would integrate with content moderation API)
    # For now, auto-approve clean comments
    comment.moderation_status = 'approved'
    comment.save()
    
    return {
        'action': 'approved',
        'reason': 'Auto-approved'
    }


def get_comment_context(comment, max_depth=2):
    """
    Get comment context (parent and nearby comments)
    """
    context = {
        'parent': None,
        'siblings': [],
        'children': []
    }
    
    # Get parent comment
    if comment.parent:
        context['parent'] = comment.parent
    
    # Get sibling comments (same parent, excluding current)
    if comment.parent:
        siblings = Comment.objects.filter(
            parent=comment.parent,
            is_deleted=False,
            moderation_status='approved'
        ).exclude(id=comment.id).order_by('created_at')[:5]
        context['siblings'] = siblings
    
    # Get child comments (replies)
    if max_depth > 0:
        children = Comment.objects.filter(
            parent=comment,
            is_deleted=False,
            moderation_status='approved'
        ).order_by('created_at')
        context['children'] = children
    
    return context


def export_comments(content_type, content_id, format='json', include_deleted=False):
    """
    Export comments for content in specified format
    """
    queryset = Comment.objects.filter(
        content_type=content_type,
        content_id=content_id
    )
    
    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)
    
    if format == 'json':
        from .serializers import CommentSerializer
        serializer = CommentSerializer(queryset, many=True)
        return serializer.data
    
    elif format == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="comments_{content_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'id', 'user', 'text', 'parent_id', 'likes_count', 
            'created_at', 'is_deleted', 'moderation_status'
        ])
        
        for comment in queryset:
            writer.writerow([
                comment.id,
                comment.user.username,
                comment.text,
                comment.parent.id if comment.parent else '',
                comment.likes_count,
                comment.created_at.isoformat(),
                comment.is_deleted,
                comment.moderation_status
            ])
        
        return response
    
    return None


def search_comments(query, content_type=None, user_id=None, date_range=None, sort_by='newest'):
    """
    Search comments by text content
    """
    from .models import Comment
    
    queryset = Comment.objects.filter(
        text__icontains=query,
        is_deleted=False,
        moderation_status='approved'
    )
    
    if content_type and content_type != 'all':
        queryset = queryset.filter(content_type=content_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if date_range:
        queryset = queryset.filter(created_at__range=date_range)
    
    # Sort results
    if sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'oldest':
        queryset = queryset.order_by('created_at')
    elif sort_by == 'popular':
        queryset = queryset.order_by('-likes_count', '-created_at')
    
    return queryset


def get_user_comment_activity(user, days=30):
    """
    Get user's comment activity statistics
    """
    from .models import Comment, CommentLike
    
    since = timezone.now() - timezone.timedelta(days=days)
    
    user_comments = Comment.objects.filter(
        user=user,
        created_at__gte=since
    )
    
    stats = {
        'comments_count': user_comments.count(),
        'likes_received': CommentLike.objects.filter(
            comment__in=user_comments
        ).count(),
        'replies_received': Comment.objects.filter(
            parent__in=user_comments
        ).count(),
        'mentions_received': Comment.objects.filter(
            mentions__mentioned_user=user,
            created_at__gte=since
        ).distinct().count(),
        'daily_activity': {}
    }
    
    # Daily breakdown
    for day in range(days):
        date = (timezone.now() - timezone.timedelta(days=day)).date()
        daily_count = user_comments.filter(created_at__date=date).count()
        stats['daily_activity'][date.isoformat()] = daily_count
    
    return stats
