import { apiClient } from '../lib/apiClient';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  bio?: string;
  followers_count: number;
  following_count: number;
  posts_count: number;
  is_following: boolean;
  is_verified: boolean;
  neural_category?: string;
  date_joined: string;
}

export interface UserSuggestion {
  user: UserProfile;
  similarity_score: number;
  match_reason: string;
  common_interests: string[];
}

export const userApi = {
  getUserProfile: (username: string) =>
    apiClient.get<UserProfile>(`/users/${username}/`),
  
  updateProfile: (data: Partial<UserProfile>) =>
    apiClient.patch<UserProfile>('/users/profile/', data),
  
  getCurrentUser: () =>
    apiClient.get<UserProfile>('/users/profile/'),
  
  followUser: (userId: string) =>
    apiClient.post(`/connections/follow/${userId}/`),
  
  unfollowUser: (userId: string) =>
    apiClient.post(`/connections/unfollow/${userId}/`),
  
  getFollowers: (username: string) =>
    apiClient.get<{ results: UserProfile[] }>(`/connections/${username}/followers/`),
  
  getFollowing: (username: string) =>
    apiClient.get<{ results: UserProfile[] }>(`/connections/${username}/following/`),
  
  getRecommendations: () =>
    apiClient.get<UserSuggestion[]>('/connections/suggestions/'),
  
  getFollowRequests: () =>
    apiClient.get<{ results: UserProfile[] }>('/connections/requests/'),
  
  acceptFollowRequest: (userId: string) =>
    apiClient.post(`/connections/accept/${userId}/`),
  
  declineFollowRequest: (userId: string) =>
    apiClient.post(`/connections/decline/${userId}/`),
  
  searchUsers: (query: string) =>
    apiClient.get<{ results: UserProfile[] }>('/users/search/', {
      params: { q: query }
    }),
};
