import React, { useState } from 'react';
import {
  Heart,
  MessageCircle,
  Send,
  Bookmark,
  MoreHorizontal } from
'lucide-react';
import { motion } from 'framer-motion';
interface PostCardProps {
  user: {
    username: string;
    avatarUrl: string;
  };
  imageUrl: string;
  likes: number;
  caption: string;
  timeAgo: string;
}
export function PostCard({
  user,
  imageUrl,
  likes,
  caption,
  timeAgo
}: PostCardProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [likeCount, setLikeCount] = useState(likes);
  const handleLike = () => {
    setIsLiked(!isLiked);
    setLikeCount((prev) => isLiked ? prev - 1 : prev + 1);
  };
  return (
    <div className="bg-dark-900 border-b border-dark-600 sm:border sm:rounded-xl pb-4 sm:mb-6 max-w-lg mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-3 cursor-pointer">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand to-orange-500 p-[2px]">
            <img
              src={user.avatarUrl}
              alt={user.username}
              className="w-full h-full rounded-full border-2 border-dark-900 object-cover" />
            
          </div>
          <span className="font-semibold text-sm hover:text-gray-300">
            {user.username}
          </span>
          <span className="text-gray-500 text-sm">• {timeAgo}</span>
        </div>
        <button className="text-gray-400 hover:text-white p-1">
          <MoreHorizontal size={20} />
        </button>
      </div>

      {/* Image */}
      <div
        className="relative aspect-square sm:aspect-[4/5] bg-dark-800"
        onDoubleClick={handleLike}>
        
        <img
          src={imageUrl}
          alt="Post content"
          className="w-full h-full object-cover" />
        
      </div>

      {/* Actions */}
      <div className="p-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <motion.button
              whileTap={{
                scale: 0.8
              }}
              onClick={handleLike}
              className={`${isLiked ? 'text-brand' : 'text-white hover:text-gray-300'}`}>
              
              <Heart size={24} fill={isLiked ? 'currentColor' : 'none'} />
            </motion.button>
            <button className="text-white hover:text-gray-300">
              <MessageCircle size={24} />
            </button>
            <button className="text-white hover:text-gray-300">
              <Send size={24} />
            </button>
          </div>
          <motion.button
            whileTap={{
              scale: 0.8
            }}
            onClick={() => setIsSaved(!isSaved)}
            className="text-white hover:text-gray-300">
            
            <Bookmark size={24} fill={isSaved ? 'currentColor' : 'none'} />
          </motion.button>
        </div>

        {/* Likes */}
        <div className="font-semibold text-sm mb-1">
          {likeCount.toLocaleString()} likes
        </div>

        {/* Caption */}
        <div className="text-sm mb-1">
          <span className="font-semibold mr-2">{user.username}</span>
          <span>{caption}</span>
        </div>

        {/* Comments */}
        <button className="text-gray-500 text-sm mb-2 hover:text-gray-400">
          View all comments
        </button>

        {/* Add comment */}
        <div className="flex items-center gap-2 mt-2">
          <input
            type="text"
            placeholder="Add a comment..."
            className="bg-transparent text-sm w-full focus:outline-none placeholder-gray-500" />
          
          <button className="text-brand font-semibold text-sm hover:text-brand-hover">
            Post
          </button>
        </div>
      </div>
    </div>);

}