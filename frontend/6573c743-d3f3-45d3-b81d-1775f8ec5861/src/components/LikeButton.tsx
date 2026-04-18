import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Heart, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { socialApi } from '../services/socialApi';

interface LikeButtonProps {
  contentType: 'post' | 'reel';
  contentId: string;
  initialLikesCount: number;
  initialIsLiked: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showCount?: boolean;
  variant?: 'default' | 'minimal' | 'outline';
}

export function LikeButton({
  contentType,
  contentId,
  initialLikesCount,
  initialIsLiked,
  className = '',
  size = 'md',
  showCount = true,
  variant = 'default'
}: LikeButtonProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [likesCount, setLikesCount] = useState(initialLikesCount);
  const [isLiked, setIsLiked] = useState(initialIsLiked);

  // Like mutation
  const likeMutation = useMutation({
    mutationFn: () => socialApi.likeContent(contentType, contentId),
    onSuccess: (data) => {
      setLikesCount(data.like_count);
      setIsLiked(data.is_liked);
      
      // Update cache for content
      queryClient.invalidateQueries({ 
        queryKey: [contentType, contentId] 
      });
    }
  });

  // Unlike mutation
  const unlikeMutation = useMutation({
    mutationFn: () => socialApi.unlikeContent(contentType, contentId),
    onSuccess: (data) => {
      setLikesCount(data.like_count);
      setIsLiked(data.is_liked);
      
      // Update cache for content
      queryClient.invalidateQueries({ 
        queryKey: [contentType, contentId] 
      });
    }
  });

  const handleLike = useCallback(() => {
    if (!user) return;
    
    if (isLiked) {
      unlikeMutation.mutate();
    } else {
      likeMutation.mutate();
    }
  }, [user, isLiked, likeMutation, unlikeMutation]);

  // Loading state
  const isLoading = likeMutation.isPending || unlikeMutation.isPending;

  // Button styling based on variant and state
  const getButtonStyles = () => {
    const baseStyles = 'flex items-center gap-2 font-medium transition-all duration-200 rounded-full';
    
    const sizeStyles = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-3 py-1.5 text-sm',
      lg: 'px-4 py-2 text-base'
    };
    
    if (variant === 'minimal') {
      return `${baseStyles} ${sizeStyles[size]} hover:bg-gray-100 dark:hover:bg-dark-800`;
    }
    
    if (variant === 'outline') {
      return `${baseStyles} ${sizeStyles[size]} ${
        isLiked 
          ? 'bg-red-500 text-white border border-red-500' 
          : 'border border-gray-300 dark:border-dark-600 hover:border-red-500'
      }`;
    }
    
    // default variant
    return `${baseStyles} ${sizeStyles[size]} ${
      isLiked 
        ? 'bg-red-500 text-white hover:bg-red-600' 
        : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-600'
    }`;
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm': return 14;
      case 'lg': return 20;
      default: return 16;
    }
  };

  const getAnimatedIcon = () => {
    const iconSize = getIconSize();
    
    if (isLoading) {
      return <Loader2 size={iconSize} className="animate-spin" />;
    }
    
    return (
      <motion.div
        animate={isLiked ? { scale: [1, 1.2, 1] } : { scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        <Heart 
          size={iconSize} 
          fill={isLiked ? 'currentColor' : 'none'}
          className={isLiked ? 'text-current' : 'text-current'}
        />
      </motion.div>
    );
  };

  const formatCount = (count: number) => {
    if (count < 1000) return count.toString();
    if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
    return `${(count / 1000000).toFixed(1)}M`;
  };

  return (
    <motion.button
      onClick={handleLike}
      disabled={isLoading || !user}
      className={`${getButtonStyles()} ${className}`}
      whileHover={{ scale: isLoading || !user ? 1 : 1.05 }}
      whileTap={{ scale: isLoading || !user ? 1 : 0.95 }}
      transition={{ duration: 0.1 }}
    >
      {getAnimatedIcon()}
      
      {showCount && (
        <motion.span
          key={likesCount}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {formatCount(likesCount)}
        </motion.span>
      )}
      
      {!user && (
        <span className="text-xs opacity-70">Login to like</span>
      )}
    </motion.button>
  );
}
