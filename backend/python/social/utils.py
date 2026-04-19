from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Count, Q, F
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import (
    UserProfile, Follow, Like, Share, FollowRequest, 
    UserActivity, Notification
)


def update_user_stats(user_id):
    """
    Update user's social statistics
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.social_profile
        
        # Update follow counts
        profile.followers_count = user.followers.count()
        profile.following_count = user.following.count()
        
        # Update content counts
        from reels.models import Reel
        profile.reels_count = Reel.objects.filter(user=user).count()
        
        # Update engagement stats
        profile.total_likes_received = Like.objects.filter(
            content_type='reel',
            content_id__in=Reel.objects.filter(user=user).values_list('id', flat=True)
        ).count()
        
        profile.save()
        
        return True
    except Exception as e:
        print(f"Error updating user stats: {e}")
        return False


def get_mutual_followers(user1_id, user2_id):
    """
    Get mutual followers between two users
    """
    try:
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        
        # Get followers of user1 that user2 follows
        mutual = user1.followers.filter(
            id__in=user2.following.values_list('following_id', flat=True)
        )
        
        return mutual
    except User.DoesNotExist:
        return []


def calculate_engagement_rate(user_id, days=30):
    """
    Calculate user's engagement rate
    """
    try:
        user = User.objects.get(id=user_id)
        since = timezone.now() - timezone.timedelta(days=days)
        
        # Get content from last 30 days
        from reels.models import Reel
        content = Reel.objects.filter(user=user, created_at__gte=since)
        
        if not content.exists():
            return 0.0
        
        # Calculate total engagement
        total_likes = Like.objects.filter(
            content_type='reel',
            content_id__in=content.values_list('id', flat=True)
        ).count()
        
        total_comments = 0  # Would need to integrate with comment system
        
        # Calculate total followers
        total_followers = user.followers.count()
        
        if total_followers == 0:
            return 0.0
        
        # Engagement rate = (likes + comments) / followers * 100
        engagement_rate = ((total_likes + total_comments) / total_followers) * 100
        
        return round(engagement_rate, 2)
        
    except User.DoesNotExist:
        return 0.0


def get_trending_users(limit=10, days=7):
    """
    Get trending users based on follower growth and engagement
    """
    try:
        since = timezone.now() - timezone.timedelta(days=days)
        
        # Get users with significant follower growth
        trending = User.objects.annotate(
            follower_growth=Count(
                'followers',
                filter=Q(followers__created_at__gte=since)
            ),
            engagement_rate=F('social_profile__total_likes_received') / (
                F('social_profile__followers_count') + 1
            )
        ).filter(
            follower_growth__gt=0,
            social_profile__followers_count__gt=100
        ).order_by('-follower_growth', '-engagement_rate')[:limit]
        
        return trending
    except Exception as e:
        print(f"Error getting trending users: {e}")
        return []


def recommend_users_to_follow(user_id, limit=20):
    """
    Recommend users for a user to follow
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get users that user's follows follow (friends of friends)
        following_ids = user.following.values_list('following_id', flat=True)
        
        # Get users followed by people user follows
        friends_of_friends = Follow.objects.filter(
            follower_id__in=following_ids
        ).exclude(
            Q(following=user) | Q(following_id__in=following_ids)
        ).values('following_id').annotate(
            mutual_count=Count('follower_id')
        ).order_by('-mutual_count')[:limit]
        
        # Get user IDs
        recommended_ids = [item['following_id'] for item in friends_of_friends]
        
        # Get user objects
        recommended_users = User.objects.filter(id__in=recommended_ids)
        
        return recommended_users
        
    except User.DoesNotExist:
        return []


def check_follow_privacy(follower_id, following_id):
    """
    Check if a user can follow another user based on privacy settings
    """
    try:
        follower = User.objects.get(id=follower_id)
        following = User.objects.get(id=following_id)
        
        profile = following.social_profile
        
        # Users can always follow themselves (shouldn't happen but just in case)
        if follower == following:
            return False, "Cannot follow yourself"
        
        # Check if already following
        if Follow.objects.filter(follower=follower, following=following).exists():
            return False, "Already following"
        
        # Check if private account
        if profile.is_private:
            if profile.allow_follow_requests:
                return True, "follow_request"
            else:
                return False, "Private account - follow requests not allowed"
        
        return True, "direct_follow"
        
    except User.DoesNotExist:
        return False, "User not found"


