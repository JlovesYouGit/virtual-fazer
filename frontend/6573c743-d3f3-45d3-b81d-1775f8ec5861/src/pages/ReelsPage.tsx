import React, { useState } from 'react';
import { Heart, MessageCircle, Send, MoreHorizontal, Music } from 'lucide-react';
import { motion } from 'framer-motion';
export function ReelsPage() {
  const reels = Array.from({
    length: 5
  }).map((_, i) => ({
    id: i,
    videoUrl: `https://picsum.photos/seed/reel${i}/1080/1920`,
    user: {
      username: `creator_${i + 1}`,
      avatarUrl: `https://picsum.photos/seed/avatar${i}/150/150`
    },
    likes: Math.floor(Math.random() * 50000),
    comments: Math.floor(Math.random() * 1000),
    caption: 'Wait for the end! 🤯 #redbird #viral #trending',
    songName: 'Original Audio - creator_' + (i + 1)
  }));
  return (
    <div className="h-screen w-full bg-black snap-y snap-mandatory overflow-y-scroll no-scrollbar relative">
      {reels.map((reel) =>
      <div
        key={reel.id}
        className="h-screen w-full snap-start relative flex justify-center items-center bg-black">
        
          {/* Video Container (mocked with image) */}
          <div className="relative w-full max-w-lg h-full sm:h-[90vh] sm:rounded-xl overflow-hidden bg-dark-900">
            <img
            src={reel.videoUrl}
            alt="Reel"
            className="w-full h-full object-cover" />
          

            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/80" />

            {/* Content Info (Bottom Left) */}
            <div className="absolute bottom-0 left-0 p-4 w-3/4 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <img
                src={reel.user.avatarUrl}
                alt={reel.user.username}
                className="w-10 h-10 rounded-full border border-white/20" />
              
                <span className="font-semibold text-white">
                  {reel.user.username}
                </span>
                <button className="border border-white text-white px-3 py-1 rounded-lg text-sm font-semibold hover:bg-white/20 transition-colors">
                  Follow
                </button>
              </div>
              <p className="text-white text-sm line-clamp-2">{reel.caption}</p>
              <div className="flex items-center gap-2 text-white text-sm bg-white/20 w-fit px-3 py-1 rounded-full backdrop-blur-sm">
                <Music size={14} />
                <span className="truncate max-w-[150px]">{reel.songName}</span>
              </div>
            </div>

            {/* Actions (Bottom Right) */}
            <div className="absolute bottom-4 right-4 flex flex-col items-center gap-6">
              <div className="flex flex-col items-center gap-1">
                <motion.button
                whileTap={{
                  scale: 0.8
                }}
                className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-brand transition-colors">
                
                  <Heart size={28} />
                </motion.button>
                <span className="text-white text-xs font-semibold">
                  {reel.likes > 1000 ?
                (reel.likes / 1000).toFixed(1) + 'k' :
                reel.likes}
                </span>
              </div>

              <div className="flex flex-col items-center gap-1">
                <button className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-gray-300 transition-colors">
                  <MessageCircle size={28} />
                </button>
                <span className="text-white text-xs font-semibold">
                  {reel.comments}
                </span>
              </div>

              <button className="p-2 bg-black/20 rounded-full backdrop-blur-sm text-white hover:text-gray-300 transition-colors">
                <Send size={28} />
              </button>

              <button className="p-2 text-white hover:text-gray-300 transition-colors">
                <MoreHorizontal size={24} />
              </button>

              <div className="w-10 h-10 rounded-lg border-2 border-white overflow-hidden mt-2">
                <img
                src={reel.user.avatarUrl}
                alt="Audio"
                className="w-full h-full object-cover" />
              
              </div>
            </div>
          </div>
        </div>
      )}
    </div>);

}