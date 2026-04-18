# Complete Chat & Inbox System Implementation Guide

## Overview

The Instagram clone now has a **complete chat and inbox system** with real-time messaging, direct messages (DMs), inbox management, and comprehensive notification integration. All messages are saved to user accounts with persistent storage and real-time WebSocket updates.

## Features Implemented

### Backend Chat System
- **Complete Chat Models**: ChatRoom, Message, ChatParticipant, MessageReaction, MessageRead, TypingIndicator
- **Direct Messages (DMs)**: One-on-one conversations with automatic room creation
- **Group Chats**: Multi-user conversations with participant management
- **Message Persistence**: All messages saved to database with timestamps
- **Real-time WebSocket**: Live messaging, typing indicators, read receipts
- **Inbox Management**: Unread counts, message search, room actions
- **Notification Integration**: Chat notifications integrated with existing notification system

### Frontend Chat Components
- **Inbox Component**: Complete inbox with conversation list, search, unread counts
- **ConversationView**: Full chat interface with message bubbles, typing indicators
- **MessageBubble**: Individual message component with reactions, editing, actions
- **ChatContext**: Real-time WebSocket context for chat state management
- **Message Bubbles**: Instagram-style message UI with read receipts, reactions

### Real-time Features
- **Live Messaging**: Real-time message delivery via WebSocket
- **Typing Indicators**: Show when users are typing
- **Read Receipts**: Message read status with timestamps
- **Message Reactions**: Emoji reactions to messages
- **Online Status**: User presence indicators
- **Live Notifications**: Real-time chat notifications

## Backend Implementation

### Database Models

