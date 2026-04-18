import React from 'react';
import { motion } from 'framer-motion';
import { storiesApi, Story } from '../services/storiesApi';

interface StoryRingProps {
  stories: Story[];
  userId: string;
  username: string;
  firstName: string;
  lastName: string;
  avatarUrl?: string;
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  showRing?: boolean;
}

export function StoryRing({ 
  stories, 
  userId, 
  username, 
  firstName, 
  lastName, 
  avatarUrl,
  size = 'medium',
  onClick,
  showRing = true
}: StoryRingProps) {
  const hasActiveStories = stories.length > 0;
  
  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-12 h-12',
    large: 'w-16 h-16'
  };
  
  const ringSizeClasses = {
    small: 'w-10 h-10',
    medium: 'w-14 h-14',
    large: 'w-20 h-20'
  };
  
  const textSizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  if (!hasActiveStories) {
    // No stories - just show avatar
    return (
      <button
        onClick={onClick}
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-700 hover:opacity-80 transition-opacity`}
      >
        {avatarUrl ? (
          <img 
            src={avatarUrl} 
            alt={username}
            className="w-full h-full rounded-full object-cover"
          />
        ) : (
          <span className={`${textSizeClasses[size]} font-medium text-gray-600 dark:text-gray-400`}>
            {firstName.charAt(0)}
          </span>
        )}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className="relative group"
    >
      {/* Story ring */}
      <motion.div
        className={`${ringSizeClasses[size]} rounded-full bg-gradient-to-tr from-pink-500 via-purple-500 to-orange-500 p-0.5 group-hover:scale-105 transition-transform`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Inner circle */}
        <div className={`${sizeClasses[size]} rounded-full bg-white dark:bg-gray-900 flex items-center justify-center`}>
          {avatarUrl ? (
            <img 
              src={avatarUrl} 
              alt={username}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className={`${textSizeClasses[size]} font-medium text-gray-900 dark:text-white`}>
              {firstName.charAt(0)}
            </span>
          )}
        </div>
      </motion.div>
      
      {/* Story count indicator */}
      {stories.length > 1 && (
        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-brand text-white rounded-full flex items-center justify-center text-xs font-medium">
          {stories.length}
        </div>
      )}
      
      {/* Username */}
      <div className="mt-1 text-center">
        <p className={`${textSizeClasses[size]} font-medium text-gray-900 dark:text-white truncate max-w-[60px]`}>
          {username}
        </p>
      </div>
    </button>
  );
}
