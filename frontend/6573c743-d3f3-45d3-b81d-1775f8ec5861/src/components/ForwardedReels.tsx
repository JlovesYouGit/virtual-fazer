import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Send, Bookmark, BookmarkCheck, Play, Pause, Volume2, VolumeX,
  MoreVertical, X, MessageCircle, Heart, Eye
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

interface ForwardedReel {
  id: string;
  reel: {
    id: string;
    creator: {
      id: string;
      username: string;
      first_name: string;
      last_name: string;
    };
    caption: string;
    video_file?: string;
    thumbnail?: string;
    duration: number;
    view_count: number;
    like_count: number;
    comment_count: number;
    created_at: string;
  };
  sender: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  message: string;
  is_saved: boolean;
  created_at: string;
  saved_at?: string;
}

interface ForwardedReelsProps {
  showSaved?: boolean;
}

export function ForwardedReels({ showSaved = false }: ForwardedReelsProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [playingVideo, setPlayingVideo] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(true);
  const videoRefs = React.useRef<{ [key: string]: HTMLVideoElement }>({});

  // Get forwarded reels
  const { data: forwardsData, isLoading } = useQuery({
    queryKey: [showSaved ? 'saved-forwards' : 'received-forwards'],
    queryFn: async () => {
      const endpoint = showSaved ? '/reels/forwards/saved/' : '/reels/forwards/received/';
      const response = await apiClient.get(endpoint);
      return response.data;
    },
  });

  // Save/unsave mutation
  const saveMutation = useMutation({
    mutationFn: async (forwardId: string) => {
      const response = await apiClient.post(`/reels/forwards/${forwardId}/save/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['received-forwards'] });
      queryClient.invalidateQueries({ queryKey: ['saved-forwards'] });
    }
  });

  const unsaveMutation = useMutation({
    mutationFn: async (forwardId: string) => {
      const response = await apiClient.delete(`/reels/forwards/${forwardId}/unsave/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['received-forwards'] });
      queryClient.invalidateQueries({ queryKey: ['saved-forwards'] });
    }
  });

  const forwards = forwardsData?.forwards || [];

  const togglePlayPause = (forwardId: string) => {
    const video = videoRefs.current[forwardId];
    if (video) {
      if (video.paused) {
        video.play();
        setPlayingVideo(forwardId);
      } else {
        video.pause();
        setPlayingVideo(null);
      }
    }
  };

  const toggleMute = (forwardId: string) => {
    const video = videoRefs.current[forwardId];
    if (video) {
      video.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleSave = (forward: ForwardedReel) => {
    if (forward.is_saved) {
      unsaveMutation.mutate(forward.id);
    } else {
      saveMutation.mutate(forward.id);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
      </div>
    );
  }

  if (forwards.length === 0) {
    return (
      <div className="text-center py-8">
        <Send className="mx-auto text-gray-400 mb-2" size={48} />
        <p className="text-gray-500 dark:text-gray-400">
          {showSaved ? 'No saved forwarded reels' : 'No forwarded reels'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {forwards.map((forward: ForwardedReel) => (
        <motion.div
          key={forward.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {forward.sender.first_name.charAt(0)}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {forward.sender.username}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    sent you a reel
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTimeAgo(forward.created_at)}
                </span>
                {forward.is_saved && (
                  <BookmarkCheck className="text-brand" size={16} />
                )}
              </div>
            </div>
            
            {forward.message && (
              <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {forward.message}
                </p>
              </div>
            )}
          </div>

          {/* Reel content */}
          <div className="relative">
            {/* Video player */}
            <div className="relative aspect-[9/16] bg-black">
              {forward.reel.video_file ? (
                <>
                  <video
                    ref={(el) => {
                      if (el) videoRefs.current[forward.id] = el;
                    }}
                    src={forward.reel.video_file}
                    className="w-full h-full object-cover"
                    loop
                    playsInline
                    muted={isMuted}
                    onClick={() => togglePlayPause(forward.id)}
                  />
                  
                  {/* Play/Pause overlay */}
                  {playingVideo !== forward.id && (
                    <div 
                      className="absolute inset-0 flex items-center justify-center cursor-pointer"
                      onClick={() => togglePlayPause(forward.id)}
                    >
                      <div className="w-16 h-16 bg-white/80 rounded-full flex items-center justify-center">
                        <Play size={24} className="text-gray-900 ml-1" />
                      </div>
                    </div>
                  )}
                  
                  {/* Controls */}
                  <div className="absolute bottom-4 right-4 flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleMute(forward.id);
                      }}
                      className="p-2 bg-black/50 rounded-full text-white hover:bg-black/70"
                    >
                      {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                    </button>
                  </div>
                </>
              ) : forward.reel.thumbnail ? (
                <img 
                  src={forward.reel.thumbnail} 
                  alt="Reel thumbnail"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gray-800">
                  <p className="text-white">No media available</p>
                </div>
              )}
            </div>

            {/* Reel info overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent">
              <div className="text-white">
                <p className="font-medium text-sm mb-1">
                  @{forward.reel.creator.username}
                </p>
                <p className="text-sm line-clamp-2">
                  {forward.reel.caption}
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <Eye size={16} />
                  <span className="text-sm">{forward.reel.view_count}</span>
                </div>
                <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <Heart size={16} />
                  <span className="text-sm">{forward.reel.like_count}</span>
                </div>
                <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <MessageCircle size={16} />
                  <span className="text-sm">{forward.reel.comment_count}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleSave(forward)}
                  disabled={saveMutation.isPending || unsaveMutation.isPending}
                  className="p-2 text-gray-500 hover:text-brand transition-colors disabled:opacity-50"
                >
                  {forward.is_saved ? (
                    <BookmarkCheck className="text-brand" size={20} />
                  ) : (
                    <Bookmark size={20} />
                  )}
                </button>
                <button className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                  <MoreVertical size={20} />
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
