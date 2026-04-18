import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { loginWithTokens } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const code = searchParams.get('code');
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    if (error) {
      setStatus('error');
      setErrorMessage(errorDescription || 'Authentication failed');
      return;
    }

    if (code) {
      // Exchange the authorization code for tokens
      handleGoogleCodeExchange(code);
    } else {
      setStatus('error');
      setErrorMessage('No authorization code received');
    }
  }, [searchParams, navigate, loginWithTokens]);

  const handleGoogleCodeExchange = async (code: string) => {
    try {
      setStatus('loading');
      
      // Exchange the code for tokens with the backend
      const response = await apiClient.post('/auth/google/exchange/', { code });
      
      const { access_token, refresh_token, user } = response.data as {
        access_token: string;
        refresh_token: string;
        user: any;
      };
      
      // Store tokens in localStorage
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Update auth context
      loginWithTokens(access_token, refresh_token, user);
      
      setStatus('success');
      
      // Redirect to feed after successful authentication
      setTimeout(() => {
        navigate('/feed');
      }, 1500);
      
    } catch (error) {
      console.error('Google code exchange failed:', error);
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to exchange authorization code');
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-t-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Processing authentication...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">Authentication Failed</div>
          <p className="text-gray-600">{errorMessage || 'There was an error processing your authentication.'}</p>
          <button
            onClick={() => navigate('/login')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-green-500 text-xl mb-4">Authentication Successful!</div>
        <p className="text-gray-600">You are now logged in. Redirecting...</p>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-t-2 border-green-500 mx-auto mt-4"></div>
      </div>
    </div>
  );
}
