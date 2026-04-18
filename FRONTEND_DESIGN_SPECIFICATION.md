# Frontend Design Specification - Instagran Platform

## Overview
This document outlines the required frontend components and features to integrate with the backend API for the Instagram-like neural social platform.

## Authentication & User Management

### 1. Authentication System
**Required Components:**
- **Login Page** (`/login`)
  - Email/Username login with password
  - "Continue with Google" button using OAuth 2.0
  - Remember me option
  - Forgot password link
  - Sign up link

- **Registration Page** (`/register`)
  - Email, username, password fields
  - First name, last name
  - "Sign up with Google" button
  - Terms of service checkbox
  - Email verification requirement

- **Social Auth Integration**
  - Google OAuth 2.0 with GSI (Google Sign-In)
  - Account linking for existing users
  - Social account management in profile settings
  - Unlink social accounts functionality

### 2. User Profile
**Required Features:**
- **Profile Editor** (`/profile/edit`)
  - Profile picture upload (crop/resize)
  - Bio/description field
  - Website, social links
  - Privacy settings (private/public account)
  - Neural category display
  - Linked social accounts management

- **Profile View** (`/profile/:username`)
  - Display user posts, followers, following
  - Neural category badges
  - Activity feed
  - Edit profile button (own profile only)

## Core Platform Features

### 3. Content Creation & Interaction
**Reels/Video Content:**
- **Reel Upload** (`/create/reel`)
  - Video file upload with progress bar
  - Thumbnail selection/cropping
  - Caption with hashtags and mentions
  - Music selection from library
  - Privacy settings (public/private)
  - Allow duet/stitch options
  - Location tagging

- **Reel Viewer** (`/reel/:id`)
  - Full-screen video player
  - Like, comment, share buttons
  - Creator profile preview
  - Related reels sidebar
  - Comments section with threading
  - Caption with clickable hashtags/mentions

- **Feed** (`/` and `/feed`)
  - Infinite scroll with pagination
  - Algorithm-based content ranking
  - Neural category filtering
  - Real-time updates via WebSocket
  - Story indicators at top
  - Swipe gestures for mobile

### 4. Social Connections
**Connection Management:**
- **User Discovery** (`/discover`)
  - Neural-based user recommendations
  - Trending users
  - Search by username/interests
  - Category-based browsing
  - "Auto-follow" suggestions

- **Follow System** (`/connections`)
  - Follow/unfollow with confirmation
  - Follower/following lists
  - Connection requests
  - Mutual connections indicator
  - Auto-follow settings management

- **Chat System** (`/messages` and `/chat/:id`)
  - Real-time messaging via WebSocket
  - Typing indicators
  - Read receipts
  - Message reactions
  - File/image sharing
  - Group chat creation
  - Online status indicators

## Neural Interface Features

### 5. Neural Categorization
**Category Display:**
- **User Categories** in profile badges
  - Technology, Social, Creative, Business
  - Entertainment, Sports, Travel, Food
  - Confidence score indicators
  - Category evolution over time

- **Smart Recommendations**
  - Content suggestions based on behavior
  - User matching with compatibility scores
  - Trending content in user's categories
  - Auto-follow recommendations

### 6. Analytics Dashboard
**User Analytics** (`/analytics`)
- **Engagement Metrics**
  - Views, likes, comments, shares
  - Follower growth charts
  - Post performance analytics
  - Best posting times
  - Demographic insights

- **Neural Insights**
  - Category behavior patterns
  - Interaction preferences
  - Content consumption habits
  - Social network analysis
  - Prediction accuracy metrics

## Technical Requirements

### 7. API Integration
**Authentication:**
```javascript
// JWT Token Management
const API_BASE_URL = 'http://localhost:8000/api';

// Login endpoint
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "password"
}

// Google OAuth
POST /api/users/social/google/login/
{
  "id_token": "google_id_token"
}

// Token refresh
POST /api/auth/refresh/
{
  "refresh": "refresh_token"
}
```

**Content APIs:**
```javascript
// Get feed
GET /api/reels/?page=1&limit=20

// Upload reel
POST /api/reels/
{
  "video_file": File,
  "caption": "Amazing content! #tech #innovation",
  "hashtags": ["tech", "innovation"],
  "music_track": "track_id"
}

// Get user recommendations
GET /api/neural/match/?user_id=uuid&limit=20

// Auto-follow
POST /api/neural/auto-follow/
{
  "confidence_threshold": 0.8,
  "max_follows": 10
}
```

### 8. WebSocket Integration
**Real-time Features:**
```javascript
// WebSocket connection
const socket = io('http://localhost:3000', {
  auth: {
    token: 'jwt_token'
  }
});

// Join chat room
socket.emit('join_room', { room_id: 'chat_uuid' });

// Send message
socket.emit('chat_message', {
  room_id: 'chat_uuid',
  content: 'Hello!',
  message_type: 'text'
});

// Receive messages
socket.on('new_message', (data) => {
  // Handle incoming message
});

// Notifications
socket.on('new_notification', (notification) => {
  // Handle real-time notification
});
```

## UI/UX Requirements

### 9. Responsive Design
**Mobile-First Approach:**
- **Breakpoints:**
  - Mobile: 320px - 768px
  - Tablet: 768px - 1024px
  - Desktop: 1024px+

