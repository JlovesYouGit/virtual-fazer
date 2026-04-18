import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, Send, Paperclip, Smile, MoreVertical, 
  Reply, Edit2, Trash2, Check, CheckCheck, Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { chatApi, InboxRoom, ChatRoom, Message } from '../services/chatApi';
import { MessageBubble } from './MessageBubble';

interface ConversationViewProps {
  room: InboxRoom;
  onBack: () => void;
}

export function ConversationView({ room, onBack }: ConversationViewProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const [messageText, setMessageText] = useState('');
  const [replyingTo, setReplyingTo] = useState<Message | null>(null);
  const [editingMessage, setEditingMessage] = useState<Message | null>(null);
  const [editText, setEditText] = useState('');
  const [showMessageActions, setShowMessageActions] = useState<string | null>(null);

  // Get detailed room information
  const {
    data: chatRoom,
    isLoading: roomLoading
  } = useQuery({
    queryKey: ['chatRoom', room.id],
    queryFn: () => chatApi.getChatRoom(room.id),
    enabled: !!room.id,
  });

  // Get messages
  const {
    data: messagesData,
    isLoading: messagesLoading,
    error: messagesError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  } = useQuery({
    queryKey: ['messages', room.id],
    queryFn: () => chatApi.getMessages(room.id),
    enabled: !!room.id,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (content: string) => 
      chatApi.sendMessage(room.id, content, 'text', replyingTo?.id),
    onSuccess: () => {
      setMessageText('');
      setReplyingTo(null);
      queryClient.invalidateQueries({ queryKey: ['messages', room.id] });
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      
      // Scroll to bottom
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  });

  // Edit message mutation (placeholder - would need to be implemented in API)
  const editMessageMutation = useMutation({
    mutationFn: ({ messageId, content }: { messageId: string; content: string }) =>
      chatApi.editMessage(messageId, content),
    onSuccess: () => {
      setEditingMessage(null);
      setEditText('');
      queryClient.invalidateQueries({ queryKey: ['messages', room.id] });
    }
  });

  // Delete message mutation (placeholder - would need to be implemented in API)
  const deleteMessageMutation = useMutation({
    mutationFn: (messageId: string) => chatApi.deleteMessage(messageId),
    onSuccess: () => {
      setShowMessageActions(null);
      queryClient.invalidateQueries({ queryKey: ['messages', room.id] });
    }
  });

  const messages = messagesData?.results || [];

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = useCallback(() => {
    if (!messageText.trim()) return;
    
    sendMessageMutation.mutate(messageText.trim());
  }, [messageText, sendMessageMutation]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const handleReply = useCallback((message: Message) => {
    setReplyingTo(message);
    inputRef.current?.focus();
  }, []);

  const handleEdit = useCallback((message: Message) => {
    setEditingMessage(message);
    setEditText(message.content);
    setReplyingTo(null);
    inputRef.current?.focus();
  }, []);

  const handleDelete = useCallback((messageId: string) => {
    if (window.confirm('Are you sure you want to delete this message?')) {
      deleteMessageMutation.mutate(messageId);
    }
  }, [deleteMessageMutation]);

  const handleEditSave = useCallback(() => {
    if (!editText.trim() || !editingMessage) return;
    
    editMessageMutation.mutate({
      messageId: editingMessage.id,
      content: editText.trim()
    });
  }, [editText, editingMessage, editMessageMutation]);

  const getRoomDisplayName = useCallback(() => {
    if (room.name) return room.name;
    
    const otherParticipants = room.participants.filter(p => p.id !== user?.id);
    if (otherParticipants.length === 1) {
      return `${otherParticipants[0].first_name} ${otherParticipants[0].last_name}`;
    }
    
    return 'Unknown';
  }, [room, user]);

  const formatTime = useCallback((timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
  }, []);

  const isOwnMessage = useCallback((message: Message) => {
    return message.sender.id === user?.id;
  }, [user]);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-dark-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 dark:hover:bg-dark-800 rounded-full transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
            </button>
            
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">
                {getRoomDisplayName()}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {room.room_type === 'direct' ? 'Direct Message' : 'Group Chat'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-dark-800 rounded-full">
              <MoreVertical size={20} className="text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messagesLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
          </div>
        ) : messagesError ? (
          <div className="text-center py-8 text-red-500">
            Failed to load messages
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No messages yet. Start the conversation!
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={isOwnMessage(message)}
                formatTime={formatTime}
                onReply={handleReply}
                onEdit={handleEdit}
                onDelete={handleDelete}
                showActions={showMessageActions === message.id}
                setShowActions={setShowMessageActions}
                isEditing={editingMessage?.id === message.id}
                editText={editText}
                setEditText={setEditText}
                onSaveEdit={handleEditSave}
                onCancelEdit={() => {
                  setEditingMessage(null);
                  setEditText('');
                }}
              />
            ))}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Reply Preview */}
      <AnimatePresence>
        {replyingTo && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 py-2 bg-gray-50 dark:bg-dark-800 border-t border-gray-200 dark:border-dark-700"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Reply size={16} />
                <span>Replying to {replyingTo.sender.first_name}</span>
                <span className="truncate max-w-xs">
                  "{replyingTo.content.substring(0, 50)}..."
                </span>
              </div>
              <button
                onClick={() => setReplyingTo(null)}
                className="p-1 hover:bg-gray-200 dark:hover:bg-dark-700 rounded"
              >
                ×
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200 dark:border-dark-700">
        <div className="flex items-end gap-2">
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-dark-800 rounded-full transition-colors">
            <Paperclip size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="w-full px-4 py-2 bg-gray-100 dark:bg-dark-800 border border-gray-200 dark:border-dark-700 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-dark-800 rounded-full transition-colors">
            <Smile size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          
          <button
            onClick={handleSendMessage}
            disabled={!messageText.trim() || sendMessageMutation.isPending}
            className="p-2 bg-brand text-white rounded-full hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
