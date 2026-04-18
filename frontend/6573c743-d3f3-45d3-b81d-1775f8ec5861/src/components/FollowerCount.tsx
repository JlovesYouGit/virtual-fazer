import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Loader2, UserPlus, UserMinus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { socialApi } from '../services/socialApi';
import { FollowButton } from './FollowButton';

interface FollowerCountProps {
  userId: string;
  initialCount: number;
  className?: string;
  showFollowers?: boolean;
  showFollowing?: boolean;
  variant?: 'default' | 'compact' | 'detailed';
}

interface UserPreview {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  followed_at: string;
}

export function FollowerCount({
  userId,
  initialCount,
  className = '',
  showFollowers = true,
  showFollowing = true,
  variant = 'default'
}: FollowerCountProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [showModal, setShowModal] = useState<'followers' | 'following' | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Get followers
  const {
    data: followersData,
    isLoading: followersLoading,
    error: followersError
  } = useQuery({
    queryKey: ['followers', userId, page],
    queryFn: () => socialApi.getFollowers(userId, { page, page_size: pageSize }),
    enabled: showModal === 'followers'
  });

  // Get following
  const {
    data: followingData,
    isLoading: followingLoading,
    error: followingError
  } = useQuery({
    queryKey: ['following', userId, page],
    queryFn: () => socialApi.getFollowing(userId, { page, page_size: pageSize }),
    enabled: showModal === 'following'
  });

  const handleOpenModal = useCallback((type: 'followers' | 'following') => {
    setShowModal(type);
    setPage(1);
  }, []);

  const handleCloseModal = useCallback(() => {
    setShowModal(null);
    setPage(1);
  }, []);

  const formatCount = (count: number) => {
    if (count < 1000) return count.toString();
    if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
    return `${(count / 1000000).toFixed(1)}M`;
  };

  const renderUserList = (users: UserPreview[], isLoading: boolean, error: any) => {
    if (isLoading) {
      return (
        <div className="flex justify-center py-8">
          <Loader2 className="animate-spin" size={24} />
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-8 text-red-500">
          Failed to load users
        </div>
      );
    }

    if (!users || users.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          No users found
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {users.map((userPreview) => (
          <motion.div
            key={userPreview.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-dark-800 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-brand to-brand-dark rounded-full flex items-center justify-center">
                <span className="text-white font-medium">
                  {userPreview.first_name[0]}{userPreview.last_name[0]}
                </span>
              </div>
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {userPreview.first_name} {userPreview.last_name}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  @{userPreview.username}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                {new Date(userPreview.followed_at).toLocaleDateString()}
              </span>
              <FollowButton
                userId={userPreview.id}
                username={userPreview.username}
                size="sm"
                variant="outline"
              />
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderPagination = (data: any) => {
    if (!data || !data.next && !data.previous) return null;

    return (
      <div className="flex justify-between items-center p-4 border-t border-gray-200 dark:border-dark-700">
        <button
          onClick={() => setPage(page - 1)}
          disabled={!data.previous}
          className="px-3 py-1 text-sm bg-gray-100 dark:bg-dark-700 rounded disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Page {page}
        </span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={!data.next}
          className="px-3 py-1 text-sm bg-gray-100 dark:bg-dark-700 rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    );
  };

  if (variant === 'compact') {
    return (
      <div className={`flex items-center gap-4 ${className}`}>
        {showFollowers && (
          <button
            onClick={() => handleOpenModal('followers')}
            className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <Users size={14} />
            <span>{formatCount(initialCount)}</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <>
      <div className={`flex items-center gap-4 ${className}`}>
        {showFollowers && (
          <motion.button
            onClick={() => handleOpenModal('followers')}
            className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Users size={16} />
            <span className="font-medium">{formatCount(initialCount)}</span>
            <span className="text-xs">followers</span>
          </motion.button>
        )}
        
        {showFollowing && (
          <motion.button
            onClick={() => handleOpenModal('following')}
            className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Users size={16} />
            <span className="font-medium">{formatCount(initialCount)}</span>
            <span className="text-xs">following</span>
          </motion.button>
        )}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={handleCloseModal}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-dark-900 rounded-xl w-full max-w-md max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {showModal === 'followers' ? 'Followers' : 'Following'}
                </h2>
                <button
                  onClick={handleCloseModal}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-dark-800 rounded-full"
                >
                  <X size={20} className="text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="max-h-[60vh] overflow-y-auto">
                {showModal === 'followers' 
                  ? renderUserList(followersData?.results || [], followersLoading, followersError)
                  : renderUserList(followingData?.results || [], followingLoading, followingError)
                }
              </div>

              {/* Pagination */}
              {showModal === 'followers' 
                ? renderPagination(followersData)
                : renderPagination(followingData)
              }
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
