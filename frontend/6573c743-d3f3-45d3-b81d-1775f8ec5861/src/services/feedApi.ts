import { apiClient } from '../lib/apiClient';

export interface Post {
  id: string;
  user: {
    id: string;
    username: string;
    avatar_url: string;
  };
  video_url?: string;
  image_url?: string;
  caption: string;
  likes_count: number;
  comments_count: number;
  is_liked: boolean;
  created_at: string;
  hashtags: string[];
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

export const feedApi = {
  getHomeFeed: (page = 1, limit = 20) =>
    apiClient.get<PaginatedResponse<Post>>('/reels/', {
      params: { page, limit }
    }),
  
  getExploreFeed: (category?: string) =>
    apiClient.get<PaginatedResponse<Post>>('/reels/explore/', {
      params: { category }
    }),
  
  getTrendingFeed: (hours = 24) =>
    apiClient.get<PaginatedResponse<Post>>('/reels/trending/', {
      params: { hours }
    }),
  
  likePost: (postId: string) =>
    apiClient.post(`/reels/${postId}/interact/`, { interaction_type: 'like' }),
  
  unlikePost: (postId: string) =>
    apiClient.delete(`/reels/${postId}/interact/`),
  
  commentOnPost: (postId: string, content: string) =>
    apiClient.post(`/reels/${postId}/comments/`, { content }),
  
  getComments: (postId: string) =>
    apiClient.get(`/reels/${postId}/comments/`),
  
  createReel: (data: {
    video_file: File;
    caption: string;
    hashtags: string[];
    music_track?: string;
  }) => apiClient.upload('/reels/', data.video_file, {
    caption: data.caption,
    hashtags: JSON.stringify(data.hashtags),
    music_track: data.music_track
  }),
};
