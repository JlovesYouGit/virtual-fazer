import React, { createContext, useContext, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { env } from '../lib/env';

interface RealtimeContextType {
  socket: Socket | null;
  connected: boolean;
  sendMessage: (roomId: string, content: string, type?: string) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  sendTypingIndicator: (roomId: string, isTyping: boolean) => void;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const { accessToken, status } = useAuth();

  useEffect(() => {
    if (status === 'authenticated' && accessToken && env.ENABLE_REALTIME_CHAT) {
      const newSocket = io(env.WS_URL, {
        auth: {
          token: accessToken,
        },
        transports: ['websocket', 'polling'],
      });

      newSocket.on('connect', () => {
        setConnected(true);
        console.log('Connected to WebSocket server');
      });

      newSocket.on('disconnect', () => {
        setConnected(false);
        console.log('Disconnected from WebSocket server');
      });

      newSocket.on('error', (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      });

      // Real-time message handling
      newSocket.on('new_message', (message) => {
        // This will be handled by individual chat components
        console.log('New message received:', message);
      });

      // Real-time notifications
      newSocket.on('new_notification', (notification) => {
        // This will be handled by notification system
        console.log('New notification:', notification);
      });

      // Typing indicators
      newSocket.on('typing_indicator', (data) => {
        console.log('Typing indicator:', data);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
      };
    }
  }, [accessToken, status]);

  const sendMessage = (roomId: string, content: string, type = 'text') => {
    if (socket && connected) {
      socket.emit('chat_message', {
        room_id: roomId,
        content,
        message_type: type
      });
    }
  };

  const joinRoom = (roomId: string) => {
    if (socket && connected) {
      socket.emit('join_room', { room_id: roomId });
    }
  };

  const leaveRoom = (roomId: string) => {
    if (socket && connected) {
      socket.emit('leave_room', { room_id: roomId });
    }
  };

  const sendTypingIndicator = (roomId: string, isTyping: boolean) => {
    if (socket && connected) {
      socket.emit('typing_indicator', {
        room_id: roomId,
        is_typing: isTyping
      });
    }
  };

  return (
    <RealtimeContext.Provider value={{
      socket, connected, sendMessage, joinRoom, leaveRoom, sendTypingIndicator
    }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (context === undefined) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}