**Components:**
- **Navigation** - Bottom tab bar on mobile, top nav on desktop
- **Feed** - Card-based layout, swipeable on mobile
- **Modals** - Full-screen overlays for actions
- **Forms** - Touch-friendly inputs with proper spacing

### 10. Modern UI Framework
**Technology Stack:**
- **React 18+** with hooks and context
- **TypeScript** for type safety
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for animations
- **React Query** for server state management
- **Zustand** for client state management

**Component Library:**
- **Headless UI** (Radix UI, Shadcn/ui)
- **Icons** (Lucide React)
- **Forms** (React Hook Form)
- **Date Handling** (date-fns)
- **File Uploads** (React Dropzone)

### 11. Performance Requirements
**Optimization:**
- **Code Splitting** - Route-based lazy loading
- **Image Optimization** - WebP format, lazy loading
- **Caching** - Service worker for offline support
- **Bundle Size** - < 2MB initial load
- **Time to Interactive** - < 3 seconds

**Metrics:**
- **Lighthouse Score** - 90+ performance
- **Core Web Vitals** - LCP < 2.5s, FID < 100ms
- **Mobile Performance** - 60fps on mid-range devices

## Security & Privacy

### 12. Security Features
**Frontend Security:**
- **XSS Protection** - Input sanitization
- **CSRF Protection** - Token-based forms
- **Secure Storage** - HttpOnly cookies for tokens
- **Content Security Policy** - Proper headers
- **HTTPS Only** - Production deployment

**Privacy Controls:**
- **Data Export** - Download user data
- **Account Deletion** - Permanent removal option
- **Privacy Settings** - Granular controls
- **Data Minimization** - Only collect necessary data
- **GDPR Compliance** - Right to be forgotten

### 13. Accessibility
**WCAG 2.1 AA Compliance:**
- **Keyboard Navigation** - Full keyboard access
- **Screen Reader Support** - Proper ARIA labels
- **High Contrast Mode** - Toggle option
- **Focus Management** - Visible focus indicators
- **Alt Text** - All images have descriptions
- **Semantic HTML** - Proper heading structure

## Deployment & Integration

### 14. Environment Configuration
**Development:**
```javascript
const config = {
  API_BASE_URL: 'http://localhost:8000',
  WS_URL: 'http://localhost:3000',
  GOOGLE_CLIENT_ID: 'dev_client_id',
  ENVIRONMENT: 'development'
};
```

**Production:**
```javascript
const config = {
  API_BASE_URL: 'https://api.instagran.com',
  WS_URL: 'https://ws.instagran.com',
  GOOGLE_CLIENT_ID: 'prod_client_id',
  ENVIRONMENT: 'production'
};
```

### 15. Build Process
**Development Workflow:**
- **Hot Reload** - Vite dev server
- **API Proxy** - Backend proxy configuration
- **Environment Variables** - .env file support
- **Type Checking** - TypeScript strict mode
- **Linting** - ESLint + Prettier

**Production Build:**
- **Static Generation** - Optimized assets
- **Bundle Analysis** - Webpack Bundle Analyzer
- **Tree Shaking** - Dead code elimination
- **Minification** - Uglify/Terser
- **Source Maps** - For debugging

## Testing Strategy

### 16. Testing Requirements
**Unit Tests:**
- **Component Tests** - Jest + React Testing Library
- **Hook Tests** - Custom hook testing
- **Utility Tests** - Helper function testing
- **API Mocking** - MSW for API simulation

**Integration Tests:**
- **E2E Testing** - Playwright or Cypress
- **API Testing** - Supertest for backend
- **WebSocket Testing** - Socket testing utilities
- **Cross-browser Testing** - BrowserStack or Sauce Labs

**Performance Testing:**
- **Load Testing** - Artillery for API
- **Stress Testing** - High concurrent users
- **Memory Profiling** - Chrome DevTools
- **Network Throttling** - Slow 3G simulation

## Launch Features

### 17. Onboarding
**New User Experience:**
- **Welcome Tour** - Interactive platform walkthrough
- **Interest Selection** - Choose categories to follow
- **Profile Completion** - Guided profile setup
- **First Connections** - Suggested users to follow
- **Content Discovery** - Trending content showcase

### 18. Growth Features
**User Engagement:**
- **Push Notifications** - Browser and mobile support
- **Email Digests** - Weekly activity summaries
- **Achievement System** - Milestone celebrations
- **Referral Program** - Invite friends benefits
- **Content Challenges** - Community engagement

---

## Implementation Priority

### Phase 1: Core Authentication (Week 1)
1. Login/registration pages
2. Google OAuth integration
3. JWT token management
4. Protected routes

### Phase 2: Basic Platform (Week 2-3)
1. User profiles
2. Content feed
3. Basic interactions (like, comment)
4. Real-time chat

### Phase 3: Advanced Features (Week 4-5)
1. Neural recommendations
2. Auto-follow system
3. Analytics dashboard
4. Content creation tools

### Phase 4: Polish & Optimization (Week 6)
1. Performance optimization
2. Mobile responsiveness
3. Accessibility improvements
4. Security hardening

This specification provides a comprehensive guide for frontend developers to build a modern, scalable Instagram-like platform that fully integrates with our neural backend features.
