import { apiClient } from './apiClient';

export interface Comment {
  id: string;
  content_type: 'reel' | 'post';
  content_id: string;
  text: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  parent_user?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  parent?: string;
  replies: Comment[];
  likes_count: number;
  replies_count: number;
  is_liked_by_user: boolean;
  mentions: Array<{
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  }>;
  is_edited: boolean;
  edited_at?: string;
  created_at: string;
  time_ago: string;
}

export interface CommentThread {
  id: string;
  content_type: string;
  content_id: string;
  comments_count: number;
  likes_count: number;
  participants_count: number;
  last_comment_at?: string;
  last_comment_by?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface CreateCommentRequest {
  text: string;
  parent_id?: string;
}

export interface UpdateCommentRequest {
  text: string;
}

export interface CommentReportRequest {
  reason: 'spam' | 'harassment' | 'hate_speech' | 'inappropriate' | 'off_topic' | 'other';
  description?: string;
}

export interface CommentNotification {
  id: string;
  comment: Comment;
  notification_type: 'reply' | 'mention' | 'like' | 'thread_update';
  is_read: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

export const commentsApi = {
  // Get comments for content
  getComments: async (
    contentType: 'reel' | 'post',
    contentId: string,
    params?: {
      page?: number;
      page_size?: number;
      sort_by?: 'newest' | 'oldest' | 'popular';
      thread_id?: string;
    }
  ): Promise<PaginatedResponse<Comment>> => {
    const response = await apiClient.get(`/comments/${contentType}/${contentId}/`, { params });
    return response.data;
  },

  // Create comment
  createComment: async (
    contentType: 'reel' | 'post',
    contentId: string,
    data: CreateCommentRequest
  ): Promise<Comment> => {
    const response = await apiClient.post(`/comments/${contentType}/${contentId}/create/`, data);
    return response.data;
  },

  // Update comment
  updateComment: async (commentId: string, data: UpdateCommentRequest): Promise<Comment> => {
    const response = await apiClient.put(`/comments/comment/${commentId}/`, data);
    return response.data;
  },

  // Delete comment
  deleteComment: async (commentId: string): Promise<void> => {
    await apiClient.delete(`/comments/comment/${commentId}/delete/`);
  },

  // Like comment
  likeComment: async (commentId: string): Promise<void> => {
    await apiClient.post(`/comments/comment/${commentId}/like/`);
  },

  // Unlike comment
  unlikeComment: async (commentId: string): Promise<void> => {
    await apiClient.delete(`/comments/comment/${commentId}/unlike/`);
  },

  // Get comment thread info
  getCommentThread: async (
    contentType: 'reel' | 'post',
    contentId: string
  ): Promise<CommentThread> => {
    const response = await apiClient.get(`/comments/${contentType}/${contentId}/thread/`);
    return response.data;
  },

  // Report comment
  reportComment: async (commentId: string, data: CommentReportRequest): Promise<void> => {
    await apiClient.post(`/comments/comment/${commentId}/report/`, data);
  },

  // Get user notifications
  getNotifications: async (params?: {
    page?: number;
    unread_only?: boolean;
  }): Promise<PaginatedResponse<CommentNotification>> => {
    const response = await apiClient.get('/comments/notifications/', { params });
    return response.data;
  },

  // Mark notifications as read
  markNotificationsRead: async (notificationIds?: string[]): Promise<void> => {
    const data = notificationIds ? { notification_ids: notificationIds } : {};
    await apiClient.put('/comments/notifications/read/', data);
  },

  // Get moderation queue (for moderators)
  getModerationQueue: async (params?: {
    status?: 'pending' | 'approved' | 'rejected';
  }): Promise<PaginatedResponse<Comment>> => {
    const response = await apiClient.get('/comments/moderation/queue/', { params });
    return response.data;
  },

  // Moderate comment (for moderators)
  moderateComment: async (
    commentId: string,
    action: 'approve' | 'reject',
    reason?: string
  ): Promise<void> => {
    const data = { action, reason };
    await apiClient.post(`/comments/moderation/comment/${commentId}/`, data);
  }
};
