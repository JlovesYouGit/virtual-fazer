import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi, Conversation, Message } from '../services/chatApi';
import { useRealtime } from '../context/RealtimeContext';
import { useAuth } from '../context/AuthContext';
import { 
  Send, 
  Paperclip, 
  Image as ImageIcon, 
  Smile, 
  Phone, 
  Video, 
  Info,
  Circle,
  Check,
  CheckCheck
} from 'lucide-react';
import { motion } from 'framer-motion';

export function RealChatPage() {
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { sendMessage, joinRoom, leaveRoom, sendTypingIndicator } = useRealtime();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Get conversations from backend
  const { data: conversations = [], isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getConversations,
    enabled: !!user,
  });

  // Get messages for active chat from backend
  const { data: messages = [], isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', activeChat],
    queryFn: () => activeChat ? chatApi.getMessages(activeChat) : [],
    enabled: !!activeChat,
  });

  // Send message mutation to backend
  const sendMessageMutation = useMutation({
    mutationFn: ({ roomId, content, type }: { roomId: string; content: string; type?: string }) =>
      chatApi.sendMessage(roomId, content, type),
    onSuccess: () => {
      // Optimistically update cache
      queryClient.invalidateQueries({ queryKey: ['messages', activeChat] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  // Real-time WebSocket listeners
  useEffect(() => {
    if (!activeChat) return;

    // Join the room for real-time messages
    joinRoom(activeChat);

    return () => {
      leaveRoom(activeChat);
    };
  }, [activeChat, joinRoom, leaveRoom]);

  // Listen for new messages via WebSocket
  useEffect(() => {
    const socket = useRealtime().socket;
    
    if (socket) {
      socket.on('new_message', (message: Message) => {
        if (message.room === activeChat) {
          queryClient.setQueryData(['messages', activeChat], (old: Message[] = []) => 
            [...old, message]
          );
        }
      });

      socket.on('message_read', ({ room_id, message_id }) => {
        if (room_id === activeChat) {
          queryClient.setQueryData(['messages', activeChat], (old: Message[] = []) =>
            old.map(msg => msg.id === message_id ? { ...msg, is_read: true } : msg)
          );
        }
      });

      socket.on('typing_indicator', ({ room_id, user_id, is_typing }) => {
        if (room_id === activeChat && user_id !== user?.id) {
          setIsTyping(is_typing);
        }
      });
    }

    return () => {
      if (socket) {
        socket.off('new_message');
        socket.off('message_read');
        socket.off('typing_indicator');
      }
    };
  }, [activeChat, user?.id, queryClient]);

  const handleSendMessage = () => {
    if (!messageInput.trim() || !activeChat) return;

    const content = messageInput.trim();
    setMessageInput('');

    // Send via WebSocket for real-time delivery
    sendMessage(activeChat, content);
    
    // Also send via REST API for persistence
    sendMessageMutation.mutate({
      roomId: activeChat,
      content,
    });

    // Mark as typing false
    sendTypingIndicator(activeChat, false);
  };

  const handleTyping = (value: string) => {
    setMessageInput(value);
    
    if (activeChat) {
      const isCurrentlyTyping = value.length > 0;
      sendTypingIndicator(activeChat, isCurrentlyTyping);
    }
  };

  const activeConversation = conversations.find(conv => conv.id === activeChat);

  if (conversationsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-dark-900">
      {/* Conversations Sidebar */}
      <div className="w-80 border-r border-dark-700 flex flex-col">
        <div className="p-4 border-b border-dark-700">
          <h2 className="text-xl font-semibold text-white">Messages</h2>
          <div className="mt-2">
            <input
              type="text"
              placeholder="Search conversations..."
              className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.map((conversation: Conversation) => (
            <ConversationItem
              key={conversation.id}
              conversation={conversation}
              isActive={activeChat === conversation.id}
              onClick={() => setActiveChat(conversation.id)}
            />
          ))}
        </div>
      </div>

      {/* Chat Area */}
      {activeChat && activeConversation ? (
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-dark-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <img
                  src={activeConversation.participant.avatar_url}
                  alt={activeConversation.participant.username}
                  className="w-10 h-10 rounded-full object-cover"
                />
                {activeConversation.participant.is_online && (
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-dark-900"></div>
                )}
              </div>
              <div>
                <h3 className="font-semibold text-white">{activeConversation.participant.username}</h3>
                <p className="text-sm text-gray-400">
                  {activeConversation.participant.is_online ? 'Active now' : `Last seen ${new Date(activeConversation.participant.last_seen).toLocaleTimeString()}`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-400 hover:text-white">
                <Phone size={20} />
              </button>
              <button className="p-2 text-gray-400 hover:text-white">
                <Video size={20} />
              </button>
              <button className="p-2 text-gray-400 hover:text-white">
                <Info size={20} />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messagesLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
              </div>
            ) : (
              messages.map((message: Message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isOwn={message.sender === user?.id}
                  senderName={activeConversation.participant.username}
                />
              ))
            )}
            
            {isTyping && (
              <div className="flex items-center gap-2 text-gray-400">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm">typing...</span>
              </div>
            )}
          </div>

          {/* Message Input */}
          <div className="px-6 py-4 border-t border-dark-700">
            <div className="flex items-center gap-3">
              <button className="p-2 text-gray-400 hover:text-white">
                <Paperclip size={20} />
              </button>
              <button className="p-2 text-gray-400 hover:text-white">
                <ImageIcon size={20} />
              </button>
              <div className="flex-1">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => handleTyping(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type a message..."
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-600 rounded-full text-white placeholder-gray-500 focus:outline-none focus:border-brand"
                />
              </div>
              <button className="p-2 text-gray-400 hover:text-white">
                <Smile size={20} />
              </button>
              <button
                onClick={handleSendMessage}
                disabled={!messageInput.trim() || sendMessageMutation.isPending}
                className="p-2 bg-brand text-white rounded-full hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-24 h-24 bg-gray-800 rounded-full mx-auto mb-4 flex items-center justify-center">
              <div className="w-12 h-12 bg-gray-700 rounded-full"></div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Select a conversation</h3>
            <p className="text-gray-400">Choose a conversation from the sidebar to start messaging</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Conversation Item Component
function ConversationItem({ 
  conversation, 
  isActive, 
  onClick 
}: { 
  conversation: Conversation; 
  isActive: boolean; 
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`p-4 hover:bg-dark-800 cursor-pointer transition-colors border-b border-dark-700 ${
        isActive ? 'bg-dark-800' : ''
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <img
            src={conversation.participant.avatar_url}
            alt={conversation.participant.username}
            className="w-12 h-12 rounded-full object-cover"
          />
          {conversation.participant.is_online && (
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-dark-900"></div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white truncate">
              {conversation.participant.username}
            </h4>
            <span className="text-xs text-gray-500">
              {new Date(conversation.last_message.created_at).toLocaleTimeString()}
            </span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <p className="text-sm text-gray-400 truncate">
              {conversation.last_message.message_type === 'image' ? 'Photo' : conversation.last_message.content}
            </p>
            {conversation.unread_count > 0 && (
              <div className="bg-brand text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {conversation.unread_count}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({ 
  message, 
  isOwn, 
  senderName 
}: { 
  message: Message; 
  isOwn: boolean; 
  senderName: string;
}) {
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md ${isOwn ? 'order-2' : 'order-1'}`}>
        {!isOwn && (
          <p className="text-xs text-gray-500 mb-1">{senderName}</p>
        )}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`px-4 py-2 rounded-2xl ${
            isOwn 
              ? 'bg-brand text-white rounded-br-none' 
              : 'bg-dark-800 text-white rounded-bl-none'
          }`}
        >
          {message.message_type === 'image' ? (
            <div className="text-center">
              <ImageIcon size={20} className="inline-block" />
              <p className="text-sm mt-1">Photo</p>
            </div>
          ) : (
            <p className="text-sm">{message.content}</p>
          )}
        </motion.div>
        <div className={`flex items-center gap-1 mt-1 text-xs text-gray-500 ${isOwn ? 'justify-end' : 'justify-start'}`}>
          <span>{new Date(message.created_at).toLocaleTimeString()}</span>
          {isOwn && (
            <>
              {message.is_read ? (
                <CheckCheck size={14} className="text-blue-400" />
              ) : (
                <Check size={14} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
