const { redis } = require('../../config/redis');
const logger = require('../../utils/logger');

class CacheService {
  constructor() {
    this.prefix = 'ai-shield:';
    this.defaultTTL = 3600; // 1 hour
  }

  /**
   * Get cached prediction by hash
   */
  async getCachedPrediction(hash) {
    try {
      const key = `${this.prefix}prediction:${hash}`;
      const cached = await redis.get(key);

      if (cached) {
        logger.debug('Cache hit', { key });
        return JSON.parse(cached);
      }

      return null;
    } catch (error) {
      logger.error('Cache get error', { error: error.message });
      return null;
    }
  }

  /**
   * Cache prediction result
   */
  async cachePrediction(hash, result, ttl = this.defaultTTL) {
    try {
      const key = `${this.prefix}prediction:${hash}`;
      await redis.setex(key, ttl, JSON.stringify(result));
      logger.debug('Cached prediction', { key, ttl });
    } catch (error) {
      logger.error('Cache set error', { error: error.message });
    }
  }

  /**
   * Invalidate cached prediction
   */
  async invalidatePrediction(hash) {
    try {
      const key = `${this.prefix}prediction:${hash}`;
      await redis.del(key);
      logger.debug('Invalidated cache', { key });
    } catch (error) {
      logger.error('Cache invalidate error', { error: error.message });
    }
  }

  /**
   * Get user session data
   */
  async getUserSession(userId) {
    try {
      const key = `${this.prefix}session:${userId}`;
      const session = await redis.get(key);
      return session ? JSON.parse(session) : null;
    } catch (error) {
      logger.error('Get session error', { error: error.message });
      return null;
    }
  }

  /**
   * Set user session data
   */
  async setUserSession(userId, data, ttl = 86400) {
    try {
      const key = `${this.prefix}session:${userId}`;
      await redis.setex(key, ttl, JSON.stringify(data));
    } catch (error) {
      logger.error('Set session error', { error: error.message });
    }
  }

  /**
   * Get rate limit count for key
   */
  async getRateLimit(key) {
    try {
      const fullKey = `${this.prefix}ratelimit:${key}`;
      const count = await redis.get(fullKey);
      return count ? parseInt(count, 10) : 0;
    } catch (error) {
      logger.error('Get rate limit error', { error: error.message });
      return 0;
    }
  }

  /**
   * Increment rate limit
   */
  async incrementRateLimit(key, ttl = 60) {
    try {
      const fullKey = `${this.prefix}ratelimit:${key}`;
      const count = await redis.incr(fullKey);

      // Set expiry on first increment
      if (count === 1) {
        await redis.expire(fullKey, ttl);
      }

      return count;
    } catch (error) {
      logger.error('Increment rate limit error', { error: error.message });
      return 0;
    }
  }

  /**
   * Clear all cache (use with caution)
   */
  async clearAll() {
    try {
      const keys = await redis.keys(`${this.prefix}*`);
      if (keys.length > 0) {
        await redis.del(...keys);
      }
      logger.info('Cache cleared', { count: keys.length });
    } catch (error) {
      logger.error('Cache clear error', { error: error.message });
    }
  }

  /**
   * Get cache statistics
   */
  async getStats() {
    try {
      const info = await redis.info('memory');
      const keys = await redis.dbsize();

      return {
        keys,
        memory: info,
      };
    } catch (error) {
      logger.error('Get stats error', { error: error.message });
      return null;
    }
  }
}

module.exports = new CacheService();
