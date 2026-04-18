# Complete Social System Implementation Guide

## Overview

The Instagram clone now has a **complete social system** with real-time follower counts, like functionality, and comprehensive user engagement tracking. All counts update in real-time from backend to frontend via WebSocket connections.

## Features Implemented

### Backend Social System
- **Follow System**: Complete follow/unfollow functionality with real-time count updates
- **Like System**: Posts/reels likes with real-time count synchronization
- **User Profiles**: Extended profiles with social statistics
- **Real-time Updates**: WebSocket integration for live count updates
- **Notifications**: Social interaction notifications
- **Privacy Controls**: Private accounts with follow requests
- **Activity Tracking**: User activity logging and analytics

### Frontend Social Components
- **FollowButton**: Interactive follow/unfollow with real-time updates
- **LikeButton**: Like/unlike functionality with animated counters
- **FollowerCount**: Display follower/following counts with modal views
- **Real-time Integration**: WebSocket connections for live updates
- **Responsive Design**: Mobile-friendly social interactions

### WebSocket Integration
- **Live Updates**: Real-time follower and like count updates
- **Notifications**: Instant social notifications
- **Content Updates**: Live content statistics
- **User Updates**: Real-time user profile updates

## Backend Implementation

### Database Models

**UserProfile Model:**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='social_profile')
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    reels_count = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)
    total_comments_received = models.PositiveIntegerField(default=0)
    total_shares_received = models.PositiveIntegerField(default=0)
    is_private = models.BooleanField(default=False)
    show_activity_status = models.BooleanField(default=True)
    allow_follow_requests = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_post_at = models.DateTimeField(null=True, blank=True)
```

**Follow Model:**
```python
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following')
    following = models.ForeignKey(User, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]
```

**Like Model:**
```python
class Like(models.Model):
    user = models.ForeignKey(User, related_name='likes')
    content_type = models.CharField(max_length=10, choices=[('post', 'Post'), ('reel', 'Reel')])
    content_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['user', 'created_at']),
        ]
```

**Supporting Models:**
- `Share` - Track content sharing
- `FollowRequest` - Handle private account follow requests
- `UserActivity` - Log user activities for analytics
- `Notification` - Social interaction notifications

### API Endpoints

**User Profile & Stats:**
- `GET /api/social/profile/{user_id}/` - Get user profile with stats
- `GET /api/social/profile/{user_id}/followers/` - Get user's followers
- `GET /api/social/profile/{user_id}/following/` - Get users that user follows
- `GET /api/social/profile/{user_id}/activity/` - Get user's activity feed

**Follow/Unfollow:**
- `POST /api/social/follow/{user_id}/` - Follow a user
- `DELETE /api/social/unfollow/{user_id}/` - Unfollow a user

**Content Interactions:**
- `POST /api/social/like/` - Like content (post/reel)
- `DELETE /api/social/unlike/` - Unlike content

**Notifications:**
- `GET /api/social/notifications/` - Get user's notifications
- `PUT /api/social/notifications/read/` - Mark notifications as read

**Follow Requests:**
- `GET /api/social/follow-requests/` - Get pending follow requests
- `POST /api/social/follow-requests/{request_id}/` - Accept/decline follow request

### Real-time Features

**WebSocket Consumers:**
```python
class SocialConsumer(AsyncWebsocketConsumer):
    # Personal notification channel
    # Content subscription/unsubscription
    # User subscription/unsubscription

class ContentSocialConsumer(AsyncWebsocketConsumer):
    # Content-specific social updates
    # Live like/comment/share updates
    # Real-time statistics

class UserSocialConsumer(AsyncWebsocketConsumer):
    # User-specific social updates
    # Follow/unfollow notifications
    # Profile updates
```

**Background Tasks:**
```python
@shared_task
def send_follow_notification(follower_id, following_id):
    # Send real-time follow notification
    # Update follower count in real-time

@shared_task
def send_like_notification(user_id, content_type, content_id, content_owner_id):
    # Send real-time like notification
    # Update like count for content

