# Frontend Integration Roadmap - Instagran Platform

## Overview
This is a structured task list for integrating the existing React/Vite frontend with the Django backend API, following the project specifications for the Instagram-like neural social platform.

## Phase 0 - Prepare For Vercel & Environments

### 1. Add environment variables support
**Files to create/modify:**
- Create `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/.env.local`
- Update `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/vite.config.ts`

**Environment Variables:**
```bash
# Development (.env.local)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:3000
VITE_APP_URL=http://localhost:5173
VITE_GOOGLE_CLIENT_ID=your-google-client-id

# Production (Vercel Dashboard)
VITE_API_BASE_URL=https://api.instagran.com
VITE_WS_URL=wss://ws.instagran.com
VITE_APP_URL=https://instagran.vercel.app
VITE_GOOGLE_CLIENT_ID=prod-google-client-id
```

**Replace hardcoded URLs:**
- Update all `localhost:8000` references to use `import.meta.env.VITE_API_BASE_URL`
- Update WebSocket connections to use `import.meta.env.VITE_WS_URL`

### 2. Verify Vite build for Vercel
**Tasks:**
- Run `npm run build` and verify `dist` folder creation
- Test `npm run preview` locally
- Add base path configuration if needed in `vite.config.ts`

---

## Phase 1 - Implement Authentication & Session

### 3. Create a typed API client
**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/lib/apiClient.ts`

**Implementation:**
```typescript
import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL;

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await apiClient.post('/auth/refresh/', {
            refresh: refreshToken,
          });
          const { access } = response.data;
          localStorage.setItem('accessToken', access);
          // Retry original request
          return apiClient.request(error.config);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

