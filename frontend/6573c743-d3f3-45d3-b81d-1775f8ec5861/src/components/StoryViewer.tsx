import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { 
  ChevronLeft, ChevronRight, X, Heart, MessageCircle, Send, 
  MoreVertical, Eye, Clock, Pause, Play, Volume2, VolumeX
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { storiesApi, Story, StoryReply, StoryView } from '../services/storiesApi';

interface StoryViewerProps {
  stories: Story[];
  initialIndex?: number;
  onClose: () => void;
  onUserClick?: (userId: string) => void;
}

export function StoryViewer({ 
  stories, 
  initialIndex = 0, 
  onClose, 
  onUserClick 
}: StoryViewerProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [progress, setProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [showActions, setShowActions] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  const currentStory = stories[currentIndex];

  // View story mutation
  const viewStoryMutation = useMutation({
    mutationFn: storiesApi.viewStory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] });
    }
  });

  // Like story mutation
  const likeStoryMutation = useMutation({
    mutationFn: storiesApi.likeStory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] });
    }
  });

  // Reply to story mutation
  const replyMutation = useMutation({
    mutationFn: ({ storyId, data }: { storyId: string; data: { content: string } }) =>
      storiesApi.replyToStory(storyId, data),
    onSuccess: () => {
      setReplyText('');
      setShowReplyInput(false);
      queryClient.invalidateQueries({ queryKey: ['stories'] });
    }
  });

  // Progress bar animation
  useEffect(() => {
    if (!currentStory || isPaused) return;

    const duration = currentStory.content_type === 'video' ? 15000 : 5000; // 15s for video, 5s for image/text
    const interval = 50; // Update every 50ms
    const increment = (interval / duration) * 100;

    progressIntervalRef.current = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          // Move to next story
          handleNext();
          return 0;
        }
        return newProgress;
      });
    }, interval);

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [currentStory, isPaused]);

  // Reset progress when story changes
  useEffect(() => {
    setProgress(0);
    setIsPaused(false);
    setShowReplyInput(false);
    setShowActions(false);
    
    // Auto-view story
    if (currentStory) {
      viewStoryMutation.mutate(currentStory.id);
    }
  }, [currentIndex]);

  // Handle video playback
  useEffect(() => {
    if (currentStory?.content_type === 'video' && videoRef.current) {
      const video = videoRef.current;
      
      if (isPaused) {
        video.pause();
      } else {
        video.play().catch(e => console.log('Video play failed:', e));
      }
    }
  }, [isPaused, currentStory]);

  const handleNext = useCallback(() => {
    if (currentIndex < stories.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      onClose();
    }
  }, [currentIndex, stories.length, onClose]);

  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  }, [currentIndex]);

  const handlePan = useCallback((event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const { offset, velocity } = info;
    
    if (Math.abs(offset.x) > 50 || Math.abs(velocity.x) > 500) {
      if (offset.x > 0) {
        handlePrevious();
      } else {
        handleNext();
      }
    }
  }, [handleNext, handlePrevious]);

  const handleLike = useCallback(() => {
    if (currentStory) {
      likeStoryMutation.mutate(currentStory.id);
    }
  }, [currentStory, likeStoryMutation]);

  const handleReply = useCallback(() => {
    setShowReplyInput(true);
    setIsPaused(true);
  }, []);

  const handleSendReply = useCallback(() => {
    if (replyText.trim() && currentStory) {
      replyMutation.mutate({
        storyId: currentStory.id,
        data: { content: replyText.trim() }
      });
    }
  }, [replyText, currentStory, replyMutation]);

  const handleUserClick = useCallback(() => {
    if (onUserClick && currentStory) {
      onUserClick(currentStory.user.id);
    }
  }, [onUserClick, currentStory]);

  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  const renderStoryContent = () => {
    if (!currentStory) return null;

    switch (currentStory.content_type) {
      case 'image':
        return (
          <img
            src={currentStory.media_url}
            alt="Story"
            className="w-full h-full object-contain"
          />
        );
      
      case 'video':
        return (
          <div className="relative w-full h-full">
            <video
              ref={videoRef}
              src={currentStory.media_url}
              className="w-full h-full object-contain"
              muted={isMuted}
              loop
              playsInline
            />
            <button
              onClick={toggleMute}
              className="absolute bottom-4 right-4 p-2 bg-black/50 rounded-full text-white"
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
          </div>
        );
      
      case 'text':
        return (
          <div 
            className="w-full h-full flex items-center justify-center p-8"
            style={{ 
              backgroundColor: currentStory.background_color,
              color: currentStory.text_color 
            }}
          >
            <p className="text-2xl font-medium text-center">
              {currentStory.text_content}
            </p>
          </div>
        );
      
      default:
        return (
          <div className="w-full h-full flex items-center justify-center bg-gray-900 text-white">
            <p className="text-lg">Unsupported story type</p>
          </div>
        );
    }
  };

  const formatTimeRemaining = () => {
    if (!currentStory) return '';
    
    const { hours, minutes, seconds } = currentStory.time_remaining;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m left`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s left`;
    } else {
      return `${seconds}s left`;
    }
  };

  if (!currentStory) return null;

  return (
    <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/50 to-transparent p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            >
              <X size={24} />
            </button>
            
            <div className="flex items-center gap-3">
              {/* Progress bars */}
              <div className="flex gap-1">
                {stories.map((story, index) => (
                  <div
                    key={story.id}
                    className="h-1 bg-white/30 rounded-full overflow-hidden"
                    style={{ width: '60px' }}
                  >
                    <motion.div
                      className="h-full bg-white"
                      initial={{ width: 0 }}
                      animate={{ 
                        width: index < currentIndex ? '100%' : 
                               index === currentIndex ? `${progress}%` : '0%'
                      }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                ))}
              </div>
              
              {/* User info */}
              <button
                onClick={handleUserClick}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-pink-500 to-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {currentStory.user.first_name.charAt(0)}
                  </span>
                </div>
                <div className="text-white">
                  <p className="font-medium text-sm">{currentStory.user.username}</p>
                  <p className="text-xs opacity-80">{formatTimeRemaining()}</p>
                </div>
              </button>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            >
              {isPaused ? <Play size={20} /> : <Pause size={20} />}
            </button>
            
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            >
              <MoreVertical size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Story Content */}
      <motion.div
        ref={containerRef}
        className="relative w-full h-full max-w-md max-h-screen cursor-grab active:cursor-grabbing"
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.2}
        onDragEnd={handlePan}
        onTap={() => setIsPaused(!isPaused)}
      >
        {renderStoryContent()}
        
        {/* Navigation hints */}
        {currentIndex > 0 && (
          <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/50">
            <ChevronLeft size={32} />
          </div>
        )}
        
        {currentIndex < stories.length - 1 && (
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/50">
            <ChevronRight size={32} />
          </div>
        )}
      </motion.div>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-black/50 to-transparent p-4">
        {/* Caption */}
        {currentStory.caption && (
          <div className="mb-4 text-white">
            <p className="text-sm">{currentStory.caption}</p>
            
            {/* Hashtags */}
            {currentStory.hashtags_list.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {currentStory.hashtags_list.map((tag, index) => (
                  <span key={index} className="text-blue-400 text-sm">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleLike}
              className="flex items-center gap-1 text-white hover:scale-110 transition-transform"
            >
              <Heart 
                size={24} 
                className={currentStory.is_liked ? 'fill-red-500 text-red-500' : ''} 
              />
              <span className="text-sm">{currentStory.likes_count}</span>
            </button>
            
            <button
              onClick={handleReply}
              className="flex items-center gap-1 text-white hover:scale-110 transition-transform"
            >
              <MessageCircle size={24} />
              <span className="text-sm">{currentStory.replies_count}</span>
            </button>
            
            <button className="text-white hover:scale-110 transition-transform">
              <Eye size={24} />
              <span className="text-sm ml-1">{currentStory.view_count}</span>
            </button>
          </div>
          
          {/* Time */}
          <div className="flex items-center gap-1 text-white/80 text-sm">
            <Clock size={16} />
            <span>{formatTimeRemaining()}</span>
          </div>
        </div>
        
        {/* Reply Input */}
        <AnimatePresence>
          {showReplyInput && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="mt-4 flex items-center gap-2"
            >
              <input
                type="text"
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Send a reply..."
                className="flex-1 px-4 py-2 bg-white/20 border border-white/30 rounded-full text-white placeholder-white/60 focus:outline-none focus:border-white/60"
                autoFocus
              />
              <button
                onClick={handleSendReply}
                disabled={!replyText.trim() || replyMutation.isPending}
                className="p-2 bg-white text-black rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={20} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Actions Menu */}
      <AnimatePresence>
        {showActions && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute top-20 right-4 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20"
          >
            <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2">
              <Eye size={16} />
              Viewers ({currentStory.viewer_count})
            </button>
            <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2">
              <Share size={16} />
              Share
            </button>
            {currentStory.user.id === user?.id && (
              <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-500">
                <Trash2 size={16} />
                Delete
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
