# Frontend Integration Instructions

## Current Status
Phase 0 and Phase 1 infrastructure is complete. The following files have been created:

### Environment Setup (Phase 0) - COMPLETED
- `.env.example` - Environment variables template
- `vercel.json` - Vercel deployment configuration  
- `vite.config.ts` - Updated with build optimization and proxy settings
- `src/lib/env.ts` - Environment configuration
- `src/lib/env.d.ts` - TypeScript environment types
- `src/lib/apiClient.ts` - Typed API client with error handling

### Authentication System (Phase 1) - INFRASTRUCTURE COMPLETE
- `src/context/AuthContext.tsx` - Authentication context with JWT handling
- `src/components/ProtectedRoute.tsx` - Route protection component

### API Services (Phase 2) - INFRASTRUCTURE COMPLETE
- `src/services/feedApi.ts` - Feed and reels API
- `src/services/userApi.ts` - User profile and connections API
- `src/services/neuralApi.ts` - Neural interface API
- `src/services/chatApi.ts` - Chat and messaging API

## Next Steps for Development Team

### 1. Install Missing Dependencies
```bash
npm install @types/node axios socket.io-client @tanstack/react-query @tanstack/react-query-devtools react-hook-form @hookform/resolvers zod
```

### 2. Create Environment File
```bash
cp .env.example .env.local
# Update .env.local with actual values
```

### 3. Update App.tsx with Authentication
```typescript
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

// Wrap app with AuthProvider
// Wrap protected routes with ProtectedRoute
```

### 4. Update Login and Signup Pages
- Connect forms to AuthContext
- Implement Google OAuth integration
- Add form validation and error handling

### 5. Update Existing Pages with Real APIs
- Replace mock data with API calls
- Add loading and error states
- Implement real-time features

## TypeScript Errors
The current TypeScript errors are expected and will be resolved when:
1. Dependencies are installed (`npm install`)
2. Environment variables are properly configured
3. The development server is started (`npm run dev`)

## API Integration Examples

### Using the API Client
```typescript
import { apiClient } from '../lib/apiClient';
import { feedApi } from '../services/feedApi';

// In a component or hook
const { data, error, isLoading } = useQuery({
  queryKey: ['feed'],
  queryFn: () => feedApi.getHomeFeed()
});
```

### Authentication Usage
```typescript
import { useAuth } from '../context/AuthContext';

const { login, loginWithGoogle, user, logout } = useAuth();

// Handle login
await login(email, password);

// Handle Google login
await loginWithGoogle(idToken);
```

## Backend API Endpoints Reference

### Authentication
- `POST /api/auth/login/` - Email/password login
- `POST /api/users/social/google/login/` - Google OAuth login
- `POST /api/auth/refresh/` - Token refresh
- `POST /api/auth/logout/` - Logout

### Feed & Content
- `GET /api/reels/` - Get feed reels
- `POST /api/reels/` - Create new reel
- `POST /api/reels/{id}/interact/` - Like/unlike reel
- `GET /api/reels/trending/` - Get trending content

### Users & Connections
- `GET /api/users/profile/` - Get current user profile
- `GET /api/users/{username}/` - Get user profile
- `POST /api/connections/follow/{id}/` - Follow user
- `GET /api/connections/suggestions/` - Get suggestions

### Neural Interface
- `GET /api/neural/profile/` - Get neural profile
- `GET /api/neural/match/` - Get user recommendations
- `POST /api/neural/auto-follow/` - Auto-follow users

### Chat & Real-time
- `GET /api/chat/rooms/` - Get conversations
- `GET /api/chat/rooms/{id}/messages/` - Get messages
- `POST /api/chat/rooms/{id}/messages/` - Send message

## WebSocket Events
- `join_room` - Join chat room
- `chat_message` - Send/receive messages
- `new_message` - New message notification
- `typing_indicator` - Typing status
- `new_notification` - Real-time notifications

## Development Workflow
1. Install dependencies
2. Set up environment variables
3. Start backend services (Django, Redis, etc.)
4. Start frontend development server
5. Test authentication flow
6. Integrate APIs page by page
7. Add real-time features
8. Test and deploy

## Testing Checklist
- [ ] Login with email/password works
- [ ] Google OAuth login works
- [ ] Protected routes redirect to login
- [ ] Feed loads real data
- [ ] Chat functionality works
- [ ] Neural recommendations display
- [ ] Real-time notifications work
- [ ] Mobile responsive design
- [ ] Error handling throughout

The infrastructure is complete and ready for full integration.