**ChatRoom Model:**
```python
class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=20, choices=[('direct', 'Direct Message'), ('group', 'Group Chat')])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    participants = models.ManyToManyField(User, related_name='chat_rooms', through='ChatParticipant')
    is_active = models.BooleanField(default=True)
    last_message = models.TextField(blank=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Message Model:**
```python
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'), ('image', 'Image'), ('video', 'Video'), 
        ('audio', 'Audio'), ('file', 'File'), ('reel_share', 'Reel Share'), 
        ('profile_share', 'Profile Share')
    ])
    media_file = models.FileField(upload_to='chat_media/', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**ChatParticipant Model:**
```python
class ChatParticipant(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('member', 'Member')])
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
```

**Supporting Models:**
- `MessageReaction` - Emoji reactions to messages
- `MessageRead` - Read receipts for messages
- `TypingIndicator` - Real-time typing status
- `ChatAnalytics` - User chat statistics

### API Endpoints

**Inbox Management:**
- `GET /api/chat/inbox/` - Get user's inbox with unread counts
- `GET /api/chat/inbox/summary/` - Get inbox summary with statistics
- `POST /api/chat/inbox/direct-message/` - Create direct message conversation
- `GET /api/chat/rooms/{room_id}/` - Get detailed chat room information
- `POST /api/chat/inbox/rooms/{room_id}/read/` - Mark room as read
- `POST /api/chat/inbox/rooms/{room_id}/archive/` - Archive conversation
- `POST /api/chat/inbox/rooms/{room_id}/mute/` - Mute notifications
- `DELETE /api/chat/inbox/rooms/{room_id}/delete/` - Delete conversation
- `GET /api/chat/inbox/search/` - Search conversations
- `GET /api/chat/inbox/rooms/{room_id}/history/` - Get message history

**Basic Chat Functionality:**
- `POST /api/chat/send-message/` - Send message to room
- `GET /api/chat/rooms/{room_id}/messages/` - Get room messages
- `POST /api/chat/mark-read/` - Mark message as read
- `POST /api/chat/react/` - Add/remove reaction to message
- `POST /api/chat/start-typing/` - Start typing indicator
- `POST /api/chat/stop-typing/` - Stop typing indicator
- `GET /api/chat/unread-count/` - Get unread message count
- `GET /api/chat/analytics/` - Get chat analytics

### Real-time WebSocket

**Chat Consumers:**
```python
class ChatConsumer(AsyncWebsocketConsumer):
    # Personal chat notifications
    # Room subscription/unsubscription
    # Direct message notifications

class ContentChatConsumer(AsyncWebsocketConsumer):
    # Room-specific chat updates
    # Live message delivery
    # Typing indicators
    # Message reactions

class UserChatConsumer(AsyncWebsocketConsumer):
    # User-specific chat updates
    # Direct message notifications
    # Read receipts
```

**WebSocket Events:**
- `chat_message` - New message delivery
- `message_reaction` - Message reactions
- `typing_indicator` - Typing status updates
- `messages_read` - Read receipts
- `new_direct_message` - New DM notification
- `message_updated` - Message edits/deletes

### Signal Handlers

**Message Events:**
```python
@receiver(post_save, sender=Message)
def handle_message_created(sender, instance, created, **kwargs):
    if created:
        # Update room's last message
        # Send WebSocket notification to room
        # Create notifications for participants
        # Send personal notifications
```

**Reaction Events:**
```python
@receiver(post_save, sender=MessageReaction)
def handle_reaction_created(sender, instance, created, **kwargs):
    if created:
        # Send WebSocket notification to room
        # Update message reactions
```

**Read Events:**
```python
@receiver(post_save, sender=MessageRead)
def handle_message_read(sender, instance, created, **kwargs):
    if created:
        # Send WebSocket notification to room
        # Update read receipts
```

## Frontend Implementation

### Chat API Service

**Complete Chat Integration:**
```typescript
export const chatApi = {
  // Inbox functionality
  getInbox: () => apiClient.get<InboxRoom[]>('/chat/inbox/'),
  getInboxSummary: () => apiClient.get<InboxSummary>('/chat/inbox/summary/'),
  createDirectMessage: (recipientId: string, initialMessage?: string) =>
    apiClient.post<{ room: InboxRoom; message: string }>('/chat/inbox/direct-message/', {
      recipient_id: recipientId,
      initial_message: initialMessage
    }),
  
  // Room management
  getChatRoom: (roomId: string) => apiClient.get<ChatRoom>(`/chat/rooms/${roomId}/`),
  markRoomAsRead: (roomId: string) => apiClient.post(`/chat/inbox/rooms/${roomId}/read/`),
  archiveRoom: (roomId: string) => apiClient.post(`/chat/inbox/rooms/${roomId}/archive/`),
  muteRoom: (roomId: string, isMuted: boolean) => 
    apiClient.post(`/chat/inbox/rooms/${roomId}/mute/`, { is_muted: isMuted }),
  deleteRoom: (roomId: string) => apiClient.delete(`/chat/inbox/rooms/${roomId}/delete/`),
  
  // Search and history
  searchConversations: (query: string) => 
    apiClient.get<{ query: string; results: InboxRoom[] }>('/chat/inbox/search/', { params: { q: query } }),
  getMessageHistory: (roomId: string, page = 1, pageSize = 50, search?: string) =>
    apiClient.get<MessageHistory>(`/chat/inbox/rooms/${roomId}/history/`, {
      params: { page, page_size: pageSize, search }
    }),
  
  // Messaging
  sendMessage: (roomId: string, content: string, type = 'text', replyToId?: string) =>
    apiClient.post<Message>('/chat/send-message/', {
      room_id: roomId,
      content,
      message_type: type,
      reply_to_id: replyToId
    }),
  
  // Real-time features
  startTyping: (roomId: string) => apiClient.post('/chat/start-typing/', { room_id: roomId }),
  stopTyping: (roomId: string) => apiClient.post('/chat/stop-typing/', { room_id: roomId }),
  reactToMessage: (messageId: string, emoji: string) =>
    apiClient.post('/chat/react/', { message_id: messageId, emoji }),
  markMessageAsRead: (messageId: string) => apiClient.post('/chat/mark-read/', { message_id: messageId }),
};
```

### Chat Context

**Real-time WebSocket Context:**
```typescript
const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [currentRoom, setCurrentRoom] = useState<InboxRoom | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // WebSocket connection management
  // Real-time message handling
  // Typing indicators
  // Notifications
  // Auto-reconnection
}
```

### Inbox Component

**Complete Inbox Interface:**
```typescript
export function Inbox() {
  const [selectedRoom, setSelectedRoom] = useState<InboxRoom | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Get inbox rooms with unread counts
  const { data: inboxRooms = [] } = useQuery({
    queryKey: ['inbox'],
    queryFn: chatApi.getInbox,
    refetchInterval: 30000,
  });

  // Get inbox summary
  const { data: inboxSummary } = useQuery({
    queryKey: ['inboxSummary'],
    queryFn: chatApi.getInboxSummary,
    refetchInterval: 30000,
  });

  // Room actions (archive, mute, delete)
  // Search conversations
  // Real-time updates
  // Unread count management
}
```

### ConversationView Component

**Full Chat Interface:**
```typescript
export function ConversationView({ room, onBack }: ConversationViewProps) {
  const [messageText, setMessageText] = useState('');
  const [replyingTo, setReplyingTo] = useState<Message | null>(null);
  const [editingMessage, setEditingMessage] = useState<Message | null>(null);

  // Get detailed room information
  // Get messages with pagination
  // Send message mutation
  // Edit/delete message mutations
  // Real-time message updates
  // Typing indicators
  // Message reactions
  // Read receipts
}
```

### MessageBubble Component

**Instagram-style Message UI:**
```typescript
export function MessageBubble({
  message,
  isOwn,
  formatTime,
  onReply,
  onEdit,
  onDelete,
  showActions,
  setShowActions,
  isEditing,
  editText,
  setEditText,
  onSaveEdit,
  onCancelEdit
}: MessageBubbleProps) {
  // Message content rendering
  // Reply indicators
  // Reactions display
  // Message status (sent/delivered/read)
  // Edit mode
  // Action menu
  // Reaction menu
}
```

## Real-time Integration

### WebSocket Connection Management

**Auto-connect and Reconnect:**
```typescript
const connect = () => {
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`;
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('Chat WebSocket connected');
    setIsConnected(true);
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
  };
  
  ws.onclose = () => {
    console.log('Chat WebSocket disconnected');
    setIsConnected(false);
    // Auto-reconnect after 3 seconds
    setTimeout(() => connect(), 3000);
  };
};
```

### Real-time Message Handling

**WebSocket Message Types:**
```typescript
const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'chat_message':
      // New message received
      setMessages(prev => [...prev, data.message]);
      if (currentRoom?.id !== data.message.room) {
        setUnreadCount(prev => prev + 1);
      }
      break;

    case 'message_reaction':
      // Message reaction added/removed
      setMessages(prev => prev.map(msg => 
        msg.id === data.reaction.message_id
          ? { ...msg, reactions: [...(msg.reactions || []), data.reaction] }
          : msg
      ));
      break;

    case 'typing_indicator':
      // User typing indicator
      const { username, is_typing } = data;
      setTypingUsers(prev => {
        if (is_typing) {
          return prev.includes(username) ? prev : [...prev, username];
        } else {
          return prev.filter(u => u !== username);
        }
      });
      break;

    case 'messages_read':
      // Messages marked as read
      setMessages(prev => prev.map(msg => ({
        ...msg,
        is_read: msg.sender.id === data.user_id ? true : msg.is_read,
        read_receipts: msg.sender.id === data.user_id 
          ? [...(msg.read_receipts || []), { user: { id: data.user_id }, read_at: data.read_up_to }]
          : msg.read_receipts
      })));
      break;
  }
};
```

## Message Persistence & Storage

### Database Storage
- **All messages saved** to PostgreSQL database
- **Message metadata** stored in JSON field
- **Media files** stored in Django media storage
- **Read receipts** tracked with timestamps
- **Reactions** stored with user and emoji data

### Message Retrieval
- **Paginated message loading** for performance
- **Message search** functionality
- **Message history** with filtering options
- **Unread message tracking** per user

### Data Integrity
- **Message deletion** (soft delete) preserves conversation flow
- **Message editing** tracked with edit timestamps
- **Reply chains** maintained with parent-child relationships
- **Message status** tracking (sent, delivered, read)

## Notification Integration

### Chat Notifications
```python
# Message notification creation
Notification.objects.create(
    recipient=participant.user,
    sender=instance.sender,
    notification_type='message',
    content_type='chat_room',
    content_id=str(room.id),
    message=f"{instance.sender.first_name} {instance.sender.last_name}: {instance.content[:50]}..."
)
```

### Real-time Notifications
- **WebSocket notifications** sent instantly
- **Personal notification channels** for direct messages
- **Room notification channels** for group messages
- **Unread count updates** in real-time

### Notification Types
- `message` - New message notification
- `chat_request` - New direct message request
- `message_reaction` - Reaction to message
- `typing_indicator` - User typing status

## File Structure

```
backend/python/chat/
models.py              # Chat database models
views.py               # Basic chat API views
inbox_views.py         # Inbox and DM API views
serializers.py         # API serializers
urls.py               # URL configuration
consumers.py          # WebSocket consumers
signals.py            # Database signal handlers
tasks.py              # Background tasks
routing.py            # WebSocket routing
apps.py               # App configuration
admin.py              # Django admin interface
migrations/           # Database migrations

