import { apiClient } from '../lib/apiClient';

export interface Reel {
  id: string;
  creator: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
    avatar_url?: string;
  };
  caption: string;
  video_file?: string;
  thumbnail?: string;
  duration: number;
  view_count: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  is_liked: boolean;
  allow_comments: boolean;
  allow_share: boolean;
  created_at: string;
  hashtags: string[];
  mentions: string[];
  music_track?: string;
}

export interface ReelForward {
  id: string;
  reel: Reel;
  sender: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  message: string;
  is_saved: boolean;
  created_at: string;
  saved_at?: string;
}

export interface ForwardableUser {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
}

export const reelsApi = {
  // Reel CRUD
  getReels: (page = 1, limit = 20) =>
    apiClient.get<{ results: Reel[]; count: number; next: string | null; previous: string | null }>('/reels/', {
      params: { page, limit }
    }),
  
  getReel: (id: string) =>
    apiClient.get<Reel>(`/reels/${id}/`),
  
  createReel: (data: FormData) =>
    apiClient.post<Reel>('/reels/', data),
  
  deleteReel: (id: string) =>
    apiClient.delete(`/reels/${id}/`),
  
  // Reel interactions
  likeReel: (id: string) =>
    apiClient.post(`/reels/${id}/interact/`, { interaction_type: 'like' }),
  
  unlikeReel: (id: string) =>
    apiClient.post(`/reels/${id}/interact/`, { interaction_type: 'unlike' }),
  
  commentOnReel: (id: string, content: string) =>
    apiClient.post(`/reels/${id}/comments/`, { content }),
  
  getReelComments: (id: string) =>
    apiClient.get(`/reels/${id}/comments/`),
  
  // Reel forwarding
  forwardReel: (reelId: string, recipientIds: string[], message?: string) =>
    apiClient.post('/reels/forward/', {
      reel_id: reelId,
      recipient_ids: recipientIds,
      message: message || ''
    }),
  
  getForwardableUsers: (reelId?: string) =>
    apiClient.get<{ users: ForwardableUser[]; total_count: number }>('/reels/forward/users/', {
      params: reelId ? { reel_id: reelId } : {}
    }),
  
  getReceivedForwards: () =>
    apiClient.get<{ forwards: ReelForward[]; total_count: number }>('/reels/forwards/received/'),
  
  getSavedForwards: () =>
    apiClient.get<{ forwards: ReelForward[]; total_count: number }>('/reels/forwards/saved/'),
  
  saveForwardedReel: (forwardId: string) =>
    apiClient.post(`/reels/forwards/${forwardId}/save/`),
  
  unsaveForwardedReel: (forwardId: string) =>
    apiClient.delete(`/reels/forwards/${forwardId}/unsave/`),
  
  // Reel discovery
  getTrendingReels: (timeRange = 'day', limit = 20) =>
    apiClient.get<Reel[]>('/reels/trending/', {
      params: { time_range: timeRange, limit }
    }),
  
  getExploreReels: (category?: string) =>
    apiClient.get<Reel[]>('/reels/explore/', {
      params: { category }
    }),
  
  searchReels: (query: string, filters?: {
    hashtags?: string[];
    music_track?: string;
    min_duration?: number;
    max_duration?: number;
    sort_by?: string;
    sort_order?: string;
  }) =>
    apiClient.get<Reel[]>('/reels/search/', {
      params: { query, ...filters }
    }),
  
  // Reel analytics
  getReelAnalytics: (days = 30) =>
    apiClient.get('/reels/analytics/', {
      params: { days }
    }),
  
  // Reel challenges
  getChallenges: () =>
    apiClient.get('/reels/challenges/'),
  
  enterChallenge: (challengeId: string, reelId: string) =>
    apiClient.post(`/reels/challenges/${challengeId}/enter/`, { reel_id: reelId }),
};
