import { apiClient } from '../lib/apiClient';

export interface Story {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  content_type: 'image' | 'video' | 'text' | 'reel_share' | 'post_share' | 'profile_share';
  media_file?: string;
  media_url?: string;
  text_content?: string;
  background_color: string;
  text_color: string;
  caption: string;
  hashtags: string;
  mentions: string;
  hashtags_list: string[];
  mentions_list: string[];
  expires_at: string;
  is_expired: boolean;
  view_count: number;
  viewer_count: number;
  likes_count: number;
  shares_count: number;
  replies_count: number;
  is_active: boolean;
  is_archived: boolean;
  is_reported: boolean;
  time_remaining: {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
  };
  hours_remaining: number;
  is_expired_now: boolean;
  is_liked: boolean;
  created_at: string;
  updated_at: string;
}

export interface StoryView {
  id: string;
  viewer: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  viewed_at: string;
  view_duration: number;
  time_ago: string;
}

export interface StoryReply {
  id: string;
  story: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  content: string;
  parent?: string;
  likes_count: number;
  replies_count: number;
  thread_replies: StoryReply[];
  is_deleted: boolean;
  is_reported: boolean;
  is_liked: boolean;
  created_at: string;
  updated_at: string;
  time_ago: string;
}

export interface StoryShare {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  share_type: 'direct_message' | 'post' | 'external' | 'story';
  shared_to?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  caption: string;
  created_at: string;
  time_ago: string;
}

export interface StoryHighlight {
  id: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  title: string;
  cover_story?: Story;
  stories: Story[];
  stories_count: number;
  is_active: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  time_ago: string;
}

export interface StoryAnalytics {
  id: string;
  story: string;
  date: string;
  date_formatted: string;
  views_count: number;
  unique_viewers: number;
  likes_count: number;
  shares_count: number;
  replies_count: number;
  completion_rate: number;
  engagement_rate: number;
  reach: number;
}

export interface CreateStoryData {
  content_type: 'image' | 'video' | 'text';
  media_file?: File;
  text_content?: string;
  caption?: string;
  hashtags?: string;
  mentions?: string;
  background_color?: string;
  text_color?: string;
}

export interface ReplyToStoryData {
  content: string;
  parent_id?: string;
}

export interface ShareStoryData {
  share_type: 'direct_message' | 'post' | 'external' | 'story';
  shared_to?: string;
  caption?: string;
}

export interface CreateHighlightData {
  title: string;
  story_ids?: string[];
  cover_story_id?: string;
}

export const storiesApi = {
  // Story listing and viewing
  getStories: () =>
    apiClient.get<Story[]>('/stories/'),
  
  getUserStories: (userId: string) =>
    apiClient.get<Story[]>(`/stories/user/${userId}/`),
  
  getStory: (storyId: string) =>
    apiClient.get<Story>(`/stories/${storyId}/`),
  
  // Story creation and management
  createStory: (data: CreateStoryData) =>
    apiClient.post<{ story: Story; message: string }>('/stories/create/', data),
  
  viewStory: (storyId: string) =>
    apiClient.post<{ status: string; view_count: number }>(`/stories/${storyId}/view/`),
  
  likeStory: (storyId: string) =>
    apiClient.post<{ status: string; like_count: number; is_liked: boolean }>(`/stories/${storyId}/like/`),
  
  deleteStory: (storyId: string) =>
    apiClient.post<{ message: string }>(`/stories/${storyId}/delete/`),
  
  // Story interactions
  getStoryViewers: (storyId: string) =>
    apiClient.get<{ viewers: StoryView[]; total_views: number; unique_viewers: number }>(`/stories/${storyId}/viewers/`),
  
  getStoryReplies: (storyId: string) =>
    apiClient.get<{ replies: StoryReply[]; total_replies: number }>(`/stories/${storyId}/replies/`),
  
  replyToStory: (storyId: string, data: ReplyToStoryData) =>
    apiClient.post<{ reply: StoryReply; message: string }>(`/stories/${storyId}/reply/`, data),
  
  shareStory: (storyId: string, data: ShareStoryData) =>
    apiClient.post<{ share: StoryShare; message: string }>(`/stories/${storyId}/share/`, data),
  
  // Story highlights
  getUserHighlights: (userId: string) =>
    apiClient.get<{ highlights: StoryHighlight[] }>(`/stories/highlights/user/${userId}/`),
  
  createHighlight: (data: CreateHighlightData) =>
    apiClient.post<{ highlight: StoryHighlight; message: string }>('/stories/highlights/create/', data),
  
  // Story analytics
  getStoryAnalytics: (storyId: string) =>
    apiClient.get<{ 
      basic_stats: {
        total_views: number;
        unique_viewers: number;
        total_likes: number;
        total_shares: number;
        total_replies: number;
        engagement_rate: number;
      };
      daily_analytics: StoryAnalytics[];
    }>(`/stories/${storyId}/analytics/`),
};
