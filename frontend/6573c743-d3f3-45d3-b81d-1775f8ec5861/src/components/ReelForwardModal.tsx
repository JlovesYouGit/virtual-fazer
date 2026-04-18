import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Send, Check, Users, UserCheck, MessageCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

interface User {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
}

interface ReelForwardModalProps {
  isOpen: boolean;
  onClose: () => void;
  reelId: string;
  reelCaption: string;
}

export function ReelForwardModal({ isOpen, onClose, reelId, reelCaption }: ReelForwardModalProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
  const [message, setMessage] = useState('');
  const [isForwarding, setIsForwarding] = useState(false);

  // Get forwardable users
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['forwardable-users', reelId],
    queryFn: async () => {
      const response = await apiClient.get(`/reels/forward/users/?reel_id=${reelId}`);
      return response.data;
    },
    enabled: isOpen && !!reelId,
  });

  // Forward reel mutation
  const forwardMutation = useMutation({
    mutationFn: async (data: { reel_id: string; recipient_ids: string[]; message?: string }) => {
      const response = await apiClient.post('/reels/forward/', data);
      return response.data;
    },
    onSuccess: (data) => {
      setIsForwarding(false);
      queryClient.invalidateQueries({ queryKey: ['received-forwards'] });
      queryClient.invalidateQueries({ queryKey: ['saved-forwards'] });
      onClose();
    },
    onError: () => {
      setIsForwarding(false);
    }
  });

  // Filter users based on search
  const filteredUsers = usersData?.users?.filter((user: User) =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.last_name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Toggle user selection
  const toggleUserSelection = (user: User) => {
    setSelectedUsers(prev => {
      const isSelected = prev.some(u => u.id === user.id);
      if (isSelected) {
        return prev.filter(u => u.id !== user.id);
      } else {
        return [...prev, user];
      }
    });
  };

  // Handle forward
  const handleForward = () => {
    if (selectedUsers.length === 0) return;
    
    setIsForwarding(true);
    forwardMutation.mutate({
      reel_id: reelId,
      recipient_ids: selectedUsers.map(u => u.id),
      message: message.trim()
    });
  };

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
      setSelectedUsers([]);
      setMessage('');
      setIsForwarding(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-md w-full max-h-[80vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Forward Reel
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Reel preview */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Reel to forward:</p>
            <p className="text-gray-900 dark:text-white font-medium truncate">
              {reelCaption || 'Untitled Reel'}
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
        </div>

        {/* Users list */}
        <div className="flex-1 overflow-y-auto p-4 max-h-60">
          {usersLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8">
              <Users className="mx-auto text-gray-400 mb-2" size={48} />
              <p className="text-gray-500 dark:text-gray-400">
                {searchQuery ? 'No users found' : 'No users available'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredUsers.map((user: User) => {
                const isSelected = selectedUsers.some(u => u.id === user.id);
                return (
                  <div
                    key={user.id}
                    onClick={() => toggleUserSelection(user)}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-brand/10 border border-brand'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent'
                    }`}
                  >
                    <div className="relative">
                      <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-orange-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-medium">
                          {user.first_name.charAt(0)}
                        </span>
                      </div>
                      {isSelected && (
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-brand rounded-full flex items-center justify-center">
                          <Check size={12} className="text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {user.username}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {user.first_name} {user.last_name}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Message input */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <textarea
            placeholder="Add a message (optional)..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
            rows={2}
            maxLength={500}
          />
          <div className="text-xs text-gray-500 dark:text-gray-400 text-right mt-1">
            {message.length}/500
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {selectedUsers.length} user{selectedUsers.length !== 1 ? 's' : ''} selected
            </span>
            {selectedUsers.length > 0 && (
              <button
                onClick={() => setSelectedUsers([])}
                className="text-sm text-brand hover:text-brand-hover"
              >
                Clear selection
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleForward}
              disabled={selectedUsers.length === 0 || isForwarding || forwardMutation.isPending}
              className="flex-1 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isForwarding || forwardMutation.isPending ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send size={16} />
              )}
              Forward to {selectedUsers.length} {selectedUsers.length === 1 ? 'user' : 'users'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
