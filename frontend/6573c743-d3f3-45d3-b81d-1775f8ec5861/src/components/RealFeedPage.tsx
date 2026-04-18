import React from 'react';
import { useQuery, useMutation, useInfiniteQuery } from '@tanstack/react-query';
import { feedApi, Post } from '../services/feedApi';
import { useAuth } from '../context/AuthContext';
import { Loader2, AlertCircle, Heart, MessageCircle, Send, Bookmark } from 'lucide-react';
import { motion } from 'framer-motion';

export function RealFeedPage() {
  const { user } = useAuth();

  // Infinite scroll feed with real backend data
  const {
    data: feedData,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch
  } = useInfiniteQuery({
    queryKey: ['homeFeed'],
    queryFn: ({ pageParam = 1 }) => 
      feedApi.getHomeFeed(pageParam),
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.data.results.length < 20) return undefined;
      return allPages.length + 1;
    },
    enabled: !!user, // Only fetch when authenticated
  });

  // Like mutation with real backend
  const likeMutation = useMutation({
    mutationFn: (postId: string) => feedApi.likePost(postId),
    onSuccess: () => {
      // Optimistically update the cache
      refetch();
    },
    onError: (error) => {
      console.error('Failed to like post:', error);
    }
  });

  // Unlike mutation with real backend
  const unlikeMutation = useMutation({
    mutationFn: (postId: string) => feedApi.unlikePost(postId),
    onSuccess: () => {
      refetch();
    },
    onError: (error) => {
      console.error('Failed to unlike post:', error);
    }
  });

  const posts = feedData?.pages.flatMap(page => page.data.results) || [];

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center py-8 text-red-500">
        <AlertCircle size={32} />
        <p className="mt-2">Failed to load feed</p>
        <p className="text-sm mt-1 text-gray-400">{error?.message || 'Unknown error'}</p>
        <button 
          onClick={() => refetch()}
          className="mt-2 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">
          <div className="w-16 h-16 bg-gray-800 rounded-full mx-auto mb-4" />
          <h3 className="text-lg font-medium">No posts yet</h3>
          <p className="text-sm mt-1">Follow some users to see their posts here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto pt-4 md:pt-8 px-0 md:px-4 flex justify-center gap-8">
      {/* Main Feed Column */}
      <div className="w-full max-w-lg">
        {/* Stories - Real backend data */}
        <div className="mb-6 bg-dark-900 sm:bg-dark-800 sm:border border-dark-600 sm:rounded-xl p-4 overflow-x-auto no-scrollbar flex gap-4">
          {/* Your Story */}
          <div className="flex flex-col items-center cursor-pointer">
            <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 p-0.5">
              <div className="w-full h-full rounded-full bg-dark-900 p-0.5">
                <img
                  src={user?.profile_image || `https://picsum.photos/seed/${user?.username}/150/150`}
                  alt="Your Story"
                  className="w-full h-full rounded-full object-cover"
                />
              </div>
            </div>
            <span className="text-xs mt-1 text-white">Your Story</span>
          </div>
        </div>

        {/* Real Posts from Backend */}
        <div className="space-y-4 sm:space-y-6">
          {posts.map((post: Post) => (
            <RealPostCard 
              key={post.id} 
              post={post}
              onLike={() => likeMutation.mutate(post.id)}
              onUnlike={() => unlikeMutation.mutate(post.id)}
              isLiking={likeMutation.isLoading}
              isUnliking={unlikeMutation.isLoading}
            />
          ))}
        </div>
        
        {/* Load More Button */}
        {hasNextPage && (
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="w-full py-3 mt-4 text-center text-gray-500 hover:text-gray-300 disabled:opacity-50"
          >
            {isFetchingNextPage ? 'Loading...' : 'Load more'}
          </button>
        )}
      </div>
    </div>
  );
}

// Real Post Card Component with Backend Integration
function RealPostCard({ 
  post, 
  onLike, 
  onUnlike, 
  isLiking, 
  isUnliking 
}: {
  post: Post;
  onLike: () => void;
  onUnlike: () => void;
  isLiking: boolean;
  isUnliking: boolean;
}) {
  const [isLiked, setIsLiked] = React.useState(post.is_liked);
  const [likeCount, setLikeCount] = React.useState(post.likes_count);

  const handleLike = () => {
    if (isLiked) {
      setIsLiked(false);
      setLikeCount(prev => prev - 1);
      onUnlike();
    } else {
      setIsLiked(true);
      setLikeCount(prev => prev + 1);
      onLike();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark-800 border border-dark-600 rounded-xl"
    >
      {/* Post Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <img
            src={post.user.avatar_url}
            alt={post.user.username}
            className="w-10 h-10 rounded-full object-cover"
          />
          <div>
            <h3 className="font-semibold text-white">{post.user.username}</h3>
            <p className="text-xs text-gray-500">{new Date(post.created_at).toLocaleTimeString()}</p>
          </div>
        </div>
        <button className="text-gray-400 hover:text-white">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>
      </div>

      {/* Post Content */}
      <div className="relative">
        {post.video_url ? (
          <video
            src={post.video_url}
            className="w-full max-h-96 object-cover"
            controls
            muted
            loop
          />
        ) : post.image_url ? (
          <img
            src={post.image_url}
            alt="Post content"
            className="w-full max-h-96 object-cover"
          />
        ) : (
          <div className="w-full h-96 bg-gray-800 flex items-center justify-center">
            <span className="text-gray-600">No media available</span>
          </div>
        )}
      </div>

      {/* Post Actions */}
      <div className="p-4">
        <div className="flex items-center gap-4 mb-3">
          <button
            onClick={handleLike}
            disabled={isLiking || isUnliking}
            className={`flex items-center gap-1 transition-colors ${
              isLiked ? 'text-red-500' : 'text-white hover:text-red-500'
            } disabled:opacity-50`}
          >
            <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
            <span className="text-sm">{likeCount}</span>
          </button>
          
          <button className="flex items-center gap-1 text-white hover:text-gray-300">
            <MessageCircle className="w-5 h-5" />
            <span className="text-sm">{post.comments_count}</span>
          </button>
          
          <button className="text-white hover:text-gray-300">
            <Send className="w-5 h-5" />
          </button>
          
          <button className="ml-auto text-white hover:text-gray-300">
            <Bookmark className="w-5 h-5" />
          </button>
        </div>

        {/* Caption */}
        {post.caption && (
          <div className="text-white">
            <span className="font-semibold">{post.user.username}</span>{' '}
            <span>{post.caption}</span>
          </div>
        )}

        {/* Hashtags */}
        {post.hashtags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {post.hashtags.map((tag, index) => (
              <span
                key={index}
                className="text-blue-400 hover:text-blue-300 cursor-pointer text-sm"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
