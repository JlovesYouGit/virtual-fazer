import { apiClient } from '../lib/apiClient';

export interface UserProfile {
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  followers_count: number;
  following_count: number;
  posts_count: number;
  reels_count: number;
  total_likes_received: number;
  total_comments_received: number;
  total_shares_received: number;
  is_private: boolean;
  show_activity_status: boolean;
  allow_follow_requests: boolean;
  last_activity?: string;
  last_post_at?: string;
  created_at: string;
  is_following?: boolean;
  follow_request_sent?: boolean;
}

export interface Follow {
  id: string;
  follower: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  following: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  follower_username: string;
  following_username: string;
  created_at: string;
}

export interface Like {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  username: string;
  content_type: 'post' | 'reel';
  content_id: string;
  created_at: string;
}

export interface Share {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  username: string;
  content_type: 'post' | 'reel';
  content_id: string;
  caption: string;
  created_at: string;
}

export interface FollowRequest {
  id: string;
  requester: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  target: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  requester_username: string;
  target_username: string;
  status: 'pending' | 'accepted' | 'declined';
  message: string;
  created_at: string;
  updated_at: string;
}

export interface UserActivity {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  user_username: string;
  activity_type: 'like' | 'comment' | 'share' | 'follow' | 'post' | 'reel';
  content_type?: string;
  content_id?: string;
  target_user?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  target_username?: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface Notification {
  id: string;
  recipient: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  sender: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  recipient_username: string;
  sender_username: string;
  notification_type: 'like' | 'comment' | 'share' | 'follow' | 'follow_request' | 'mention' | 'reel_comment' | 'post_comment';
  content_type?: string;
  content_id?: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

export const socialApi = {
  // User profile
  getUserProfile: async (userId: string): Promise<UserProfile> => {
    const response = await apiClient.get(`/social/profile/${userId}/`);
    return response.data;
  },

  // Follow/Unfollow
  followUser: async (userId: string, message?: string): Promise<any> => {
    const response = await apiClient.post(`/social/follow/${userId}/`, { message });
    return response.data;
  },

  unfollowUser: async (userId: string): Promise<any> => {
    const response = await apiClient.delete(`/social/unfollow/${userId}/`);
    return response.data;
  },

  // Get followers and following
  getFollowers: async (
    userId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<any> => {
    const response = await apiClient.get(`/social/profile/${userId}/followers/`, { params });
    return response.data;
  },

  getFollowing: async (
    userId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<any> => {
    const response = await apiClient.get(`/social/profile/${userId}/following/`, { params });
    return response.data;
  },

  // Like/Unlike content
  likeContent: async (contentType: 'post' | 'reel', contentId: string): Promise<any> => {
    const response = await apiClient.post(`/social/like/${contentType}/${contentId}/`);
    return response.data;
  },

  unlikeContent: async (contentType: 'post' | 'reel', contentId: string): Promise<any> => {
    const response = await apiClient.delete('/social/unlike/', {
      data: {
        content_type: contentType,
        content_id: contentId
      }
    });
    return response.data;
  },

  // Notifications
  getNotifications: async (params?: {
    page?: number;
    unread_only?: boolean;
  }): Promise<PaginatedResponse<Notification>> => {
    const response = await apiClient.get('/social/notifications/', { params });
    return response.data;
  },

  markNotificationsRead: async (notificationIds?: string[]): Promise<{ message: string }> => {
    const response = await apiClient.put('/social/notifications/read/', {
      notification_ids: notificationIds
    });
    return response.data;
  },

  // Follow requests
  getFollowRequests: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<FollowRequest>> => {
    const response = await apiClient.get('/social/follow-requests/', { params });
    return response.data;
  },

  respondFollowRequest: async (
    requestId: string,
    action: 'accept' | 'decline'
  ): Promise<{ message: string }> => {
    const response = await apiClient.post(`/social/follow-requests/${requestId}/`, { action });
    return response.data;
  },

  // User activity
  getUserActivity: async (
    userId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<UserActivity>> => {
    const response = await apiClient.get(`/social/profile/${userId}/activity/`, { params });
    return response.data;
  }
};
