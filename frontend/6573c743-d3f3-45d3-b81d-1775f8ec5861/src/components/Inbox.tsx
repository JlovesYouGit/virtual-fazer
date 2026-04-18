import React, { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, Search, Plus, MoreVertical, Archive, 
  Volume2, VolumeX, Trash2, Check, CheckCheck, Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { chatApi, InboxRoom, ChatRoom, Message } from '../services/chatApi';
import { ConversationView } from './ConversationView';

export function Inbox() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [selectedRoom, setSelectedRoom] = useState<InboxRoom | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showRoomActions, setShowRoomActions] = useState<string | null>(null);

  // Get inbox rooms
  const {
    data: inboxRooms = [],
    isLoading: inboxLoading,
    error: inboxError
  } = useQuery({
    queryKey: ['inbox'],
    queryFn: chatApi.getInbox,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Get inbox summary
  const {
    data: inboxSummary,
    isLoading: summaryLoading
  } = useQuery({
    queryKey: ['inboxSummary'],
    queryFn: chatApi.getInboxSummary,
    refetchInterval: 30000,
  });

  // Search conversations
  const {
    data: searchResults,
    isLoading: searchLoading
  } = useQuery({
    queryKey: ['searchConversations', searchQuery],
    queryFn: () => chatApi.searchConversations(searchQuery),
    enabled: searchQuery.length > 0,
  });

  // Mark room as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: (roomId: string) => chatApi.markRoomAsRead(roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      queryClient.invalidateQueries({ queryKey: ['inboxSummary'] });
    }
  });

  // Archive room mutation
  const archiveMutation = useMutation({
    mutationFn: (roomId: string) => chatApi.archiveRoom(roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      if (selectedRoom?.id === roomId) {
        setSelectedRoom(null);
      }
    }
  });

  // Mute room mutation
  const muteMutation = useMutation({
    mutationFn: ({ roomId, isMuted }: { roomId: string; isMuted: boolean }) =>
      chatApi.muteRoom(roomId, isMuted),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    }
  });

  // Delete room mutation
  const deleteMutation = useMutation({
    mutationFn: (roomId: string) => chatApi.deleteRoom(roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      if (selectedRoom?.id === roomId) {
        setSelectedRoom(null);
      }
    }
  });

  const handleRoomSelect = useCallback((room: InboxRoom) => {
    setSelectedRoom(room);
    setShowRoomActions(null);
    
    // Mark as read if unread
    if (room.unread_count > 0) {
      markAsReadMutation.mutate(room.id);
    }
  }, [markAsReadMutation]);

  const handleRoomAction = useCallback((action: string, roomId: string) => {
    switch (action) {
      case 'archive':
        archiveMutation.mutate(roomId);
        break;
      case 'mute':
        muteMutation.mutate({ roomId, isMuted: true });
        break;
      case 'unmute':
        muteMutation.mutate({ roomId, isMuted: false });
        break;
      case 'delete':
        deleteMutation.mutate(roomId);
        break;
    }
    setShowRoomActions(null);
  }, [archiveMutation, muteMutation, deleteMutation]);

  const formatTime = useCallback((timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'now';
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    
    return date.toLocaleDateString();
  }, []);

  const getRoomDisplayName = useCallback((room: InboxRoom) => {
    if (room.name) return room.name;
    
    // For direct messages, show the other user's name
    const otherParticipants = room.participants.filter(p => p.id !== user?.id);
    if (otherParticipants.length === 1) {
      return `${otherParticipants[0].first_name} ${otherParticipants[0].last_name}`;
    }
    
    return 'Unknown';
  }, [user]);

  const displayRooms = searchQuery ? (searchResults?.results || []) : inboxRooms;

  const renderRoomItem = (room: InboxRoom) => {
    const isSelected = selectedRoom?.id === room.id;
    const displayName = getRoomDisplayName(room);
    const isUnread = room.unread_count > 0;

    return (
      <motion.div
        key={room.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        onClick={() => handleRoomSelect(room)}
        className={`p-4 border-b border-gray-200 dark:border-dark-700 cursor-pointer transition-colors ${
          isSelected ? 'bg-brand/10 border-brand/20' : 'hover:bg-gray-50 dark:hover:bg-dark-800'
        }`}
      >
        <div className="flex items-start gap-3">
          {/* Avatar */}
          <div className="w-12 h-12 bg-gradient-to-br from-brand to-brand-dark rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-medium text-sm">
              {displayName.charAt(0).toUpperCase()}
            </span>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <h3 className={`font-medium text-gray-900 dark:text-white truncate ${
                isUnread ? 'font-semibold' : ''
              }`}>
                {displayName}
              </h3>
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                {formatTime(room.last_message_time)}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <p className={`text-sm truncate ${
                isUnread 
                  ? 'text-gray-900 dark:text-white font-medium' 
                  : 'text-gray-600 dark:text-gray-400'
              }`}>
                {room.last_message_sender && (
                  <span className="font-medium">{room.last_message_sender}: </span>
                )}
                {room.last_message_content}
              </p>
              
              {/* Unread indicator */}
              {isUnread && (
                <div className="ml-2 w-5 h-5 bg-brand rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-medium">
                    {room.unread_count > 99 ? '99+' : room.unread_count}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowRoomActions(showRoomActions === room.id ? null : room.id);
              }}
              className="p-1 hover:bg-gray-200 dark:hover:bg-dark-700 rounded-full"
            >
              <MoreVertical size={16} className="text-gray-500" />
            </button>

            <AnimatePresence>
              {showRoomActions === room.id && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute right-0 top-8 bg-white dark:bg-dark-800 rounded-lg shadow-lg border border-gray-200 dark:border-dark-700 py-1 z-10"
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRoomAction(room.room_type === 'direct' ? 'delete' : 'archive', room.id);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-700 flex items-center gap-2"
                  >
                    {room.room_type === 'direct' ? (
                      <>
                        <Trash2 size={14} />
                        Delete
                      </>
                    ) : (
                      <>
                        <Archive size={14} />
                        Archive
                      </>
                    )}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    );
  };

  if (selectedRoom) {
    return (
      <ConversationView
        room={selectedRoom}
        onBack={() => setSelectedRoom(null)}
      />
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-dark-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-700">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Messages
          </h1>
          
          <div className="flex items-center gap-2">
            {/* Unread count */}
            {!summaryLoading && inboxSummary && (
              <div className="px-3 py-1 bg-brand text-white rounded-full text-sm font-medium">
                {inboxSummary.total_unread_messages} unread
              </div>
            )}
            
            {/* New message button */}
            <button className="p-2 bg-brand text-white rounded-full hover:bg-brand-hover transition-colors">
              <Plus size={20} />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-dark-800 border border-gray-200 dark:border-dark-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
          />
        </div>
      </div>

      {/* Room List */}
      <div className="flex-1 overflow-y-auto">
        {inboxLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
          </div>
        ) : inboxError ? (
          <div className="text-center py-8 text-red-500">
            Failed to load messages
          </div>
        ) : displayRooms.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No conversations found' : 'No messages yet'}
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
              Start a conversation to see messages here
            </p>
          </div>
        ) : (
          <div>
            <AnimatePresence>
              {displayRooms.map(renderRoomItem)}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
