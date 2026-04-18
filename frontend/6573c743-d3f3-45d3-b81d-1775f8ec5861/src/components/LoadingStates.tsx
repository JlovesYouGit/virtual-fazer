import React from 'react';
import { Loader2 } from 'lucide-react';

// Post Skeleton Loader
export function PostSkeleton() {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-700 rounded-full"></div>
          <div className="flex-1">
            <div className="h-4 bg-gray-700 rounded w-24 mb-2"></div>
            <div className="h-3 bg-gray-700 rounded w-16"></div>
          </div>
        </div>
        <div className="w-5 h-5 bg-gray-700 rounded"></div>
      </div>

      {/* Content */}
      <div className="h-96 bg-gray-700 rounded-lg mb-4"></div>

      {/* Actions */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-4">
          <div className="w-5 h-5 bg-gray-700 rounded"></div>
          <div className="w-5 h-5 bg-gray-700 rounded"></div>
          <div className="w-5 h-5 bg-gray-700 rounded"></div>
        </div>
        <div className="w-5 h-5 bg-gray-700 rounded"></div>
      </div>

      {/* Caption */}
      <div className="space-y-2">
        <div className="h-4 bg-gray-700 rounded w-3/4"></div>
        <div className="h-4 bg-gray-700 rounded w-1/2"></div>
      </div>
    </div>
  );
}

// User Profile Skeleton
export function UserProfileSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Header */}
      <div className="h-32 bg-gradient-to-r from-gray-700 to-gray-600"></div>
      
      {/* Profile Info */}
      <div className="px-6 pb-6">
        <div className="flex items-end -mt-16 mb-4">
          <div className="w-32 h-32 bg-gray-700 rounded-full border-4 border-dark-900"></div>
          <div className="ml-auto mt-4">
            <div className="h-10 bg-gray-700 rounded w-32"></div>
          </div>
        </div>
        
        <div className="space-y-3">
          <div className="h-6 bg-gray-700 rounded w-48"></div>
          <div className="h-4 bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
        </div>
        
        {/* Stats */}
        <div className="flex justify-around py-4 mt-6 border-t border-gray-700">
          <div className="text-center">
            <div className="h-6 bg-gray-700 rounded w-8 mx-auto mb-1"></div>
            <div className="h-3 bg-gray-700 rounded w-16"></div>
          </div>
          <div className="text-center">
            <div className="h-6 bg-gray-700 rounded w-8 mx-auto mb-1"></div>
            <div className="h-3 bg-gray-700 rounded w-12"></div>
          </div>
          <div className="text-center">
            <div className="h-6 bg-gray-700 rounded w-8 mx-auto mb-1"></div>
            <div className="h-3 bg-gray-700 rounded w-20"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Chat Skeleton
export function ChatSkeleton() {
  return (
    <div className="flex h-screen">
      {/* Conversations Sidebar */}
      <div className="w-80 border-r border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <div className="h-6 bg-gray-700 rounded w-32 mb-3"></div>
          <div className="h-10 bg-gray-700 rounded w-full"></div>
        </div>
        
        <div className="space-y-2 p-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 p-3 animate-pulse">
              <div className="w-12 h-12 bg-gray-700 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-700 rounded w-24 mb-2"></div>
                <div className="h-3 bg-gray-700 rounded w-32"></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-700 rounded-full"></div>
            <div className="flex-1">
              <div className="h-5 bg-gray-700 rounded w-32 mb-1"></div>
              <div className="h-3 bg-gray-700 rounded w-24"></div>
            </div>
          </div>
        </div>
        
        <div className="flex-1 p-6 space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-xs p-3 rounded-2xl bg-gray-700 h-16 w-32 animate-pulse`}></div>
            </div>
          ))}
        </div>
        
        <div className="px-6 py-4 border-t border-gray-700">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-10 bg-gray-700 rounded-full"></div>
            <div className="w-10 h-10 bg-gray-700 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Feed Skeleton
export function FeedSkeleton() {
  return (
    <div className="max-w-4xl mx-auto pt-4 md:pt-8 px-0 md:px-4 flex justify-center gap-8">
      <div className="w-full max-w-lg space-y-4">
        {/* Stories */}
        <div className="mb-6 bg-dark-900 sm:bg-dark-800 sm:border border-dark-600 sm:rounded-xl p-4">
          <div className="flex gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex flex-col items-center">
                <div className="w-16 h-16 bg-gray-700 rounded-full animate-pulse"></div>
                <div className="h-3 bg-gray-700 rounded w-16 mt-2"></div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Posts */}
        {Array.from({ length: 3 }).map((_, i) => (
          <PostSkeleton key={i} />
        ))}
      </div>
      
      {/* Sidebar */}
      <div className="hidden lg:block w-80">
        <div className="space-y-4">
          {/* User Profile */}
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 bg-gray-700 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-700 rounded w-24 mb-1"></div>
                <div className="h-3 bg-gray-700 rounded w-32"></div>
              </div>
            </div>
          </div>
          
          {/* Suggestions */}
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
            <div className="h-5 bg-gray-700 rounded w-32 mb-4"></div>
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-700 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-700 rounded w-20 mb-1"></div>
                    <div className="h-3 bg-gray-700 rounded w-24"></div>
                  </div>
                </div>
                <div className="h-8 bg-gray-700 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Generic Loading Spinner
export function LoadingSpinner({ size = 'medium', text }: { size?: 'small' | 'medium' | 'large'; text?: string }) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <Loader2 className={`animate-spin text-brand ${sizeClasses[size]}`} />
      {text && <p className="mt-2 text-gray-400 text-sm">{text}</p>}
    </div>
  );
}

// Full Page Loader
export function FullPageLoader({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900">
      <div className="text-center">
        <LoadingSpinner size="large" />
        <p className="mt-4 text-gray-400">{text}</p>
      </div>
    </div>
  );
}

// Empty State Component
export function EmptyState({ 
  title, 
  description, 
  action,
  icon 
}: { 
  title: string; 
  description: string; 
  action?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div className="text-center py-12">
      {icon && (
        <div className="w-16 h-16 bg-gray-800 rounded-full mx-auto mb-4 flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 mb-4">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// Error State Component
export function ErrorState({ 
  title = 'Something went wrong', 
  description = 'Please try again later', 
  onRetry,
  icon 
}: { 
  title?: string; 
  description?: string; 
  onRetry?: () => void;
  icon?: React.ReactNode;
}) {
  return (
    <div className="text-center py-12">
      {icon && (
        <div className="w-16 h-16 bg-red-500/20 rounded-full mx-auto mb-4 flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 mb-4">{description}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