### 4. Implement AuthContext
**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/context/AuthContext.tsx`

**Implementation:**
```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../lib/apiClient';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  status: 'idle' | 'authenticating' | 'authenticated' | 'unauthenticated';
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<void>;
  bootstrap: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'authenticating' | 'authenticated' | 'unauthenticated'>('idle');

  const login = async (email: string, password: string) => {
    try {
      setStatus('authenticating');
      const response = await apiClient.post('/auth/login/', { email, password });
      const { access, refresh, user: userData } = response.data;
      
      setAccessToken(access);
      setRefreshToken(refresh);
      setUser(userData);
      setStatus('authenticated');
      
      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      setStatus('unauthenticated');
      throw error;
    }
  };

  const loginWithGoogle = async (idToken: string) => {
    try {
      setStatus('authenticating');
      const response = await apiClient.post('/users/social/google/login/', { id_token: idToken });
      const { access_token, refresh_token, user: userData } = response.data;
      
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      setUser(userData);
      setStatus('authenticated');
      
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      setStatus('unauthenticated');
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    setStatus('unauthenticated');
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  };

  const refreshTokens = async () => {
    try {
      const response = await apiClient.post('/auth/refresh/', {
        refresh: refreshToken,
      });
      const { access } = response.data;
      setAccessToken(access);
      localStorage.setItem('accessToken', access);
    } catch (error) {
      logout();
    }
  };

  const bootstrap = async () => {
    const token = localStorage.getItem('accessToken');
    const refresh = localStorage.getItem('refreshToken');
    const userData = localStorage.getItem('user');
    
    if (token && refresh && userData) {
      try {
        setAccessToken(token);
        setRefreshToken(refresh);
        setUser(JSON.parse(userData));
        setStatus('authenticated');
      } catch (error) {
        logout();
      }
    } else {
      setStatus('unauthenticated');
    }
  };

  useEffect(() => {
    bootstrap();
  }, []);

  return (
    <AuthContext.Provider value={{
      user, accessToken, refreshToken, status,
      login, loginWithGoogle, logout, refreshTokens, bootstrap
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 5. Add protected routing
**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/components/ProtectedRoute.tsx`

**Implementation:**
```typescript
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'authenticating') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin" size={48} />
      </div>
    );
  }

  if (status !== 'authenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

### 6. Wire UI to real auth
**Files to modify:**
- `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/App.tsx`
- `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/pages/LoginPage.tsx`
- `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/pages/SignupPage.tsx`
- `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/components/AppLayout.tsx`

**App.tsx updates:**
```typescript
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

// Wrap app with AuthProvider
// Wrap protected routes with ProtectedRoute
```

**LoginPage.tsx updates:**
```typescript
import { useAuth } from '../context/AuthContext';

// Connect form to useAuth.login()
// Add Google OAuth integration
```

---

## Phase 2 - Replace Mock Data With Real APIs

### 7. Set up feature-specific API modules
**Directory:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/services/`

**Files to create:**

**feedApi.ts:**
```typescript
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

export const feedApi = {
  getHomeFeed: (page = 1, limit = 20) =>
    apiClient.get<{ results: Post[]; count: number }>('/reels/', {
      params: { page, limit }
    }),
  
  getExploreFeed: (category?: string) =>
    apiClient.get<{ results: Post[] }>('/reels/explore/', {
      params: { category }
    }),
  
  getTrendingFeed: (hours = 24) =>
    apiClient.get<{ results: Post[] }>('/reels/trending/', {
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
};
```

**userApi.ts:**
```typescript
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
}

export const userApi = {
  getUserProfile: (username: string) =>
    apiClient.get<UserProfile>(`/users/${username}/`),
  
  updateProfile: (data: Partial<UserProfile>) =>
    apiClient.patch('/users/profile/', data),
  
  followUser: (userId: string) =>
    apiClient.post(`/connections/follow/${userId}/`),
  
  unfollowUser: (userId: string) =>
    apiClient.post(`/connections/unfollow/${userId}/`),
  
  getFollowers: (username: string) =>
    apiClient.get(`/connections/${username}/followers/`),
  
  getFollowing: (username: string) =>
    apiClient.get(`/connections/${username}/following/`),
  
  getRecommendations: () =>
    apiClient.get('/connections/suggestions/'),
};
```

**chatApi.ts:**
```typescript
import { apiClient } from '../lib/apiClient';

export interface Conversation {
  id: string;
  participant: {
    id: string;
    username: string;
    avatar_url: string;
    is_online: boolean;
  };
  last_message: {
    content: string;
    created_at: string;
    sender: string;
  };
  unread_count: number;
}

export interface Message {
  id: string;
  content: string;
  sender: string;
  created_at: string;
  message_type: 'text' | 'image' | 'video';
}

export const chatApi = {
  getConversations: () =>
    apiClient.get<Conversation[]>('/chat/rooms/'),
  
  getMessages: (roomId: string) =>
    apiClient.get<Message[]>(`/chat/rooms/${roomId}/messages/`),
  
  sendMessage: (roomId: string, content: string, type = 'text') =>
    apiClient.post(`/chat/rooms/${roomId}/messages/`, {
      content,
      message_type: type
    }),
  
  createRoom: (participantId: string) =>
    apiClient.post('/chat/rooms/', { participant: participantId }),
};
```

**neuralApi.ts:**
```typescript
import { apiClient } from '../lib/apiClient';

export interface NeuralProfile {
  user_id: string;
  category: string;
  confidence_score: number;
  behavior_patterns: string[];
  interests: string[];
}

export interface UserMatch {
  user: {
    id: string;
    username: string;
    avatar_url: string;
  };
  similarity_score: number;
  match_reason: string;
  common_interests: string[];
}

export const neuralApi = {
  getNeuralProfile: () =>
    apiClient.get<NeuralProfile>('/neural/profile/'),
  
  getRecommendations: (limit = 20) =>
    apiClient.get<UserMatch[]>('/neural/match/', {
      params: { limit }
    }),
  
  analyzeBehavior: () =>
    apiClient.post('/neural/analyze/'),
  
  autoFollow: (confidenceThreshold = 0.8, maxFollows = 10) =>
    apiClient.post('/neural/auto-follow/', {
      confidence_threshold: confidenceThreshold,
      max_follows: maxFollows
    }),
  
  getCategories: () =>
    apiClient.get('/neural/categories/'),
};
```

### 8. Integrate data-fetching layer (TanStack Query)
**Install dependencies:**
```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/lib/queryClient.ts`

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});
```

**Update App.tsx:**
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './lib/queryClient';

// Wrap app with QueryClientProvider
```

### 9. Update each page with real data

**FeedPage.tsx updates:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { feedApi, Post } from '../services/feedApi';
import { Loader2, AlertCircle } from 'lucide-react';

export function FeedPage() {
  const {
    data: feedData,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  } = useInfiniteQuery({
    queryKey: ['homeFeed'],
    queryFn: ({ pageParam = 1 }) => 
      feedApi.getHomeFeed(pageParam),
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.data.results.length < 20) return undefined;
      return allPages.length + 1;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center py-8 text-red-500">
        <AlertCircle size={32} />
        <p className="mt-2">Failed to load feed</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-2 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  const posts = feedData?.pages.flatMap(page => page.data.results) || [];

  return (
    <div className="max-w-4xl mx-auto pt-4 md:pt-8 px-0 md:px-4 flex justify-center gap-8">
      {/* Main Feed Column */}
      <div className="w-full max-w-lg">
        {/* Stories - Implement with real data */}
        {/* Posts */}
        <div className="space-y-4 sm:space-y-6">
          {posts.map((post: Post) => (
            <PostCard 
              key={post.id} 
              post={post}
              onLike={() => feedApi.likePost(post.id)}
              onUnlike={() => feedApi.unlikePost(post.id)}
            />
          ))}
        </div>
        
        {/* Load More */}
        {hasNextPage && (
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="w-full py-3 mt-4 text-center text-gray-500 hover:text-gray-300"
          >
            {isFetchingNextPage ? 'Loading...' : 'Load more'}
          </button>
        )}
      </div>
      
      {/* Sidebar with real suggestions */}
      <UserSuggestions />
    </div>
  );
}
```

---

## Phase 3 - Real-Time Chat & Notifications

### 10. Implement RealtimeProvider (WebSocket)
**Install dependencies:**
```bash
npm install socket.io-client
```

**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/context/RealtimeContext.tsx`

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';

interface RealtimeContextType {
  socket: Socket | null;
  connected: boolean;
  sendMessage: (roomId: string, content: string) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const { accessToken, status } = useAuth();

  useEffect(() => {
    if (status === 'authenticated' && accessToken) {
      const newSocket = io(import.meta.env.VITE_WS_URL, {
        auth: {
          token: accessToken,
        },
      });

      newSocket.on('connect', () => {
        setConnected(true);
        console.log('Connected to WebSocket server');
      });

      newSocket.on('disconnect', () => {
        setConnected(false);
        console.log('Disconnected from WebSocket server');
      });

      newSocket.on('error', (error) => {
        console.error('WebSocket error:', error);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
      };
    }
  }, [accessToken, status]);

  const sendMessage = (roomId: string, content: string) => {
    if (socket && connected) {
      socket.emit('chat_message', {
        room_id: roomId,
        content,
        message_type: 'text'
      });
    }
  };

  const joinRoom = (roomId: string) => {
    if (socket && connected) {
      socket.emit('join_room', { room_id: roomId });
    }
  };

  const leaveRoom = (roomId: string) => {
    if (socket && connected) {
      socket.emit('leave_room', { room_id: roomId });
    }
  };

  return (
    <RealtimeContext.Provider value={{
      socket, connected, sendMessage, joinRoom, leaveRoom
    }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (context === undefined) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}
```

### 11. Wire chat to real-time events
**Update ChatPage.tsx:**
```typescript
import { useRealtime } from '../context/RealtimeContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../services/chatApi';

export function ChatPage() {
  const { sendMessage, joinRoom, leaveRoom } = useRealtime();
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Get conversations
  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getConversations,
  });

  // Get messages for active chat
  const { data: messages = [] } = useQuery({
    queryKey: ['messages', activeChat],
    queryFn: () => activeChat ? chatApi.getMessages(activeChat) : [],
    enabled: !!activeChat,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: ({ roomId, content }: { roomId: string; content: string }) =>
      chatApi.sendMessage(roomId, content),
  });

  // Listen for new messages
  useEffect(() => {
    const socket = useRealtime().socket;
    
    if (socket) {
      socket.on('new_message', (message) => {
        if (message.room_id === activeChat) {
          queryClient.setQueryData(['messages', activeChat], (old: any) => 
            old ? [...old, message] : [message]
          );
        }
      });

      socket.on('typing_indicator', (data) => {
        // Handle typing indicators
      });
    }

    return () => {
      if (socket) {
        socket.off('new_message');
        socket.off('typing_indicator');
      }
    };
  }, [activeChat, queryClient]);

  const handleSendMessage = (content: string) => {
    if (activeChat) {
      sendMessage(activeChat, content);
      sendMessageMutation.mutate({ roomId: activeChat, content });
    }
  };

  // Join/leave rooms
  useEffect(() => {
    if (activeChat) {
      joinRoom(activeChat);
      return () => leaveRoom(activeChat);
    }
  }, [activeChat]);

  return (
    // Chat UI implementation
  );
}
```

### 12. Real-time notifications
**Create NotificationProvider:**
```typescript
// src/context/NotificationContext.tsx
import React, { createContext, useContext, useState } from 'react';
import { useRealtime } from './RealtimeContext';

interface Notification {
  id: string;
  type: 'like' | 'comment' | 'follow' | 'message';
  message: string;
  created_at: string;
  read: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { socket } = useRealtime();

  useEffect(() => {
    if (socket) {
      socket.on('new_notification', (notification) => {
        setNotifications(prev => [notification, ...prev]);
      });
    }

    return () => {
      if (socket) {
        socket.off('new_notification');
      }
    };
  }, [socket]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  return (
    <NotificationContext.Provider value={{
      notifications, unreadCount, markAsRead, markAllAsRead
    }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}
```

---

## Phase 4 - Neural Interface & Analytics

### 13. Category & recommendation UI
**Update ExplorePage.tsx:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { neuralApi } from '../services/neuralApi';

export function ExplorePage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: neuralApi.getCategories,
  });

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', selectedCategory],
    queryFn: () => neuralApi.getRecommendations(20),
    enabled: !!selectedCategory,
  });

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Category tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {categories?.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.name)}
            className={`px-4 py-2 rounded-full whitespace-nowrap ${
              selectedCategory === category.name
                ? 'bg-brand text-white'
                : 'bg-dark-800 text-gray-300'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Recommended users */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations?.map((match) => (
          <UserSuggestionCard
            key={match.user.id}
            user={match.user}
            matchReason={match.match_reason}
            similarityScore={match.similarity_score}
          />
        ))}
      </div>
    </div>
  );
}
```

### 14. Behavioral analytics client
**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/lib/analyticsClient.ts`

```typescript
interface AnalyticsEvent {
  event_type: string;
  payload: Record<string, any>;
  timestamp: string;
}

class AnalyticsClient {
  private eventQueue: AnalyticsEvent[] = [];
  private flushInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.startFlushInterval();
  }

  track(eventType: string, payload: Record<string, any>) {
    const event: AnalyticsEvent = {
      event_type: eventType,
      payload,
      timestamp: new Date().toISOString(),
    };

    this.eventQueue.push(event);

    // Flush immediately for important events
    if (['post_like', 'post_comment', 'user_follow'].includes(eventType)) {
      this.flush();
    }
  }

  private async flush() {
    if (this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL}/analytics/events/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({ events }),
      });
    } catch (error) {
      console.error('Failed to send analytics events:', error);
      // Re-add events to queue on failure
      this.eventQueue.unshift(...events);
    }
  }

  private startFlushInterval() {
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 30000); // Flush every 30 seconds
  }

  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    this.flush(); // Final flush
  }
}