@shared_task
def update_content_stats(content_type, content_id):
    # Update content statistics
    # Send real-time updates
```

### Signal Handlers

**Follow Events:**
```python
@receiver(post_save, sender=Follow)
def handle_follow_created(sender, instance, created, **kwargs):
    if created:
        # Update user stats
        update_user_stats_task.delay(instance.follower.id)
        update_user_stats_task.delay(instance.following.id)
        
        # Send real-time notification
        send_follow_notification.delay(
            follower_id=instance.follower.id,
            following_id=instance.following.id
        )
        
        # Create activity record
        UserActivity.objects.create(
            user=instance.follower,
            activity_type='follow',
            target_user=instance.following
        )
```

**Like Events:**
```python
@receiver(post_save, sender=Like)
def handle_like_created(sender, instance, created, **kwargs):
    if created:
        # Update content stats
        update_content_stats.delay(instance.content_type, instance.content_id)
        
        # Send notification to content owner
        send_like_notification.delay(
            user_id=instance.user.id,
            content_type=instance.content_type,
            content_id=instance.content_id,
            content_owner_id=content_owner.id
        )
```

## Frontend Implementation

### Social API Service

**Complete API Integration:**
```typescript
export const socialApi = {
  // User profile
  getUserProfile: async (userId: string): Promise<UserProfile>,
  
  // Follow/Unfollow
  followUser: async (userId: string, message?: string),
  unfollowUser: async (userId: string),
  
  // Get followers and following
  getFollowers: async (userId: string, params?: { page?: number }),
  getFollowing: async (userId: string, params?: { page?: number }),
  
  // Like/Unlike content
  likeContent: async (contentType: 'post' | 'reel', contentId: string),
  unlikeContent: async (contentType: 'post' | 'reel', contentId: string),
  
  // Notifications
  getNotifications: async (params?: { page?: number; unread_only?: boolean }),
  markNotificationsRead: async (notificationIds?: string[]),
  
  // Follow requests
  getFollowRequests: async (params?: { page?: number }),
  respondFollowRequest: async (requestId: string, action: 'accept' | 'decline'),
  
  // User activity
  getUserActivity: async (userId: string, params?: { page?: number })
};
```

### FollowButton Component

**Interactive Follow/Unfollow:**
```typescript
export function FollowButton({
  userId,
  username,
  initialIsFollowing = false,
  initialFollowRequestSent = false,
  isPrivate = false,
  variant = 'primary',
  size = 'md'
}: FollowButtonProps) {
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [followRequestSent, setFollowRequestSent] = useState(initialFollowRequestSent);

  // Follow mutation
  const followMutation = useMutation({
    mutationFn: (message?: string) => socialApi.followUser(userId, message),
    onSuccess: (data) => {
      if (data.request_id) {
        // Follow request sent for private account
        setFollowRequestSent(true);
        setIsFollowing(false);
      } else {
        // Direct follow for public account
        setIsFollowing(true);
        setFollowRequestSent(false);
      }
    }
  });

  // Unfollow mutation
  const unfollowMutation = useMutation({
    mutationFn: () => socialApi.unfollowUser(userId),
    onSuccess: () => {
      setIsFollowing(false);
      setFollowRequestSent(false);
    }
  });
}
```

### LikeButton Component

**Real-time Like/Unlike:**
```typescript
export function LikeButton({
  contentType,
  contentId,
  initialLikesCount,
  initialIsLiked,
  showCount = true,
  variant = 'default'
}: LikeButtonProps) {
  const [likesCount, setLikesCount] = useState(initialLikesCount);
  const [isLiked, setIsLiked] = useState(initialIsLiked);

  // Like mutation
  const likeMutation = useMutation({
    mutationFn: () => socialApi.likeContent(contentType, contentId),
    onSuccess: (data) => {
      setLikesCount(data.like_count);
      setIsLiked(data.is_liked);
    }
  });

  // Unlike mutation
  const unlikeMutation = useMutation({
    mutationFn: () => socialApi.unlikeContent(contentType, contentId),
    onSuccess: (data) => {
      setLikesCount(data.like_count);
      setIsLiked(data.is_liked);
    }
  });
}
```

### FollowerCount Component

**Interactive Follower Display:**
```typescript
export function FollowerCount({
  userId,
  initialCount,
  showFollowers = true,
  showFollowing = true,
  variant = 'default'
}: FollowerCountProps) {
  const [showModal, setShowModal] = useState<'followers' | 'following' | null>(null);

  // Get followers
  const { data: followersData, isLoading: followersLoading } = useQuery({
    queryKey: ['followers', userId, page],
    queryFn: () => socialApi.getFollowers(userId, { page, page_size: pageSize }),
    enabled: showModal === 'followers'
  });

  // Get following
  const { data: followingData, isLoading: followingLoading } = useQuery({
    queryKey: ['following', userId, page],
    queryFn: () => socialApi.getFollowing(userId, { page, page_size: pageSize }),
    enabled: showModal === 'following'
  });
}
```

## Real-time Integration

### WebSocket Connection Management

**Social Context:**
```typescript
const SocialContext = createContext({
  subscribeToContent: (contentType: string, contentId: string) => {},
  unsubscribeFromContent: (contentType: string, contentId: string) => {},
  subscribeToUser: (userId: string) => {},
  unsubscribeFromUser: (userId: string) => {},
});

