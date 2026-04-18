import React, { useState, useRef, useEffect } from 'react';
import { Heart, MessageCircle, Send, MoreHorizontal, Music, Loader2, AlertCircle } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { reelsApi, Reel } from '../services/reelsApi';
import { useAuth } from '../context/AuthContext';

export function ReelsPage() {
  const { user } = useAuth();
  const [activeReelIndex, setActiveReelIndex] = useState(0);
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);

  // Fetch real reels from backend
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['reels'],
    queryFn: () => reelsApi.getReels(1, 10),
  });

  // Like mutation
  const likeMutation = useMutation({
    mutationFn: (reelId: string) => reelsApi.likeReel(reelId),
    onSuccess: () => refetch(),
  });

  // Unlike mutation
  const unlikeMutation = useMutation({
    mutationFn: (reelId: string) => reelsApi.unlikeReel(reelId),
    onSuccess: () => refetch(),
  });

  const reels = data?.data.results || [];

  // Handle scroll to update active reel
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    const windowHeight = window.innerHeight;
    const newIndex = Math.round(scrollTop / windowHeight);
    setActiveReelIndex(newIndex);
  };

  // Play/pause videos based on active reel
  useEffect(() => {
    videoRefs.current.forEach((video, index) => {
      if (video) {
        if (index === activeReelIndex) {
          video.play().catch(() => {});
        } else {
          video.pause();
        }
      }
    });
  }, [activeReelIndex]);

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const handleLike = (reel: Reel) => {
    if (reel.is_liked) {
      unlikeMutation.mutate(reel.id);
    } else {
      likeMutation.mutate(reel.id);
    }
  };

  if (isLoading) {
    return (
      <div className="h-screen w-full bg-black flex items-center justify-center">
        <Loader2 className="animate-spin text-white" size={48} />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="h-screen w-full bg-black flex flex-col items-center justify-center text-white">
        <AlertCircle size={48} className="text-red-500 mb-4" />
        <p className="text-xl mb-2">Failed to load reels</p>
        <p className="text-gray-400 mb-4">{error?.message || 'Unknown error'}</p>
        <button 
          onClick={() => refetch()} 
          className="px-6 py-2 bg-brand rounded-lg hover:bg-brand-hover transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (reels.length === 0) {
    return (
      <div className="h-screen w-full bg-black flex flex-col items-center justify-center text-white">
        <div className="text-6xl mb-4">🎬</div>
        <p className="text-xl mb-2">No reels yet</p>
        <p className="text-gray-400">Be the first to create a reel!</p>
      </div>
    );
  }

  return (
    <div 
      className="h-screen w-full bg-black snap-y snap-mandatory overflow-y-scroll no-scrollbar relative"
      onScroll={handleScroll}
    >
      {reels.map((reel, index) => (
        <div
          key={reel.id}
          className="h-screen w-full snap-start relative flex justify-center items-center bg-black"
        >
          {/* Video Container */}
          <div className="relative w-full max-w-lg h-full sm:h-[90vh] sm:rounded-xl overflow-hidden bg-dark-900">
            {reel.video_file ? (
              <video
                ref={(el) => { videoRefs.current[index] = el; }}
                src={reel.video_file}
                className="w-full h-full object-cover"
                loop
                muted
                playsInline
                poster={reel.thumbnail}
              />
            ) : reel.thumbnail ? (
              <img
                src={reel.thumbnail}
                alt={reel.caption}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-dark-800 text-gray-500">
                <div className="text-center">
                  <div className="text-4xl mb-2">🎬</div>
                  <p>No video available</p>
                </div>
              </div>
            )}

            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/80" />

            {/* Content Info (Bottom Left) */}
            <div className="absolute bottom-0 left-0 p-4 w-3/4 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full border border-white/20 bg-dark-700 flex items-center justify-center overflow-hidden">
                  {reel.creator?.avatar_url ? (
                    <img
                      src={reel.creator.avatar_url}
                      alt={reel.creator.username}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-white text-lg">👤</span>
                  )}
                </div>
                <span className="font-semibold text-white">
                  {reel.creator?.username || 'Unknown'}
                </span>
                <button className="border border-white text-white px-3 py-1 rounded-lg text-sm font-semibold hover:bg-white/20 transition-colors">
                  Follow
                </button>
              </div>
              <p className="text-white text-sm line-clamp-2">{reel.caption}</p>
              {reel.music_track && (
                <div className="flex items-center gap-2 text-white text-sm bg-white/20 w-fit px-3 py-1 rounded-full backdrop-blur-sm">
                  <Music size={14} />
                  <span className="truncate max-w-[150px]">{reel.music_track}</span>
                </div>
              )}
            </div>

            {/* Actions (Bottom Right) */}
            <div className="absolute bottom-4 right-4 flex flex-col items-center gap-6">
              <button 
                onClick={() => handleLike(reel)}
                className={`p-2 rounded-full backdrop-blur-sm transition-colors ${
                  reel.is_liked ? 'text-red-500' : 'text-white hover:text-gray-300'
                }`}
              >
                <Heart size={28} fill={reel.is_liked ? "currentColor" : "none"} />
                <span className="text-white text-sm mt-1 block">{formatNumber(reel.like_count)}</span>
              </button>
              
              <button className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-gray-300 transition-colors">
                <MessageCircle size={28} />
                <span className="text-white text-sm mt-1 block">{formatNumber(reel.comment_count)}</span>
              </button>
              
              <button className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-gray-300 transition-colors">
                <Send size={28} />
                <span className="text-white text-sm mt-1 block">{formatNumber(reel.share_count)}</span>
              </button>
              
              <button className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-gray-300 transition-colors">
                <MoreHorizontal size={28} />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
