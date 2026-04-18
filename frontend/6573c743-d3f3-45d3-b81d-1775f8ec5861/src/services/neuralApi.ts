import { apiClient } from '../lib/apiClient';

export interface NeuralProfile {
  user_id: string;
  category: string;
  confidence_score: number;
  behavior_patterns: string[];
  interests: string[];
  created_at: string;
  updated_at: string;
}

export interface UserMatch {
  user: {
    id: string;
    username: string;
    avatar_url: string;
    first_name: string;
    last_name: string;
  };
  similarity_score: number;
  match_reason: string;
  common_interests: string[];
}

export interface NeuralCategory {
  id: string;
  name: string;
  description: string;
  color: string;
  icon: string;
  user_count: number;
}

export interface AutoFollowSettings {
  enabled: boolean;
  confidence_threshold: number;
  max_follows_per_day: number;
  categories: string[];
}

export const neuralApi = {
  getNeuralProfile: () =>
    apiClient.get<NeuralProfile>('/neural/profile/'),
  
  getRecommendations: (limit = 20) =>
    apiClient.get<UserMatch[]>('/neural/match/', {
      params: { limit }
    }),
  
  analyzeBehavior: () =>
    apiClient.post<NeuralProfile>('/neural/analyze/'),
  
  autoFollow: (settings: AutoFollowSettings) =>
    apiClient.post<{ followed_users: number; skipped_users: number }>('/neural/auto-follow/', settings),
  
  getAutoFollowSettings: () =>
    apiClient.get<AutoFollowSettings>('/neural/auto-follow/settings/'),
  
  updateAutoFollowSettings: (settings: Partial<AutoFollowSettings>) =>
    apiClient.patch<AutoFollowSettings>('/neural/auto-follow/settings/', settings),
  
  getCategories: () =>
    apiClient.get<NeuralCategory[]>('/neural/categories/'),
  
  getCategoryUsers: (categoryName: string, limit = 20) =>
    apiClient.get<UserMatch[]>(`/neural/categories/${categoryName}/users/`, {
      params: { limit }
    }),
  
  getBehavioralInsights: () =>
    apiClient.get<{
      top_interests: string[];
      engagement_patterns: string[];
      best_posting_times: string[];
      content_preferences: string[];
    }>('/neural/insights/'),
  
  trackUserAction: (action: {
    action_type: string;
    target_type: string;
    target_id: string;
    metadata?: Record<string, any>;
  }) =>
    apiClient.post('/neural/track/', action),
};