// In your component
const { subscribeToContent } = useSocialContext();

// Subscribe to content updates
subscribeToContent('reel', reel.id);

// Handle real-time updates
const handleSocialUpdate = (event) => {
  // Update UI with new like/follow count
  if (event.type === 'like_update') {
    setLikesCount(event.likes_count);
  }
  if (event.type === 'follow_update') {
    setFollowersCount(event.followers_count);
  }
};
```

### Real-time Update Flow

**Follow Flow:**
1. User clicks "Follow" button
2. Frontend calls `socialApi.followUser()`
3. Backend creates follow relationship
4. Django signal triggers WebSocket message
5. Connected users receive real-time update
6. Frontend updates follower count instantly

**Like Flow:**
1. User clicks "Like" button
2. Frontend calls `socialApi.likeContent()`
3. Backend creates like record
4. Django signal triggers WebSocket message
5. Content owner receives real-time notification
6. All viewers see updated like count

## Count Management

### Backend Count Updates

**Automatic Count Updates:**
```python
def update_user_stats(user_id):
    """Update user's social statistics"""
    user = User.objects.get(id=user_id)
    profile = user.social_profile
    
    # Update follow counts
    profile.followers_count = user.followers.count()
    profile.following_count = user.following.count()
    profile.save(update_fields=['followers_count', 'following_count'])
```

**Content Count Updates:**
```python
def update_content_stats(content_type, content_id):
    """Update content statistics"""
    likes_count = Like.objects.filter(
        content_type=content_type,
        content_id=content_id
    ).count()
    
    # Send real-time update
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"social_{content_type}_{content_id}",
        {
            'type': 'content_stats_update',
            'message': {
                'likes_count': likes_count,
                'timestamp': timezone.now().isoformat()
            }
        }
    )
```

### Frontend Count Synchronization

**Optimistic Updates:**
```typescript
// Immediate UI update
const handleLike = () => {
  if (isLiked) {
    setLikesCount(prev => prev - 1);
    setIsLiked(false);
    unlikeMutation.mutate();
  } else {
    setLikesCount(prev => prev + 1);
    setIsLiked(true);
    likeMutation.mutate();
  }
};

