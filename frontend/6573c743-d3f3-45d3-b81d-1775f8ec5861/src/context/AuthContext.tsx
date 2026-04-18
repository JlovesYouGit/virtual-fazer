import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient, ApiError } from '../lib/apiClient';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  is_verified: boolean;
  date_joined: string;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  status: 'idle' | 'authenticating' | 'authenticated' | 'unauthenticated';
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  loginWithTokens: (accessToken: string, refreshToken: string, user: User) => void;
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
  const [isLoading, setIsLoading] = useState(true);

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
      if (error instanceof ApiError) {
        throw new Error(error.message);
      }
      throw new Error('Login failed. Please try again.');
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
      if (error instanceof ApiError) {
        throw new Error(error.message);
      }
      throw new Error('Google login failed. Please try again.');
    }
  };

  const loginWithTokens = (accessToken: string, refreshToken: string, user: User) => {
    setAccessToken(accessToken);
    setRefreshToken(refreshToken);
    setUser(user);
    setStatus('authenticated');
    
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const logout = async () => {
    try {
      // Call logout endpoint if available (skip for guests)
      if (!localStorage.getItem('isGuest')) {
        await apiClient.post('/auth/logout/');
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    }
    
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    setStatus('unauthenticated');
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    localStorage.removeItem('isGuest');
  };

  const refreshTokens = async () => {
    try {
      const token = refreshToken || localStorage.getItem('refreshToken');
      if (!token) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/auth/refresh/', {
        refresh: token,
      });
      const { access, refresh: newRefresh } = response.data;
      
      setAccessToken(access);
      if (newRefresh) {
        setRefreshToken(newRefresh);
        localStorage.setItem('refreshToken', newRefresh);
      }
      
      localStorage.setItem('accessToken', access);
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      throw error;
    }
  };

  const bootstrap = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('accessToken');
      const refresh = localStorage.getItem('refreshToken');
      const userData = localStorage.getItem('user');
      const isGuest = localStorage.getItem('isGuest');
      
      // Handle guest users
      if (isGuest === 'true' && userData) {
        const guestUser = JSON.parse(userData);
        setUser(guestUser);
        setStatus('authenticated');
        setIsLoading(false);
        return;
      }
      
      if (token && refresh && userData) {
        // Validate token by making a request to get current user
        try {
          const response = await apiClient.get('/users/profile/');
          const currentUser = response.data;
          
          setAccessToken(token);
          setRefreshToken(refresh);
          setUser(currentUser);
          setStatus('authenticated');
        } catch (error) {
          if (error instanceof ApiError && error.status === 401) {
            // Token is invalid, try to refresh
            try {
              await refreshTokens();
              // After successful refresh, get user data
              const response = await apiClient.get('/users/profile/');
              const currentUser = response.data;
              setUser(currentUser);
              setStatus('authenticated');
            } catch (refreshError) {
              // Refresh failed, clear everything
              await logout();
            }
          } else {
            await logout();
          }
        }
      } else {
        setStatus('unauthenticated');
      }
    } catch (error) {
      console.error('Bootstrap error:', error);
      await logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
  }, []);

  const value: AuthContextType = {
    user,
    accessToken,
    refreshToken,
    status,
    isLoading,
    login,
    loginWithGoogle,
    loginWithTokens,
    logout,
    refreshTokens,
    bootstrap,
  };

  return (
    <AuthContext.Provider value={value}>
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