frontend/src/
components/Inbox.tsx              # Main inbox component
components/ConversationView.tsx   # Chat conversation interface
components/MessageBubble.tsx      # Individual message component
context/ChatContext.tsx           # Real-time WebSocket context
services/chatApi.ts               # Chat API service
```

## Usage Examples

### Frontend Integration

```typescript
// Wrap app with ChatProvider
<ChatProvider>
  <App />
</ChatProvider>

// Use inbox component
<Inbox />

// Use chat context in components
const { 
  isConnected, 
  currentRoom, 
  messages, 
  sendMessage, 
  sendTypingIndicator 
} = useChat();
```

### Backend Integration

```typescript
// Create direct message
const response = await chatApi.createDirectMessage(userId, "Hey there!");

// Send message
await chatApi.sendMessage(roomId, "Hello!", 'text');

// Mark as read
await chatApi.markRoomAsRead(roomId);

// Search conversations
const results = await chatApi.searchConversations("john");
```

### WebSocket Events

```typescript
// Listen for real-time messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chat_message') {
    // Handle new message
    addMessage(data.message);
  }
};

// Send typing indicator
ws.send(JSON.stringify({
  type: 'typing_indicator',
  room_id: roomId,
  is_typing: true
}));
```

---

## Status: Complete Implementation

The chat and inbox system is now **fully implemented** with:
- **Complete DM/inbox system** with message persistence
- **Real-time messaging** via WebSocket connections
- **Message bubbles** with Instagram-style UI
- **Inbox management** with unread counts and search
- **Notification integration** with existing notification system
- **Message persistence** in database with full history
- **Real-time features** including typing indicators and read receipts
- **Group chat support** with participant management
- **Media sharing** capabilities (images, videos, files)
- **Message reactions** and editing functionality

All messages are **saved to user accounts** with persistent storage, real-time updates, and comprehensive notification integration. The system provides a complete Instagram-like messaging experience with modern real-time features.