export const analyticsClient = new AnalyticsClient();

// Custom hooks
export const useFeedTracking = () => {
  const trackScroll = () => {
    analyticsClient.track('feed_scroll', {
      scroll_depth: window.scrollY,
      viewport_height: window.innerHeight,
    });
  };

  const trackPostImpression = (postId: string) => {
    analyticsClient.track('post_impression', { post_id: postId });
  };

  return { trackScroll, trackPostImpression };
};

export const usePostTracking = () => {
  const trackLike = (postId: string) => {
    analyticsClient.track('post_like', { post_id: postId });
  };

  const trackComment = (postId: string, content: string) => {
    analyticsClient.track('post_comment', { 
      post_id: postId, 
      comment_length: content.length 
    });
  };

  const trackShare = (postId: string, platform: string) => {
    analyticsClient.track('post_share', { post_id: postId, platform });
  };

  return { trackLike, trackComment, trackShare };
};
```

---

## Phase 5 - UX, Errors & Edge Cases

### 15. Loading, error, and empty states
**Create reusable components:**
```typescript
// src/components/LoadingStates.tsx
export function PostSkeleton() {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <div className="flex items-center mb-4">
        <div className="w-10 h-10 bg-gray-700 rounded-full animate-pulse" />
        <div className="ml-3 flex-1">
          <div className="h-4 bg-gray-700 rounded w-1/3 animate-pulse" />
          <div className="h-3 bg-gray-700 rounded w-1/4 mt-1 animate-pulse" />
        </div>
      </div>
      <div className="h-96 bg-gray-700 rounded animate-pulse" />
      <div className="mt-4 h-4 bg-gray-700 rounded animate-pulse" />
    </div>
  );
}

