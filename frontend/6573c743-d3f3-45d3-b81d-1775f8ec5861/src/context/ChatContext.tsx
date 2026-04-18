import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { chatApi, Message, InboxRoom } from '../services/chatApi';

interface ChatContextType {
  // WebSocket connection
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  
  // Room management
  currentRoom: InboxRoom | null;
  setCurrentRoom: (room: InboxRoom | null) => void;
  
  // Real-time messages
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  
  // Typing indicators
  typingUsers: string[];
  setTypingUsers: (users: string[]) => void;
  
  // Notifications
  unreadCount: number;
  setUnreadCount: (count: number) => void;
  
  // WebSocket events
  sendMessage: (content: string, roomId: string) => void;
  sendTypingIndicator: (roomId: string, isTyping: boolean) => void;
  markAsRead: (roomId: string) => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [currentRoom, setCurrentRoom] = useState<InboxRoom | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Get unread count from API
  const { data: unreadData } = useQuery({
    queryKey: ['unreadCount'],
    queryFn: chatApi.getUnreadCount,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  useEffect(() => {
    if (unreadData) {
      setUnreadCount(unreadData.unread_count);
    }
  }, [unreadData]);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Chat WebSocket connected');
      setIsConnected(true);
      
      // Clear any pending reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('Chat WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
    };
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'chat_message':
        // New message received
        const newMessage = data.message;
        setMessages((prev: any) => [...prev, newMessage]);
        
        // Update unread count if not in current room
        if (currentRoom?.id !== newMessage.room) {
          setUnreadCount((prev: number) => prev + 1);
        }
        
        // Invalidate inbox cache
        queryClient.invalidateQueries({ queryKey: ['inbox'] });
        break;

      case 'message_reaction':
        // Message reaction added/removed
        const reactionData = data.reaction;
        setMessages((prev: any[]) => prev.map((msg: { id: any; reactions: any; }) => 
          msg.id === reactionData.message_id
            ? { ...msg, reactions: [...(msg.reactions || []), reactionData] }
            : msg
        ));
        break;

      case 'typing_indicator':
        // User typing indicator
        const { username, is_typing } = data;
        setTypingUsers((prev: any[]) => {
          if (is_typing) {
            return prev.includes(username) ? prev : [...prev, username];
          } else {
            return prev.filter((u: any) => u !== username);
          }
        });
        break;

      case 'messages_read':
        // Messages marked as read
        const { user_id, read_up_to } = data;
        setMessages((prev: any[]) => prev.map((msg: { sender: { id: any; }; is_read: any; read_receipts: any; }) => ({
          ...msg,
          is_read: msg.sender.id === user_id ? true : msg.is_read,
          read_receipts: msg.sender.id === user_id 
            ? [...(msg.read_receipts || []), { user: { id: user_id }, read_at: read_up_to }]
            : msg.read_receipts
        })));
        break;

      case 'new_direct_message':
        // New direct message notification
        const { room_id, sender_id, sender_username } = data;
        setUnreadCount((prev: number) => prev + 1);
        
        // Invalidate inbox cache
        queryClient.invalidateQueries({ queryKey: ['inbox'] });
        queryClient.invalidateQueries({ queryKey: ['unreadCount'] });
        break;

      case 'message_updated':
        // Message edited or deleted
        const updatedMessage = data.message;
        setMessages((prev: any[]) => prev.map((msg: { id: any; }) => 
          msg.id === updatedMessage.id ? updatedMessage : msg
        ));
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  const sendMessage = (content: string, roomId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'send_message',
        room_id: roomId,
        content: content
      }));
    }
  };

  const sendTypingIndicator = (roomId: string, isTyping: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing_indicator',
        room_id: roomId,
        is_typing: isTyping
      }));
    }
  };

  const markAsRead = (roomId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'mark_as_read',
        room_id: roomId
      }));
    }
  };

  const addMessage = (message: Message) => {
    setMessages((prev: Message[]) => [...prev, message]);
  };

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []);

  // Clear typing users when room changes
  useEffect(() => {
    setTypingUsers([]);
  }, [currentRoom]);

  const value: ChatContextType = {
    isConnected,
    connect,
    disconnect,
    currentRoom,
    setCurrentRoom,
    messages,
    setMessages,
    addMessage,
    typingUsers,
    setTypingUsers,
    unreadCount,
    setUnreadCount,
    sendMessage,
    sendTypingIndicator,
    markAsRead,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
