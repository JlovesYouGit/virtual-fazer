const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const redis = require('redis');
const { Pool } = require('pg');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const Joi = require('joi');
const winston = require('winston');

// Load environment variables
require('dotenv').config();

// Initialize Express app
const app = express();
const server = http.createServer(app);

// Initialize Socket.IO
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Winston logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Redis client (Redis v4+ syntax)
const redisClient = redis.createClient({
  url: `redis://${process.env.REDIS_HOST || 'localhost'}:${process.env.REDIS_PORT || 6379}`,
  password: process.env.REDIS_PASSWORD || undefined
});

redisClient.on('error', (err) => {
  logger.error('Redis error:', err);
});

redisClient.on('connect', () => {
  logger.info('Connected to Redis');
});

// Connect to Redis (required for Redis v4+)
redisClient.connect().catch(err => {
  logger.error('Failed to connect to Redis:', err);
});

// PostgreSQL pool
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'instagran',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  logger.error('PostgreSQL error:', err);
});

// In-memory storage for active connections
const activeUsers = new Map();
const userSockets = new Map();
const chatRooms = new Map();

// JWT middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }
    req.user = user;
    next();
  });
};

// Validation schemas
const messageSchema = Joi.object({
  room_id: Joi.string().uuid().required(),
  content: Joi.string().max(2000).required(),
  message_type: Joi.string().valid('text', 'image', 'video', 'audio', 'file').default('text'),
  reply_to_id: Joi.string().uuid().allow(null)
});

const notificationSchema = Joi.object({
  user_id: Joi.string().uuid().required(),
  type: Joi.string().valid('like', 'comment', 'follow', 'message', 'mention').required(),
  title: Joi.string().max(100).required(),
  message: Joi.string().max(500).required(),
  metadata: Joi.object().default({})
});

