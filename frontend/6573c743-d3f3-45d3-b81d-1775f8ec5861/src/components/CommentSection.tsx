import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageCircle, 
  Heart, 
  Send, 
  Reply, 
  MoreHorizontal,
  Flag,
  Edit2,
  Trash2,
  User,
  Clock,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useRealtime } from '../context/RealtimeContext';
import { LoadingSpinner } from './LoadingStates';
import { commentsApi } from '../services/commentsApi';

interface Comment {
  id: string;
  text: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  parent_user?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  parent?: string;
  replies: Comment[];
  likes_count: number;
  replies_count: number;
  is_liked_by_user: boolean;
  mentions: Array<{
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  }>;
  is_edited: boolean;
  edited_at?: string;
  created_at: string;
  time_ago: string;
}

interface CommentSectionProps {
  content_type: 'reel' | 'post';
  content_id: string;
  className?: string;
}

export function CommentSection({ content_type, content_id, className = '' }: CommentSectionProps) {
  const { user } = useAuth();
  const { subscribeToComments, unsubscribeFromComments } = useRealtime();
  const queryClient = useQueryClient();
  
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<Comment | null>(null);
  const [editingComment, setEditingComment] = useState<Comment | null>(null);
  const [editText, setEditText] = useState('');
  const [showComments, setShowComments] = useState(false);
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'popular'>('newest');
  const commentInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Fetch comments
  const {
    data: commentsData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['comments', content_type, content_id, sortBy],
    queryFn: () => commentsApi.getComments(content_type, content_id, { sort_by: sortBy }),
    enabled: showComments
  });
  
  // Create comment mutation
  const createCommentMutation = useMutation({
    mutationFn: (data: { text: string; parent_id?: string }) => 
      commentsApi.createComment(content_type, content_id, data),
    onSuccess: () => {
      setNewComment('');
      setReplyingTo(null);
      queryClient.invalidateQueries({ queryKey: ['comments', content_type, content_id] });
      queryClient.invalidateQueries({ queryKey: ['comment_thread', content_type, content_id] });
    }
  });
  
  // Update comment mutation
  const updateCommentMutation = useMutation({
    mutationFn: ({ commentId, text }: { commentId: string; text: string }) =>
      commentsApi.updateComment(commentId, { text }),
    onSuccess: () => {
      setEditingComment(null);
      setEditText('');
      queryClient.invalidateQueries({ queryKey: ['comments', content_type, content_id] });
    }
  });
  
  // Delete comment mutation
  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: string) => commentsApi.deleteComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', content_type, content_id] });
      queryClient.invalidateQueries({ queryKey: ['comment_thread', content_type, content_id] });
    }
  });
  
  // Like comment mutation
  const likeCommentMutation = useMutation({
    mutationFn: (commentId: string) => commentsApi.likeComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', content_type, content_id] });
    }
  });
  
  // Unlike comment mutation
  const unlikeCommentMutation = useMutation({
    mutationFn: (commentId: string) => commentsApi.unlikeComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', content_type, content_id] });
    }
  });
  
  // Real-time updates
  useEffect(() => {
    if (showComments) {
      subscribeToComments(content_type, content_id);
    }
    
    return () => {
      unsubscribeFromComments(content_type, content_id);
    };
  }, [showComments, content_type, content_id]);
  
  // Handle new comment submission
  const handleSubmitComment = useCallback(async () => {
    if (!newComment.trim() || !user) return;
    
    const data: { text: string; parent_id?: string } = {
      text: newComment.trim()
    };
    
    if (replyingTo) {
      data.parent_id = replyingTo.id;
    }
    
    createCommentMutation.mutate(data);
  }, [newComment, user, replyingTo, createCommentMutation]);
  
  // Handle edit submission
  const handleEditSubmit = useCallback(async () => {
    if (!editText.trim() || !editingComment) return;
    
    updateCommentMutation.mutate({
      commentId: editingComment.id,
      text: editText.trim()
    });
  }, [editText, editingComment, updateCommentMutation]);
  
  // Handle like/unlike
  const handleLikeComment = useCallback((commentId: string, isLiked: boolean) => {
    if (isLiked) {
      unlikeCommentMutation.mutate(commentId);
    } else {
      likeCommentMutation.mutate(commentId);
    }
  }, [likeCommentMutation, unlikeCommentMutation]);
  
  // Handle delete
  const handleDeleteComment = useCallback((commentId: string) => {
    if (window.confirm('Are you sure you want to delete this comment?')) {
      deleteCommentMutation.mutate(commentId);
    }
  }, [deleteCommentMutation]);
  
  // Handle reply
  const handleReply = useCallback((comment: Comment) => {
    setReplyingTo(comment);
    setNewComment(`@${comment.user.username} `);
    commentInputRef.current?.focus();
  }, []);
  
  // Handle edit
  const handleEdit = useCallback((comment: Comment) => {
    setEditingComment(comment);
    setEditText(comment.text);
  }, []);
  
  // Format timestamp
  const formatTimestamp = useCallback((timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
  }, []);
  
  // Render single comment
  const renderComment = useCallback((comment: Comment, isReply = false) => (
    <motion.div
      key={comment.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`${isReply ? 'ml-8' : ''}`}
    >
      <div className="flex gap-3 p-3 hover:bg-dark-800/50 rounded-lg transition-colors">
        {/* User Avatar */}
        <div className="w-10 h-10 bg-gradient-to-br from-brand to-brand-dark rounded-full flex items-center justify-center flex-shrink-0">
          <User size={20} className="text-white" />
        </div>
        
        {/* Comment Content */}
        <div className="flex-1 min-w-0">
          {/* User Info */}
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-white">
              {comment.user.first_name} {comment.user.last_name}
            </span>
            <span className="text-gray-400 text-sm">@{comment.user.username}</span>
            <span className="text-gray-500 text-sm flex items-center gap-1">
              <Clock size={12} />
              {formatTimestamp(comment.created_at)}
            </span>
            {comment.is_edited && (
              <span className="text-gray-500 text-xs">(edited)</span>
            )}
          </div>
          
          {/* Reply to indicator */}
          {comment.parent_user && (
            <div className="text-gray-400 text-sm mb-2">
              replying to <span className="text-brand">@{comment.parent_user.username}</span>
            </div>
          )}
          
          {/* Comment Text */}
          <div className="text-gray-300 break-words mb-3">
            {editingComment?.id === comment.id ? (
              <div className="space-y-2">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg p-2 text-white placeholder-gray-400 resize-none focus:outline-none focus:border-brand"
                  rows={3}
                  placeholder="Edit your comment..."
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleEditSubmit}
                    disabled={updateCommentMutation.isPending}
                    className="px-3 py-1 bg-brand text-white text-sm rounded hover:bg-brand-hover disabled:opacity-50"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingComment(null)}
                    className="px-3 py-1 bg-dark-700 text-white text-sm rounded hover:bg-dark-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{comment.text}</p>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-4 text-sm">
            <button
              onClick={() => handleLikeComment(comment.id, comment.is_liked_by_user)}
              className={`flex items-center gap-1 transition-colors ${
                comment.is_liked_by_user ? 'text-red-500' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Heart size={16} fill={comment.is_liked_by_user ? 'currentColor' : 'none'} />
              <span>{comment.likes_count}</span>
            </button>
            
            <button
              onClick={() => handleReply(comment)}
              className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors"
            >
              <Reply size={16} />
              <span>{comment.replies_count}</span>
            </button>
            
            {user && comment.user.id === user.id && (
              <>
                <button
                  onClick={() => handleEdit(comment)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Edit2 size={16} />
                </button>
                
                <button
                  onClick={() => handleDeleteComment(comment.id)}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </>
            )}
            
            <button className="text-gray-400 hover:text-white transition-colors">
              <MoreHorizontal size={16} />
            </button>
          </div>
          
          {/* Replies */}
          {comment.replies.length > 0 && (
            <div className="mt-3 space-y-2">
              {comment.replies.map(reply => renderComment(reply, true))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  ), [
    formatTimestamp, 
    handleLikeComment, 
    handleReply, 
    handleEdit, 
    handleDeleteComment, 
    handleEditSubmit,
    editingComment,
    editText,
    setEditText,
    setEditingComment,
    user
  ]);
  
  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle size={16} />
          <span>Failed to load comments</span>
          <button
            onClick={() => refetch()}
            className="text-brand hover:text-brand-light"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`bg-dark-900 rounded-xl ${className}`}>
      {/* Comment Toggle */}
      <div className="p-4 border-b border-dark-700">
        <button
          onClick={() => setShowComments(!showComments)}
          className="flex items-center gap-2 text-white hover:text-brand transition-colors"
        >
          <MessageCircle size={20} />
          <span className="font-medium">
            {showComments ? 'Hide Comments' : 'View Comments'}
          </span>
          {commentsData?.results && (
            <span className="text-gray-400">
              ({commentsData.results.length})
            </span>
          )}
        </button>
      </div>
      
      {/* Comments Section */}
      <AnimatePresence>
        {showComments && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            {/* Sort Options */}
            <div className="px-4 py-2 border-b border-dark-700">
              <div className="flex items-center gap-4">
                <span className="text-gray-400 text-sm">Sort by:</span>
                {['newest', 'oldest', 'popular'].map((sort) => (
                  <button
                    key={sort}
                    onClick={() => setSortBy(sort as any)}
                    className={`text-sm px-2 py-1 rounded transition-colors ${
                      sortBy === sort
                        ? 'bg-brand text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    {sort.charAt(0).toUpperCase() + sort.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Comments List */}
            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="p-4 flex justify-center">
                  <LoadingSpinner text="Loading comments..." />
                </div>
              ) : commentsData?.results?.length > 0 ? (
                <div className="p-4 space-y-3">
                  {commentsData.results.map((comment: Comment) => renderComment(comment))}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-400">
                  <MessageCircle size={48} className="mx-auto mb-4 opacity-50" />
                  <p>No comments yet. Be the first to comment!</p>
                </div>
              )}
            </div>
            
            {/* Comment Input */}
            {user && (
              <div className="p-4 border-t border-dark-700">
                {replyingTo && (
                  <div className="mb-3 p-2 bg-dark-800 rounded-lg flex items-center justify-between">
                    <span className="text-sm text-gray-300">
                      Replying to @{replyingTo.user.username}
                    </span>
                    <button
                      onClick={() => setReplyingTo(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      ×
                    </button>
                  </div>
                )}
                
                <div className="flex gap-2">
                  <textarea
                    ref={commentInputRef}
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="flex-1 bg-dark-800 border border-dark-600 rounded-lg p-3 text-white placeholder-gray-400 resize-none focus:outline-none focus:border-brand"
                    rows={2}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmitComment();
                      }
                    }}
                  />
                  <button
                    onClick={handleSubmitComment}
                    disabled={!newComment.trim() || createCommentMutation.isPending}
                    className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {createCommentMutation.isPending ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Send size={16} />
                    )}
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
