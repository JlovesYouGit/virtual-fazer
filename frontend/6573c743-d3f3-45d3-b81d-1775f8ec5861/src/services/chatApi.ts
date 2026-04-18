import { apiClient } from '../lib/apiClient';

export interface InboxRoom {
  id: string;
  name?: string;
  room_type: 'direct' | 'group';
  participants: Array<{
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  }>;
  unread_count: number;
  last_message_content: string;
  last_message_time: string;
  last_message_sender: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRoom {
  id: string;
  name?: string;
  room_type: 'direct' | 'group';
  participants: Array<{
    id: string;
    username: string;
    first_name: string;
    last_name: string;
    role: 'admin' | 'member';
    joined_at: string;
    last_read: string;
    is_muted: boolean;
    is_archived: boolean;
  }>;
  unread_count: number;
  created_by: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  last_message: string;
  last_message_time: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  room: string;
  sender: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  content: string;
  message_type: 'text' | 'image' | 'video' | 'audio' | 'file' | 'reel_share' | 'profile_share';
  media_file?: string;
  reply_to?: Message;
  is_edited: boolean;
  edited_at?: string;
  is_deleted: boolean;
  deleted_at?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  reactions: Array<{
    id: string;
    user: {
      id: string;
      username: string;
      first_name: string;
      last_name: string;
    };
    emoji: string;
    created_at: string;
  }>;
  is_read: boolean;
  read_receipts: Array<{
    user: {
      id: string;
      username: string;
      first_name: string;
      last_name: string;
    };
    read_at: string;
  }>;
}

export interface InboxSummary {
  total_unread_messages: number;
  unread_notifications: number;
  recent_rooms: InboxRoom[];
  total_rooms: number;
}

export interface MessageHistory {
  messages: Message[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export const chatApi = {
  // Inbox functionality
  getInbox: () =>
    apiClient.get<InboxRoom[]>('/chat/inbox/'),
  
  getInboxSummary: () =>
    apiClient.get<InboxSummary>('/chat/inbox/summary/'),
  
  createDirectMessage: (recipientId: string, initialMessage?: string) =>
    apiClient.post<{ room: InboxRoom; message: string }>('/chat/inbox/direct-message/', {
      recipient_id: recipientId,
      initial_message: initialMessage
    }),
  
  getChatRoom: (roomId: string) =>
    apiClient.get<ChatRoom>(`/chat/rooms/${roomId}/`),
  
  markRoomAsRead: (roomId: string) =>
    apiClient.post(`/chat/inbox/rooms/${roomId}/read/`),
  
  archiveRoom: (roomId: string) =>
    apiClient.post(`/chat/inbox/rooms/${roomId}/archive/`),
  
  muteRoom: (roomId: string, isMuted: boolean) =>
    apiClient.post(`/chat/inbox/rooms/${roomId}/mute/`, { is_muted: isMuted }),
  
  deleteRoom: (roomId: string) =>
    apiClient.delete(`/chat/inbox/rooms/${roomId}/delete/`),
  
  searchConversations: (query: string) =>
    apiClient.get<{ query: string; results: InboxRoom[] }>('/chat/inbox/search/', {
      params: { q: query }
    }),
  
  getMessageHistory: (roomId: string, page = 1, pageSize = 50, search?: string) =>
    apiClient.get<MessageHistory>(`/chat/inbox/rooms/${roomId}/history/`, {
      params: { page, page_size: pageSize, search }
    }),
  
  // Basic chat functionality
  getMessages: (roomId: string, page = 1, limit = 50) =>
    apiClient.get<{ results: Message[] }>(`/chat/rooms/${roomId}/messages/`, {
      params: { page, limit }
    }),
  
  sendMessage: (roomId: string, content: string, type = 'text', replyToId?: string) =>
    apiClient.post<Message>('/chat/send-message/', {
      room_id: roomId,
      content,
      message_type: type,
      reply_to_id: replyToId
    }),
  
  createRoom: (participantId: string) =>
    apiClient.post<ChatRoom>('/chat/create-room/', { participant_ids: [participantId] }),
  
  createGroupRoom: (name: string, participantIds: string[]) =>
    apiClient.post<ChatRoom>('/chat/create-room/', {
      name,
      room_type: 'group',
      participant_ids: participantIds
    }),
  
  markMessageAsRead: (messageId: string) =>
    apiClient.post('/chat/mark-read/', { message_id: messageId }),
  
  reactToMessage: (messageId: string, emoji: string) =>
    apiClient.post('/chat/react/', { message_id: messageId, emoji }),
  
  startTyping: (roomId: string) =>
    apiClient.post('/chat/start-typing/', { room_id: roomId }),
  
  stopTyping: (roomId: string) =>
    apiClient.post('/chat/stop-typing/', { room_id: roomId }),
  
  getUnreadCount: () =>
    apiClient.get<{ unread_count: number }>('/chat/unread-count/'),
  
  getChatAnalytics: (days = 30) =>
    apiClient.get('/chat/analytics/', { params: { days } }),
};
