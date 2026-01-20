const { Server } = require('socket.io');
const logger = require('../utils/logger');
const jwt = require('jsonwebtoken');

let io = null;

/**
 * Initialize WebSocket server
 * @param {Object} httpServer - HTTP server instance
 * @returns {Object} Socket.IO server instance
 */
const initWebSocket = (httpServer) => {
  io = new Server(httpServer, {
    cors: {
      origin: process.env.CORS_ORIGIN || '*',
      methods: ['GET', 'POST'],
      credentials: true,
    },
    pingTimeout: 60000,
    pingInterval: 25000,
  });

  // Authentication middleware
  io.use((socket, next) => {
    const token = socket.handshake.auth.token || socket.handshake.headers.authorization?.split(' ')[1];

    if (!token) {
      // Allow anonymous connections for basic notifications
      socket.userId = null;
      return next();
    }

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.userId = decoded.userId;
      next();
    } catch (error) {
      logger.warn('WebSocket auth failed', { error: error.message });
      // Allow connection but without user context
      socket.userId = null;
      next();
    }
  });

  // Connection handler
  io.on('connection', (socket) => {
    logger.info('WebSocket client connected', {
      socketId: socket.id,
      userId: socket.userId,
    });

    // Join user-specific room if authenticated
    if (socket.userId) {
      socket.join(`user:${socket.userId}`);
      logger.debug(`Socket ${socket.id} joined room user:${socket.userId}`);
    }

    // Subscribe to job updates
    socket.on('subscribe:job', (jobId) => {
      socket.join(`job:${jobId}`);
      logger.debug(`Socket ${socket.id} subscribed to job:${jobId}`);
    });

    // Unsubscribe from job updates
    socket.on('unsubscribe:job', (jobId) => {
      socket.leave(`job:${jobId}`);
      logger.debug(`Socket ${socket.id} unsubscribed from job:${jobId}`);
    });

    // Handle disconnection
    socket.on('disconnect', (reason) => {
      logger.info('WebSocket client disconnected', {
        socketId: socket.id,
        userId: socket.userId,
        reason,
      });
    });

    // Error handling
    socket.on('error', (error) => {
      logger.error('WebSocket error', {
        socketId: socket.id,
        error: error.message,
      });
    });
  });

  logger.info('WebSocket server initialized');
  return io;
};

/**
 * Get Socket.IO instance
 * @returns {Object|null} Socket.IO server instance
 */
const getIO = () => io;

/**
 * Emit event to user room
 * @param {string} userId - User ID
 * @param {string} event - Event name
 * @param {Object} data - Event data
 */
const emitToUser = (userId, event, data) => {
  if (io && userId) {
    io.to(`user:${userId}`).emit(event, data);
  }
};

/**
 * Emit event to job room
 * @param {string} jobId - Job ID
 * @param {string} event - Event name
 * @param {Object} data - Event data
 */
const emitToJob = (jobId, event, data) => {
  if (io && jobId) {
    io.to(`job:${jobId}`).emit(event, data);
  }
};

/**
 * Broadcast event to all connected clients
 * @param {string} event - Event name
 * @param {Object} data - Event data
 */
const broadcast = (event, data) => {
  if (io) {
    io.emit(event, data);
  }
};

module.exports = {
  initWebSocket,
  getIO,
  emitToUser,
  emitToJob,
  broadcast,
  get io() {
    return io;
  },
};
