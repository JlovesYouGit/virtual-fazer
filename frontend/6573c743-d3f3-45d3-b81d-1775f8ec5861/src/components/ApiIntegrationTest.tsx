import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { userApi } from '../services/userApi';
import { feedApi } from '../services/feedApi';
import { reelsApi } from '../services/reelsApi';
import { storiesApi } from '../services/storiesApi';
import { chatApi } from '../services/chatApi';
import { socialApi } from '../services/socialApi';
import { useAuth } from '../context/AuthContext';
import { CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react';

interface TestResult {
  name: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  error?: string;
  data?: any;
}

export function ApiIntegrationTest() {
  const { user } = useAuth();
  const [testResults, setTestResults] = useState<TestResult[]>([
    { name: 'User Profile', status: 'pending' },
    { name: 'Feed API', status: 'pending' },
    { name: 'Reels API', status: 'pending' },
    { name: 'Stories API', status: 'pending' },
    { name: 'Chat API', status: 'pending' },
    { name: 'Social API', status: 'pending' },
    { name: 'Reel Forwarding', status: 'pending' },
  ]);

  const updateTestResult = (index: number, result: Partial<TestResult>) => {
    setTestResults(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], ...result };
      return updated;
    });
  };

  // Test User Profile API
  const { refetch: refetchUser } = useQuery({
    queryKey: ['test-user-profile'],
    queryFn: () => userApi.getCurrentUser(),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(0, { status: 'success', data: data.data });
    },
    onError: (error: any) => {
      updateTestResult(0, { status: 'error', error: error.message });
    }
  });

  // Test Feed API
  const { refetch: refetchFeed } = useQuery({
    queryKey: ['test-feed'],
    queryFn: () => feedApi.getHomeFeed(1, 5),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(1, { status: 'success', data: data.data.results.length });
    },
    onError: (error: any) => {
      updateTestResult(1, { status: 'error', error: error.message });
    }
  });

  // Test Reels API
  const { refetch: refetchReels } = useQuery({
    queryKey: ['test-reels'],
    queryFn: () => reelsApi.getReels(1, 5),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(2, { status: 'success', data: data.data.results.length });
    },
    onError: (error: any) => {
      updateTestResult(2, { status: 'error', error: error.message });
    }
  });

  // Test Stories API
  const { refetch: refetchStories } = useQuery({
    queryKey: ['test-stories'],
    queryFn: () => storiesApi.getActiveStories(),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(3, { status: 'success', data: data.data.length });
    },
    onError: (error: any) => {
      updateTestResult(3, { status: 'error', error: error.message });
    }
  });

  // Test Chat API
  const { refetch: refetchChat } = useQuery({
    queryKey: ['test-chat'],
    queryFn: () => chatApi.getInbox(),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(4, { status: 'success', data: data.data.results.length });
    },
    onError: (error: any) => {
      updateTestResult(4, { status: 'error', error: error.message });
    }
  });

  // Test Social API
  const { refetch: refetchSocial } = useQuery({
    queryKey: ['test-social'],
    queryFn: () => socialApi.getNotifications(),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(5, { status: 'success', data: data.data.results.length });
    },
    onError: (error: any) => {
      updateTestResult(5, { status: 'error', error: error.message });
    }
  });

  // Test Reel Forwarding
  const { refetch: refetchForwarding } = useQuery({
    queryKey: ['test-forwarding'],
    queryFn: () => reelsApi.getForwardableUsers(),
    enabled: false,
    onSuccess: (data) => {
      updateTestResult(6, { status: 'success', data: data.data.total_count });
    },
    onError: (error: any) => {
      updateTestResult(6, { status: 'error', error: error.message });
    }
  });

  const runAllTests = async () => {
    // Reset all tests to pending
    setTestResults(prev => prev.map(test => ({ ...test, status: 'pending' as const, error: undefined, data: undefined })));

    // Run all tests in sequence
    updateTestResult(0, { status: 'loading' });
    await refetchUser();

    updateTestResult(1, { status: 'loading' });
    await refetchFeed();

    updateTestResult(2, { status: 'loading' });
    await refetchReels();

    updateTestResult(3, { status: 'loading' });
    await refetchStories();

    updateTestResult(4, { status: 'loading' });
    await refetchChat();

    updateTestResult(5, { status: 'loading' });
    await refetchSocial();

    updateTestResult(6, { status: 'loading' });
    await refetchForwarding();
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'loading':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 bg-gray-500 rounded-full" />;
    }
  };

  const allTestsPassed = testResults.every(test => test.status === 'success');
  const hasErrors = testResults.some(test => test.status === 'error');
  const isLoading = testResults.some(test => test.status === 'loading');

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-gray-400">Please log in to test API integrations</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">API Integration Test</h1>
          <p className="text-gray-400">Test all frontend-backend API connections</p>
        </div>

        {/* Overall Status */}
        <div className={`mb-8 p-4 rounded-lg border ${
          allTestsPassed 
            ? 'bg-green-900/20 border-green-500' 
            : hasErrors 
            ? 'bg-red-900/20 border-red-500'
            : 'bg-gray-800 border-gray-700'
        }`}>
          <div className="flex items-center gap-3">
            {isLoading ? (
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            ) : allTestsPassed ? (
              <CheckCircle className="w-6 h-6 text-green-500" />
            ) : hasErrors ? (
              <XCircle className="w-6 h-6 text-red-500" />
            ) : (
              <div className="w-6 h-6 bg-gray-500 rounded-full" />
            )}
            <div>
              <h3 className="font-semibold">
                {isLoading ? 'Testing APIs...' : allTestsPassed ? 'All APIs Connected!' : 'Some APIs Failed'}
              </h3>
              <p className="text-sm text-gray-400">
                {isLoading 
                  ? 'Running integration tests...'
                  : `${testResults.filter(t => t.status === 'success').length}/${testResults.length} APIs working`
                }
              </p>
            </div>
          </div>
        </div>

        {/* Test Results */}
        <div className="space-y-4 mb-8">
          {testResults.map((test, index) => (
            <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  {getStatusIcon(test.status)}
                  <h4 className="font-medium">{test.name}</h4>
                </div>
                <span className={`text-sm px-2 py-1 rounded ${
                  test.status === 'success' ? 'bg-green-500/20 text-green-400' :
                  test.status === 'error' ? 'bg-red-500/20 text-red-400' :
                  test.status === 'loading' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {test.status.toUpperCase()}
                </span>
              </div>
              
              {test.data && (
                <p className="text-sm text-gray-400">
                  Response: {typeof test.data === 'number' ? `${test.data} items` : 'Success'}
                </p>
              )}
              
              {test.error && (
                <p className="text-sm text-red-400 mt-1">
                  Error: {test.error}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Test Button */}
        <div className="flex justify-center">
          <button
            onClick={runAllTests}
            disabled={isLoading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Testing...
              </>
            ) : (
              'Run All Tests'
            )}
          </button>
        </div>

        {/* Connection Info */}
        <div className="mt-8 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <h4 className="font-medium mb-2">Connection Information</h4>
          <div className="text-sm text-gray-400 space-y-1">
            <p>API Base URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}</p>
            <p>WebSocket URL: {import.meta.env.VITE_WS_URL || 'ws://localhost:3000'}</p>
            <p>Current User: {user?.username} ({user?.email})</p>
          </div>
        </div>
      </div>
    </div>
  );
}
