const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const http = require('http');
const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./config/swagger');
const config = require('./config');
const routes = require('./routes');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const logger = require('./utils/logger');
const { initWebSocket } = require('./websocket');
const { initRedis, closeRedis } = require('./config/redis');
const { initQueues, closeQueues } = require('./config/queue');

const app = express();

// Create HTTP server for WebSocket support
const server = http.createServer(app);

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors(config.cors));

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Logging middleware - use Winston HTTP logger for file persistence
if (config.env !== 'test') {
  // Morgan for detailed Apache-style logs to console
  app.use(morgan('combined', { stream: logger.stream }));
  // Custom HTTP logger for structured logging
  app.use(logger.httpLogger);
}

// Swagger documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec, {
  explorer: true,
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'AI Anti-Spam Shield API Documentation'
}));

// Swagger JSON endpoint
app.get('/api-docs.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(swaggerSpec);
});

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    status: 'success',
    message: 'Server is running',
    timestamp: new Date().toISOString(),
    services: {
      api: 'healthy',
    }
  };

  // Check Redis connection if available
  try {
    const { redis } = require('./config/redis');
    await redis.ping();
    health.services.redis = 'healthy';
  } catch (error) {
    health.services.redis = 'unavailable';
  }

  res.status(200).json(health);
});

// API routes
app.use(`/api/${config.apiVersion}`, routes);

// Error handling
app.use(notFoundHandler);
app.use(errorHandler);

// Initialize services and start server
const PORT = config.port || 3000;

const startServer = async () => {
  try {
    // Initialize Redis connection
    const redisConnected = await initRedis();
    if (redisConnected) {
      logger.info('Redis connected successfully');

      // Initialize queues (only if Redis is connected)
      await initQueues();
      logger.info('Message queues initialized');
    } else {
      logger.warn('Redis not available, running without queue support');
    }

    // Initialize WebSocket server
    initWebSocket(server);
    logger.info('WebSocket server initialized');

    // Start HTTP server
    server.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`, { mode: config.env, port: PORT });
    });
  } catch (error) {
    logger.error('Failed to start server', { error: error.message });
    process.exit(1);
  }
};

// Graceful shutdown
const shutdown = async (signal) => {
  logger.info(`Received ${signal}, shutting down gracefully...`);

  server.close(async () => {
    logger.info('HTTP server closed');

    try {
      await closeQueues();
      await closeRedis();
      logger.info('All connections closed');
      process.exit(0);
    } catch (error) {
      logger.error('Error during shutdown', { error: error.message });
      process.exit(1);
    }
  });

  // Force shutdown after 30 seconds
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

// Start the server
startServer();

module.exports = app;
