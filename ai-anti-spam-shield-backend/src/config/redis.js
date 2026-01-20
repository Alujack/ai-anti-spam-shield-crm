const Redis = require('ioredis');
const logger = require('../utils/logger');

// Redis connection configuration
const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT) || 6379,
  password: process.env.REDIS_PASSWORD || undefined,
  db: parseInt(process.env.REDIS_DB) || 0,
  maxRetriesPerRequest: 3,
  retryDelayOnFailover: 100,
  enableReadyCheck: true,
  lazyConnect: true,
};

// Create Redis client
const redis = new Redis(redisConfig);

// Connection event handlers
redis.on('connect', () => {
  logger.info('Redis: Connecting...');
});

redis.on('ready', () => {
  logger.info('Redis: Connected and ready');
});

redis.on('error', (err) => {
  logger.error('Redis: Connection error', { error: err.message });
});

redis.on('close', () => {
  logger.warn('Redis: Connection closed');
});

redis.on('reconnecting', () => {
  logger.info('Redis: Reconnecting...');
});

// Graceful shutdown
const closeRedis = async () => {
  try {
    await redis.quit();
    logger.info('Redis: Connection closed gracefully');
  } catch (error) {
    logger.error('Redis: Error closing connection', { error: error.message });
  }
};

// Parse Redis URL if provided
const parseRedisUrl = (url) => {
  if (!url) return redisConfig;

  try {
    const parsed = new URL(url);
    return {
      host: parsed.hostname,
      port: parseInt(parsed.port) || 6379,
      password: parsed.password || undefined,
      db: parseInt(parsed.pathname?.slice(1)) || 0,
    };
  } catch (error) {
    logger.error('Redis: Failed to parse URL', { error: error.message });
    return redisConfig;
  }
};

// Initialize with URL if provided
const initRedis = async () => {
  const config = process.env.REDIS_URL
    ? parseRedisUrl(process.env.REDIS_URL)
    : redisConfig;

  Object.assign(redis.options, config);

  try {
    await redis.connect();
    // Test connection
    await redis.ping();
    logger.info('Redis: Connection test successful');
    return true;
  } catch (error) {
    logger.error('Redis: Failed to connect', { error: error.message });
    return false;
  }
};

module.exports = {
  redis,
  initRedis,
  closeRedis,
  redisConfig,
};