def get_user_feed_algorithm(user_id, limit=50):
    """
    Get personalized feed for user based on algorithm
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get users that current user follows
        following_ids = user.following.values_list('following_id', flat=True)
        
        # Get content from followed users
        from reels.models import Reel
        feed_content = Reel.objects.filter(
            user_id__in=following_ids,
            is_public=True
        ).order_by('-created_at')[:limit]
        
        # Apply algorithm scoring
        scored_content = []
        for content in feed_content:
            score = 0
            
            # Recency score
            hours_old = (timezone.now() - content.created_at).total_seconds() / 3600
            recency_score = max(0, 100 - hours_old)
            score += recency_score * 0.3
            
            # Engagement score
            engagement_score = min(100, content.likes_count * 2 + content.comments_count)
            score += engagement_score * 0.4
            
            # Follow relationship strength
            follow_age = Follow.objects.filter(
                follower=user,
                following=content.user
            ).first()
            if follow_age:
                days_following = (timezone.now() - follow_age.created_at).days
                relationship_score = min(100, days_following * 2)
                score += relationship_score * 0.3
            
            scored_content.append({
                'content': content,
                'score': score
            })
        
        # Sort by score
        scored_content.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['content'] for item in scored_content]
        
    except User.DoesNotExist:
        return []


@shared_task
def send_social_notification(recipient_id, notification_type, sender_id=None, 
                          sender_username=None, content_type=None, content_id=None):
    """
    Send real-time social notification via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        
        # Send to user's personal channel
        user_channel = f"user_{recipient_id}"
        
        message = {
            'type': 'social_notification',
            'notification_type': notification_type,
            'sender_id': str(sender_id) if sender_id else None,
            'sender_username': sender_username,
            'content_type': content_type,
            'content_id': str(content_id) if content_id else None,
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            user_channel,
            {
                'type': 'social_update',
                'message': message
            }
        )
        
        # Also send to content-specific channels if applicable
        if content_type and content_id:
            content_channel = f"social_{content_type}_{content_id}"
            
            content_message = {
                'type': 'content_update',
                'notification_type': notification_type,
                'sender_id': str(sender_id) if sender_id else None,
                'sender_username': sender_username,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                content_channel,
                {
                    'type': 'social_content_update',
                    'message': content_message
                }
            )
        
    except Exception as e:
        print(f"Error sending social notification: {e}")


@shared_task
def update_all_user_stats():
    """
    Update statistics for all users (run periodically)
    """
    try:
        users = User.objects.all()
        updated_count = 0
        
        for user in users:
            if update_user_stats(user.id):
                updated_count += 1
        
        return {
            'updated_users': updated_count,
            'total_users': users.count()
        }
        
    except Exception as e:
        print(f"Error updating all user stats: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        deleted_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        return {
            'deleted_notifications': deleted_count
        }
        
    except Exception as e:
        print(f"Error cleaning up notifications: {e}")
        return {'error': str(e)}


@shared_task
def generate_user_analytics():
    """
    Generate analytics for all users
    """
    try:
        users = User.objects.all()
        analytics_data = []
        
        for user in users:
            profile = user.social_profile
            
            # Calculate metrics
            engagement_rate = calculate_engagement_rate(user.id)
            
            # Get follower growth (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            follower_growth = Follow.objects.filter(
                following=user,
                created_at__gte=thirty_days_ago
            ).count()
            
            analytics_data.append({
                'user_id': user.id,
                'username': user.username,
                'followers_count': profile.followers_count,
                'following_count': profile.following_count,
                'engagement_rate': engagement_rate,
                'follower_growth_30d': follower_growth,
                'total_likes_received': profile.total_likes_received,
                'total_comments_received': profile.total_comments_received,
                'total_shares_received': profile.total_shares_received,
                'is_private': profile.is_private
            })
        
        return {
            'generated_at': timezone.now().isoformat(),
            'total_users': len(analytics_data),
            'analytics': analytics_data
        }
        
    except Exception as e:
        print(f"Error generating user analytics: {e}")
        return {'error': str(e)}


def get_user_social_graph(user_id, depth=2):
    """
    Get user's social graph (followers and following network)
    """
    try:
        user = User.objects.get(id=user_id)
        
        graph = {
            'user': {
                'id': user.id,
                'username': user.username
            },
            'followers': [],
            'following': [],
            'mutual_connections': {}
        }
        
        # Get direct followers
        followers = user.followers.select_related('follower')[:100]
        for follow in followers:
            graph['followers'].append({
                'id': follow.follower.id,
                'username': follow.follower.username,
                'followed_at': follow.created_at.isoformat()
            })
        
        # Get direct following
        following = user.following.select_related('following')[:100]
        for follow in following:
            graph['following'].append({
                'id': follow.following.id,
                'username': follow.following.username,
                'followed_at': follow.created_at.isoformat()
            })
        
        # Get mutual connections
        if depth > 1:
            for followed_user in following:
                mutuals = get_mutual_followers(user_id, followed_user.following.id)[:10]
                graph['mutual_connections'][followed_user.following.id] = [
                    {
                        'id': mutual.id,
                        'username': mutual.username
                    }
                    for mutual in mutuals
                ]
        
        return graph
        
    except User.DoesNotExist:
        return None


def detect_fake_followers(user_id):
    """
    Detect potentially fake followers using heuristics
    """
    try:
        user = User.objects.get(id=user_id)
        followers = user.followers.select_related('follower')
        
        suspicious_count = 0
        total_count = followers.count()
        
        for follow in followers:
            follower = follow.follower
            suspicion_score = 0
            
            # Check if profile is incomplete
            if not follower.first_name or not follower.last_name:
                suspicion_score += 1
            
            # Check if user has no content
            from reels.models import Reel
            if not Reel.objects.filter(user=follower).exists():
                suspicion_score += 1
            
            # Check if user follows too many people
            if follower.following.count() > 1000:
                suspicion_score += 1
            
            # Check if user has very few followers
            if follower.followers.count() < 10:
                suspicion_score += 1
            
            # Check if account was created recently
            if (timezone.now() - follower.date_joined).days < 7:
                suspicion_score += 2
            
            if suspicion_score >= 3:
                suspicious_count += 1
        
        if total_count == 0:
            return {
                'total_followers': 0,
                'suspicious_count': 0,
                'suspicious_percentage': 0
            }
        
        return {
            'total_followers': total_count,
            'suspicious_count': suspicious_count,
            'suspicious_percentage': round((suspicious_count / total_count) * 100, 2)
        }
        
    except User.DoesNotExist:
        return {
            'total_followers': 0,
            'suspicious_count': 0,
            'suspicious_percentage': 0
        }
