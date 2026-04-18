import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { UserPlus, UserMinus, Loader2, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { socialApi } from '../services/socialApi';

interface FollowButtonProps {
  userId: string;
  username: string;
  initialIsFollowing?: boolean;
  initialFollowRequestSent?: boolean;
  isPrivate?: boolean;
  className?: string;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export function FollowButton({
  userId,
  username,
  initialIsFollowing = false,
  initialFollowRequestSent = false,
  isPrivate = false,
  className = '',
  variant = 'primary',
  size = 'md'
}: FollowButtonProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [followRequestSent, setFollowRequestSent] = useState(initialFollowRequestSent);

  // Follow mutation
  const followMutation = useMutation({
    mutationFn: (message?: string) => socialApi.followUser(userId, message),
    onSuccess: (data) => {
      if (data.request_id) {
        // Follow request sent for private account
        setFollowRequestSent(true);
        setIsFollowing(false);
      } else {
        // Direct follow for public account
        setIsFollowing(true);
        setFollowRequestSent(false);
        
        // Update user profile cache
        queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
        queryClient.invalidateQueries({ queryKey: ['currentUserProfile'] });
      }
    }
  });

  // Unfollow mutation
  const unfollowMutation = useMutation({
    mutationFn: () => socialApi.unfollowUser(userId),
    onSuccess: () => {
      setIsFollowing(false);
      setFollowRequestSent(false);
      
      // Update user profile cache
      queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
      queryClient.invalidateQueries({ queryKey: ['currentUserProfile'] });
    }
  });

  const handleFollow = useCallback(() => {
    if (!user || userId === user.id) return;
    
    if (isFollowing) {
      unfollowMutation.mutate();
    } else {
      followMutation.mutate();
    }
  }, [user, userId, isFollowing, followMutation, unfollowMutation]);

  // Don't show follow button for own profile
  if (user && userId === user.id) {
    return null;
  }

  // Loading state
  const isLoading = followMutation.isPending || unfollowMutation.isPending;

  // Button styling based on variant and state
  const getButtonStyles = () => {
    const baseStyles = 'flex items-center gap-2 font-medium transition-all duration-200 rounded-full';
    
    const sizeStyles = {
      sm: 'px-3 py-1 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base'
    };
    
    if (followRequestSent) {
      return `${baseStyles} ${sizeStyles[size]} bg-gray-200 text-gray-600 hover:bg-gray-300`;
    }
    
    if (isFollowing) {
      return `${baseStyles} ${sizeStyles[size]} bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300`;
    }
    
    const variantStyles = {
      primary: `${baseStyles} ${sizeStyles[size]} bg-brand text-white hover:bg-brand-hover`,
      secondary: `${baseStyles} ${sizeStyles[size]} bg-dark-700 text-white hover:bg-dark-600`,
      outline: `${baseStyles} ${sizeStyles[size]} border border-brand text-brand hover:bg-brand hover:text-white`
    };
    
    return variantStyles[variant];
  };

  const getIcon = () => {
    if (isLoading) {
      return <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" />;
    }
    
    if (followRequestSent) {
      return <Check size={size === 'sm' ? 14 : 16} />;
    }
    
    if (isFollowing) {
      return <UserMinus size={size === 'sm' ? 14 : 16} />;
    }
    
    return <UserPlus size={size === 'sm' ? 14 : 16} />;
  };

  const getText = () => {
    if (isLoading) {
      return isFollowing ? 'Unfollowing...' : 'Following...';
    }
    
    if (followRequestSent) {
      return 'Requested';
    }
    
    if (isFollowing) {
      return 'Following';
    }
    
    return 'Follow';
  };

  return (
    <motion.button
      onClick={handleFollow}
      disabled={isLoading}
      className={`${getButtonStyles()} ${className}`}
      whileHover={{ scale: isLoading ? 1 : 1.02 }}
      whileTap={{ scale: isLoading ? 1 : 0.98 }}
      transition={{ duration: 0.1 }}
    >
      {getIcon()}
      <span>{getText()}</span>
    </motion.button>
  );
}