export function EmptyState({ title, description, action }: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="text-center py-12">
      <div className="text-gray-500 mb-4">
        <div className="w-16 h-16 bg-gray-800 rounded-full mx-auto mb-4" />
        <h3 className="text-lg font-medium">{title}</h3>
        <p className="text-sm mt-1">{description}</p>
      </div>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
```

### 16. Global error boundary
**File:** `frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/src/components/ErrorBoundary.tsx`

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-dark-900">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-4">
              Something went wrong
            </h1>
            <p className="text-gray-400 mb-6">
              We're sorry, but something unexpected happened.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 17. Form validation
**Install dependencies:**
```bash
npm install react-hook-form @hookform/resolvers zod
```

**Update forms with validation:**
```typescript
// src/components/ValidatedLoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function ValidatedLoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const { login } = useAuth();

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
    } catch (error) {
      // Handle login error
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields with validation */}
    </form>
  );
}
```

---

## Phase 6 - Vercel Deployment & Final Checks

### 18. Wire Vite to Vercel
**Update package.json:**
```json
{
  "scripts": {
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

**Create vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

### 19. Configure environment variables on Vercel
**Vercel Dashboard Settings:**
- Go to Project Settings > Environment Variables
- Add production variables:
  - `VITE_API_BASE_URL=https://api.instagran.com`
  - `VITE_WS_URL=wss://ws.instagran.com`
  - `VITE_APP_URL=https://instagran.vercel.app`
  - `VITE_GOOGLE_CLIENT_ID=prod-client-id`

### 20. OAuth redirect URLs
**Google Console Updates:**
- Add `https://instagran.vercel.app/accounts/google/login/callback/`
- Add `https://instagran.vercel.app/` to authorized origins

### 21. Production checklist
**Final verification:**
- [ ] No localhost URLs in production build
- [ ] All API calls use environment variables
- [ ] Authentication flow works end-to-end
- [ ] WebSocket connections established
- [ ] Error handling implemented
- [ ] Loading states for all async operations
- [ ] Responsive design on all devices
- [ ] Lighthouse score > 90
- [ ] No console errors in production

---

## Implementation Order & Dependencies

**Week 1: Phase 0-1**
- Environment setup
- Authentication system
- Protected routing

**Week 2: Phase 2**
- API client setup
- Real data integration
- TanStack Query implementation

**Week 3: Phase 3**
- WebSocket integration
- Real-time chat
- Notifications

**Week 4: Phase 4**
- Neural interface
- Analytics tracking
- Recommendations

**Week 5: Phase 5**
- Error handling
- Loading states
- Form validation

**Week 6: Phase 6**
- Vercel deployment
- Production optimization
- Final testing

---

## Developer Instructions

**To the frontend developer:**

1. **Follow this roadmap in order** - Each phase builds on the previous one
2. **Test each phase thoroughly** before moving to the next
3. **Use the existing UI components** as a foundation
4. **Maintain the current design system** and styling
5. **Implement proper TypeScript types** for all API responses
6. **Add comprehensive error handling** for all user interactions
7. **Optimize for performance** - lazy load components, optimize images
8. **Ensure mobile responsiveness** is maintained throughout

**Backend API Reference:**
- Base URL: `http://localhost:8000/api`
- Authentication: JWT Bearer tokens
- WebSocket: `ws://localhost:3000`
- Documentation: Available at `/api/docs/`

**Success Criteria:**
- All mock data replaced with real API calls
- Authentication flow works seamlessly
- Real-time features functional
- Neural interface integrated
- Production-ready deployment on Vercel

This roadmap provides a clear path from the current UI-only state to a fully functional, production-ready Instagram-like platform integrated with our Django backend and neural features.
