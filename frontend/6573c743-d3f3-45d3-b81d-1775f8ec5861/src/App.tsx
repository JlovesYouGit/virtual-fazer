import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { AuthProvider } from './context/AuthContext';
import { RealtimeProvider } from './context/RealtimeContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { FeedPage } from './pages/FeedPage';
import { ProfilePage } from './pages/ProfilePage';
import { ReelsPage } from './pages/ReelsPage';
import { ExplorePage } from './pages/ExplorePage';
import { ChatPage } from './pages/ChatPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
// Import real components with backend integration
import { RealFeedPage } from './components/RealFeedPage';
import { RealChatPage } from './components/RealChatPage';
import { RealNeuralPage } from './components/RealNeuralPage';
import { CreatePostPage } from './components/CreatePostPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <RealtimeProvider>
              <Routes>
                {/* Unauthenticated Routes */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />

                {/* Authenticated Routes with protection */}
                <Route
                  path="/feed"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <RealFeedPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/explore"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <ExplorePage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/reels"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <ReelsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/chat"
                  element={
                    <ProtectedRoute>
                      <RealChatPage />
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <NotificationsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <AnalyticsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/neural"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <RealNeuralPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/create"
                  element={
                    <ProtectedRoute>
                      <CreatePostPage />
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <ProfilePage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/profile/:username"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <ProfilePage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </RealtimeProvider>
          </AuthProvider>
        </BrowserRouter>
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}