// Socket.IO authentication middleware
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  
  if (!token) {
    return next(new Error('Authentication token required'));
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, decoded) => {
    if (err) {
      return next(new Error('Invalid token'));
    }
    socket.userId = decoded.userId;
    socket.username = decoded.username;
    next();
  });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`User ${socket.username} connected with socket ${socket.id}`);
  
  // Store user socket mapping
  userSockets.set(socket.userId, socket.id);
  activeUsers.set(socket.userId, {
    username: socket.username,
    socketId: socket.id,
    connectedAt: new Date(),
    lastActivity: new Date()
  });

  // Join user to their personal room for notifications
  socket.join(`user:${socket.userId}`);

  // Handle joining chat rooms
  socket.on('join_room', async (data) => {
    try {
      const { roomId } = data;
      
      // Verify user is participant in the room
      const result = await pool.query(
        'SELECT 1 FROM chat_chatparticipant WHERE user_id = $1 AND room_id = $2',
        [socket.userId, roomId]
      );

      if (result.rows.length === 0) {
        socket.emit('error', { message: 'Not authorized to join this room' });
        return;
      }

      socket.join(roomId);
      
      if (!chatRooms.has(roomId)) {
        chatRooms.set(roomId, new Set());
      }
      chatRooms.get(roomId).add(socket.userId);

      // Notify others in the room
      socket.to(roomId).emit('user_joined', {
        userId: socket.userId,
        username: socket.username,
        timestamp: new Date()
      });

      // Update last activity
      const user = activeUsers.get(socket.userId);
      if (user) {
        user.lastActivity = new Date();
      }

    } catch (error) {
      logger.error('Error joining room:', error);
      socket.emit('error', { message: 'Failed to join room' });
    }
  });

  // Handle leaving chat rooms
  socket.on('leave_room', (roomId) => {
    socket.leave(roomId);
    
    if (chatRooms.has(roomId)) {
      chatRooms.get(roomId).delete(socket.userId);
      if (chatRooms.get(roomId).size === 0) {
        chatRooms.delete(roomId);
      }
    }

    socket.to(roomId).emit('user_left', {
      userId: socket.userId,
      username: socket.username,
      timestamp: new Date()
    });
  });

  // Handle chat messages
  socket.on('chat_message', async (data) => {
    try {
      const { error, value } = messageSchema.validate(data);
      if (error) {
        socket.emit('error', { message: 'Invalid message format' });
        return;
      }

      const { room_id, content, message_type, reply_to_id } = value;

      // Verify user is in the room
      const roomCheck = await pool.query(
        'SELECT 1 FROM chat_chatparticipant WHERE user_id = $1 AND room_id = $2',
        [socket.userId, room_id]
      );

      if (roomCheck.rows.length === 0) {
        socket.emit('error', { message: 'Not authorized to send messages to this room' });
        return;
      }

      // Create message in database
      const messageResult = await pool.query(
        `INSERT INTO chat_message (id, room_id, sender_id, content, message_type, reply_to_id, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, NOW())
         RETURNING *`,
        [uuidv4(), room_id, socket.userId, content, message_type, reply_to_id]
      );

      const message = messageResult.rows[0];

      // Update room's last message
      await pool.query(
        'UPDATE chat_chatroom SET last_message = $1, last_message_time = NOW() WHERE id = $2',
        [content, room_id]
      );

      // Broadcast message to room
      io.to(room_id).emit('new_message', {
        id: message.id,
        room_id: message.room_id,
        sender: {
          id: socket.userId,
          username: socket.username
        },
        content: message.content,
        message_type: message.message_type,
        reply_to_id: message.reply_to_id,
        created_at: message.created_at
      });

      // Update last activity
      const user = activeUsers.get(socket.userId);
      if (user) {
        user.lastActivity = new Date();
      }

      // Cache message in Redis
      await redisClient.setex(`message:${message.id}`, 3600, JSON.stringify(message));

    } catch (error) {
      logger.error('Error handling chat message:', error);
      socket.emit('error', { message: 'Failed to send message' });
    }
  });

  // Handle typing indicators
  socket.on('typing_start', (roomId) => {
    socket.to(roomId).emit('user_typing', {
      userId: socket.userId,
      username: socket.username,
      isTyping: true
    });
  });

  socket.on('typing_stop', (roomId) => {
    socket.to(roomId).emit('user_typing', {
      userId: socket.userId,
      username: socket.username,
      isTyping: false
    });
  });

  // Handle real-time notifications
  socket.on('mark_notification_read', async (notificationId) => {
    try {
      await pool.query(
        'UPDATE notification SET read_at = NOW() WHERE id = $1 AND user_id = $2',
        [notificationId, socket.userId]
      );
    } catch (error) {
      logger.error('Error marking notification as read:', error);
    }
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    logger.info(`User ${socket.username} disconnected`);
    
    // Clean up user data
    userSockets.delete(socket.userId);
    activeUsers.delete(socket.userId);
    
    // Remove from all chat rooms
    chatRooms.forEach((participants, roomId) => {
      if (participants.has(socket.userId)) {
        participants.delete(socket.userId);
        socket.to(roomId).emit('user_left', {
          userId: socket.userId,
          username: socket.username,
          timestamp: new Date()
        });
      }
    });
  });
});

// REST API Routes

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date(),
    activeConnections: activeUsers.size,
    activeRooms: chatRooms.size
  });
});

// Get active users
app.get('/api/v1/users/active', authenticateToken, (req, res) => {
  const users = Array.from(activeUsers.values()).map(user => ({
    userId: Object.keys(activeUsers).find(key => activeUsers.get(key) === user),
    username: user.username,
    connectedAt: user.connectedAt,
    lastActivity: user.lastActivity
  }));
  
  res.json({ activeUsers: users });
});