// Server confirmation updates final count
likeMutation.onSuccess = (data) => {
  setLikesCount(data.like_count);
  setIsLiked(data.is_liked);
};
```

**Real-time WebSocket Updates:**
```typescript
// Listen for real-time updates
useEffect(() => {
  const handleSocialUpdate = (event) => {
    if (event.type === 'content_stats_update') {
      if (event.stats.likes_count !== undefined) {
        setLikesCount(event.stats.likes_count);
      }
    }
  };

  // Subscribe to content updates
  subscribeToContent(contentType, contentId);
  
  return () => {
    unsubscribeFromContent(contentType, contentId);
  };
}, [contentType, contentId]);
```

## Privacy & Security

### Follow Requests
```python
# Private account follow flow
if target_profile.is_private and target_profile.allow_follow_requests:
    # Create follow request instead of direct follow
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
```

### Rate Limiting
```python
# Follow rate limiting (50 follows per hour)
class RateLimitFollows(BasePermission):
    def has_permission(self, request, view):
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_follows = Follow.objects.filter(
            follower=request.user,
            created_at__gte=one_hour_ago
        ).count()
        
        return recent_follows < 50
```

## Performance Optimization

### Database Optimization
```python
# Optimized queries with select_related
followers = Follow.objects.filter(
    following=target_user
).select_related('follower')

# Efficient count queries
followers_count = user.followers.count()

# Batch updates
UserProfile.objects.filter(
    user__in=updated_users
).update(
    followers_count=F('followers_count') + 1
)
```

### Caching Strategy
```python
# Cache user profiles
@cache_page(60 * 15)  # 15 minutes
def get_user_profile(request, user_id):
    profile = get_object_or_404(UserProfile, user_id=user_id)
    return UserProfileSerializer(profile).data

# Invalidate cache on updates
@receiver(post_save, sender=Follow)
def invalidate_profile_cache(sender, instance, **kwargs):
    cache.delete(f"user_profile_{instance.following.id}")
```

## File Structure

```
backend/python/social/
models.py              # Database models
views.py               # API views
serializers.py         # API serializers
permissions.py         # Permission classes
utils.py              # Utility functions
tasks.py              # Background tasks
consumers.py          # WebSocket consumers
routing.py            # WebSocket routing
urls.py               # URL configuration
apps.py               # App configuration
signals.py            # Database signals
admin.py              # Django admin
migrations/           # Database migrations

frontend/src/
components/FollowButton.tsx      # Follow/unfollow component
components/LikeButton.tsx        # Like/unlike component
components/FollowerCount.tsx     # Follower count display
services/socialApi.ts            # API service
context/SocialContext.tsx         # WebSocket context
```

## Usage Examples

### Frontend Integration

```typescript
// Follow button in profile
<FollowButton 
  userId={user.id}
  username={user.username}
  initialIsFollowing={profile.is_following}
  initialFollowRequestSent={profile.follow_request_sent}
  isPrivate={profile.is_private}
/>

// Like button on content
<LikeButton 
  contentType="reel"
  contentId={reel.id}
  initialLikesCount={reel.likes_count}
  initialIsLiked={reel.is_liked}
/>

// Follower count display
<FollowerCount 
  userId={user.id}
  initialCount={user.followers_count}
  showFollowers={true}
  showFollowing={true}
/>
```

### Backend Integration

```python
# Add to main urls.py
path('api/social/', include('social.urls')),

# Add to websocket routing
path('ws/social/', include('social.routing')),
```

### WebSocket Connection

```typescript
// Connect to social WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/social/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleSocialUpdate(data);
};

// Subscribe to content updates
ws.send(JSON.stringify({
  type: 'subscribe_to_content',
  content_type: 'reel',
  content_id: reel.id
}));
```

---

## Status: Complete Implementation

The social system is now **fully implemented** with:
- **Complete follow system** with real-time follower count updates
- **Like functionality** for posts/reels with live count synchronization
- **Real-time WebSocket integration** for instant updates
- **User profiles** with comprehensive social statistics
- **Privacy controls** with follow requests for private accounts
- **Performance optimization** with caching and efficient queries
- **Security features** with rate limiting and permissions

All follower counts, like counts, and social statistics now update **in real-time** from backend to frontend, providing a seamless social experience for all users.