// Send notification
app.post('/api/v1/notifications/send', authenticateToken, async (req, res) => {
  try {
    const { error, value } = notificationSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { user_id, type, title, message, metadata } = value;

    // Create notification in database
    const notificationResult = await pool.query(
      `INSERT INTO notification (id, user_id, type, title, message, metadata, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, NOW())
       RETURNING *`,
      [uuidv4(), user_id, type, title, message, JSON.stringify(metadata)]
    );

    const notification = notificationResult.rows[0];

    // Send real-time notification if user is online
    if (userSockets.has(user_id)) {
      io.to(`user:${user_id}`).emit('new_notification', {
        id: notification.id,
        type: notification.type,
        title: notification.title,
        message: notification.message,
        metadata: notification.metadata,
        created_at: notification.created_at
      });
    }

    res.status(201).json({ notification });

  } catch (error) {
    logger.error('Error sending notification:', error);
    res.status(500).json({ error: 'Failed to send notification' });
  }
});

// Get user notifications
app.get('/api/v1/notifications/:user_id', authenticateToken, async (req, res) => {
  try {
    const { user_id } = req.params;
    const limit = parseInt(req.query.limit) || 20;
    const offset = parseInt(req.query.offset) || 0;

    const result = await pool.query(
      `SELECT * FROM notification 
       WHERE user_id = $1 
       ORDER BY created_at DESC 
       LIMIT $2 OFFSET $3`,
      [user_id, limit, offset]
    );

    res.json({ notifications: result.rows });

  } catch (error) {
    logger.error('Error fetching notifications:', error);
    res.status(500).json({ error: 'Failed to fetch notifications' });
  }
});

// Get chat rooms for user
app.get('/api/v1/chat/rooms/:user_id', authenticateToken, async (req, res) => {
  try {
    const { user_id } = req.params;

    const result = await pool.query(
      `SELECT cr.*, cp.last_read, u.username as other_username
       FROM chat_chatroom cr
       JOIN chat_chatparticipant cp ON cr.id = cp.room_id
       LEFT JOIN chat_chatparticipant cp2 ON cr.id = cp2.room_id AND cp2.user_id != $1
       LEFT JOIN users_user u ON cp2.user_id = u.id
       WHERE cp.user_id = $1
       ORDER BY cr.last_message_time DESC NULLS LAST`,
      [user_id]
    );

    res.json({ rooms: result.rows });

  } catch (error) {
    logger.error('Error fetching chat rooms:', error);
    res.status(500).json({ error: 'Failed to fetch chat rooms' });
  }
});

// Get messages for room
app.get('/api/v1/chat/rooms/:room_id/messages', authenticateToken, async (req, res) => {
  try {
    const { room_id } = req.params;
    const limit = parseInt(req.query.limit) || 50;
    const offset = parseInt(req.query.offset) || 0;

    // Verify user is participant
    const participantCheck = await pool.query(
      'SELECT 1 FROM chat_chatparticipant WHERE user_id = $1 AND room_id = $2',
      [req.user.userId, room_id]
    );

    if (participantCheck.rows.length === 0) {
      return res.status(403).json({ error: 'Not authorized to access this room' });
    }

    const result = await pool.query(
      `SELECT m.*, u.username as sender_username
       FROM chat_message m
       JOIN users_user u ON m.sender_id = u.id
       WHERE m.room_id = $1 AND m.is_deleted = false
       ORDER BY m.created_at ASC
       LIMIT $2 OFFSET $3`,
      [room_id, limit, offset]
    );

    res.json({ messages: result.rows });

  } catch (error) {
    logger.error('Error fetching messages:', error);
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
});

// Real-time metrics endpoint
app.get('/api/v1/metrics/realtime', authenticateToken, (req, res) => {
  const metrics = {
    activeUsers: activeUsers.size,
    activeRooms: chatRooms.size,
    totalConnections: userSockets.size,
    timestamp: new Date()
  };

  res.json(metrics);
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  logger.info(`Node.js WebSocket service running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  
  server.close(() => {
    logger.info('HTTP server closed');
    
    pool.end(() => {
      logger.info('Database pool closed');
      redisClient.quit(() => {
        logger.info('Redis client closed');
        process.exit(0);
      });
    });
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.emit('SIGTERM');
});
