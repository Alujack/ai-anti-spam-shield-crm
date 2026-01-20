# Phase 1: Architecture Hardening

> **Duration:** 1 Week
> **Priority:** Critical
> **Dependencies:** None

---

## Overview

Transform the synchronous, single-service architecture into a scalable, containerized system with async processing capabilities.

### Goals

1. Containerize all services with Docker
2. Migrate from SQLite to PostgreSQL
3. Implement async job queue with BullMQ + Redis
4. Add API Gateway (Kong) for rate limiting and routing
5. Enable real-time updates via WebSocket

### Deliverables

- [ ] `docker-compose.yml` orchestrating all services
- [ ] PostgreSQL database with new schema
- [ ] Redis for queue and caching
- [ ] BullMQ workers for async processing
- [ ] Kong API Gateway configuration
- [ ] WebSocket integration for job status updates

---

## 1. Docker Infrastructure

### 1.1 Main Docker Compose File

**Create:** `/docker-compose.yml`

```yaml
version: '3.8'

services:
  # ===========================================
  # API GATEWAY
  # ===========================================
  gateway:
    image: kong:3.4-alpine
    container_name: ai-shield-gateway
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: "0.0.0.0:8001"
    volumes:
      - ./gateway/kong/kong.yml:/etc/kong/kong.yml:ro
    ports:
      - "8080:8000"      # Proxy port (public)
      - "8443:8443"      # Proxy SSL
      - "8001:8001"      # Admin API (internal only)
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - ai-shield-network
    restart: unless-stopped

  # ===========================================
  # NODE.JS BACKEND
  # ===========================================
  backend:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile
    container_name: ai-shield-backend
    environment:
      NODE_ENV: production
      PORT: 3000
      DATABASE_URL: postgresql://aishield:${DB_PASSWORD:-secretpassword}@postgres:5432/aishield
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ml-service:8000
      JWT_SECRET: ${JWT_SECRET:-your-super-secret-jwt-key}
      JWT_REFRESH_SECRET: ${JWT_REFRESH_SECRET:-your-refresh-secret}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:-your-32-byte-encryption-key-here}
    volumes:
      - backend-logs:/app/logs
    ports:
      - "3000:3000"      # Direct access (for debugging)
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      ml-service:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ai-shield-network
    restart: unless-stopped

  # ===========================================
  # QUEUE WORKERS
  # ===========================================
  text-worker:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile
    container_name: ai-shield-text-worker
    command: ["node", "src/services/queue/workers/text.worker.js"]
    environment:
      NODE_ENV: production
      WORKER_TYPE: text
      DATABASE_URL: postgresql://aishield:${DB_PASSWORD:-secretpassword}@postgres:5432/aishield
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ml-service:8000
    depends_on:
      - backend
    networks:
      - ai-shield-network
    restart: unless-stopped
    deploy:
      replicas: 2

  voice-worker:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile
    container_name: ai-shield-voice-worker
    command: ["node", "src/services/queue/workers/voice.worker.js"]
    environment:
      NODE_ENV: production
      WORKER_TYPE: voice
      DATABASE_URL: postgresql://aishield:${DB_PASSWORD:-secretpassword}@postgres:5432/aishield
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ml-service:8000
    depends_on:
      - backend
    networks:
      - ai-shield-network
    restart: unless-stopped

  url-worker:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile
    container_name: ai-shield-url-worker
    command: ["node", "src/services/queue/workers/url.worker.js"]
    environment:
      NODE_ENV: production
      WORKER_TYPE: url
      DATABASE_URL: postgresql://aishield:${DB_PASSWORD:-secretpassword}@postgres:5432/aishield
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ml-service:8000
    depends_on:
      - backend
    networks:
      - ai-shield-network
    restart: unless-stopped

  # ===========================================
  # ML SERVICE (FastAPI)
  # ===========================================
  ml-service:
    build:
      context: ./ai-anti-spam-shield-service-model
      dockerfile: Dockerfile
    container_name: ai-shield-ml-service
    environment:
      MODEL_DIR: /app/model
      PYTHONUNBUFFERED: 1
    volumes:
      - ml-models:/app/model
    ports:
      - "8000:8000"      # Direct access (for debugging)
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - ai-shield-network
    restart: unless-stopped
    # Uncomment for GPU support:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # ===========================================
  # POSTGRESQL DATABASE
  # ===========================================
  postgres:
    image: postgres:15-alpine
    container_name: ai-shield-postgres
    environment:
      POSTGRES_DB: aishield
      POSTGRES_USER: aishield
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secretpassword}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"      # Direct access (for debugging)
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aishield -d aishield"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai-shield-network
    restart: unless-stopped

  # ===========================================
  # REDIS (Queue + Cache)
  # ===========================================
  redis:
    image: redis:7-alpine
    container_name: ai-shield-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"      # Direct access (for debugging)
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai-shield-network
    restart: unless-stopped

  # ===========================================
  # MONITORING (Optional - Phase 8)
  # ===========================================
  prometheus:
    image: prom/prometheus:latest
    container_name: ai-shield-prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - ai-shield-network
    restart: unless-stopped
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: ai-shield-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - ai-shield-network
    restart: unless-stopped
    profiles:
      - monitoring

# ===========================================
# NETWORKS
# ===========================================
networks:
  ai-shield-network:
    driver: bridge

# ===========================================
# VOLUMES
# ===========================================
volumes:
  postgres-data:
  redis-data:
  ml-models:
  backend-logs:
  prometheus-data:
  grafana-data:
```

### 1.2 Development Override

**Create:** `/docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile.dev
    environment:
      NODE_ENV: development
      LOG_LEVEL: debug
    volumes:
      - ./ai-anti-spam-shield-backend/src:/app/src:ro
    command: ["npm", "run", "dev"]

  ml-service:
    volumes:
      - ./ai-anti-spam-shield-service-model/app:/app/app:ro
    command: ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

  # Disable workers in dev (run from backend)
  text-worker:
    profiles:
      - workers
  voice-worker:
    profiles:
      - workers
  url-worker:
    profiles:
      - workers

  # Disable gateway in dev (direct backend access)
  gateway:
    profiles:
      - production
```

### 1.3 Backend Dockerfile

**Create:** `/ai-anti-spam-shield-backend/Dockerfile`

```dockerfile
# ===========================================
# Stage 1: Dependencies
# ===========================================
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies for native modules
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci --only=production

# Generate Prisma client
RUN npx prisma generate

# ===========================================
# Stage 2: Production
# ===========================================
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 aishield

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/prisma ./prisma

# Copy application code
COPY src ./src
COPY package*.json ./

# Set ownership
RUN chown -R aishield:nodejs /app

# Switch to non-root user
USER aishield

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start application
CMD ["node", "src/app.js"]
```

**Create:** `/ai-anti-spam-shield-backend/Dockerfile.dev`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache python3 make g++

COPY package*.json ./
COPY prisma ./prisma/

RUN npm install
RUN npx prisma generate

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

---

## 2. Kong API Gateway

### 2.1 Gateway Configuration

**Create:** `/gateway/kong/kong.yml`

```yaml
_format_version: "3.0"
_transform: true

# ===========================================
# SERVICES
# ===========================================
services:
  # Backend API Service
  - name: backend-api
    url: http://backend:3000
    routes:
      - name: api-v1-route
        paths:
          - /api/v1
        strip_path: false
      - name: api-v2-route
        paths:
          - /api/v2
        strip_path: false
      - name: health-route
        paths:
          - /health
        strip_path: false

  # WebSocket Service (for real-time updates)
  - name: websocket-service
    url: http://backend:3000
    routes:
      - name: websocket-route
        paths:
          - /ws
        strip_path: false
        protocols:
          - http
          - https
          - ws
          - wss

# ===========================================
# PLUGINS (Global)
# ===========================================
plugins:
  # Rate Limiting
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
      policy: local
      fault_tolerant: true
      hide_client_headers: false

  # Request Size Limiting (10MB for voice files)
  - name: request-size-limiting
    config:
      allowed_payload_size: 10
      size_unit: megabytes

  # CORS
  - name: cors
    config:
      origins:
        - "*"
      methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Authorization
        - Content-Type
        - X-Request-ID
      exposed_headers:
        - X-Request-ID
        - X-RateLimit-Remaining
      credentials: true
      max_age: 3600

  # Request/Response Logging
  - name: file-log
    config:
      path: /dev/stdout
      reopen: true

  # Request ID (for tracing)
  - name: correlation-id
    config:
      header_name: X-Request-ID
      generator: uuid
      echo_downstream: true

# ===========================================
# CONSUMERS (for authenticated endpoints)
# ===========================================
consumers:
  - username: mobile-app
    custom_id: mobile-app-client

# ===========================================
# ROUTE-SPECIFIC PLUGINS
# ===========================================

# Higher rate limit for scan endpoints
upstreams:
  - name: backend-upstream
    targets:
      - target: backend:3000
        weight: 100
    healthchecks:
      active:
        healthy:
          interval: 10
          successes: 2
        unhealthy:
          interval: 10
          http_failures: 3
      passive:
        healthy:
          successes: 2
        unhealthy:
          http_failures: 3
```

### 2.2 Gateway Dockerfile

**Create:** `/gateway/kong/Dockerfile`

```dockerfile
FROM kong:3.4-alpine

# Copy declarative config
COPY kong.yml /etc/kong/kong.yml

# Validate config on build
RUN kong config parse /etc/kong/kong.yml

USER kong
```

---

## 3. Redis Configuration

### 3.1 Redis Connection Module

**Create:** `/ai-anti-spam-shield-backend/src/config/redis.js`

```javascript
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
```

---

## 4. BullMQ Queue System

### 4.1 Queue Configuration

**Create:** `/ai-anti-spam-shield-backend/src/config/queue.js`

```javascript
const { Queue, QueueEvents } = require('bullmq');
const { redis } = require('./redis');
const logger = require('../utils/logger');

// Queue names
const QUEUES = {
  TEXT_SCAN: 'text-scan',
  VOICE_SCAN: 'voice-scan',
  URL_SCAN: 'url-scan',
  FEEDBACK: 'feedback-processing',
  RETRAINING: 'model-retraining',
};

// Default job options
const defaultJobOptions = {
  attempts: 3,
  backoff: {
    type: 'exponential',
    delay: 1000,
  },
  removeOnComplete: {
    count: 1000,      // Keep last 1000 completed jobs
    age: 24 * 3600,   // Remove jobs older than 24 hours
  },
  removeOnFail: {
    count: 5000,      // Keep last 5000 failed jobs for debugging
    age: 7 * 24 * 3600, // Remove failed jobs older than 7 days
  },
};

// Queue-specific configurations
const queueConfigs = {
  [QUEUES.TEXT_SCAN]: {
    ...defaultJobOptions,
    priority: 1,
  },
  [QUEUES.VOICE_SCAN]: {
    ...defaultJobOptions,
    priority: 2,
    attempts: 2,      // Voice processing is expensive, fewer retries
  },
  [QUEUES.URL_SCAN]: {
    ...defaultJobOptions,
    priority: 1,
  },
  [QUEUES.FEEDBACK]: {
    ...defaultJobOptions,
    priority: 3,      // Lower priority than scans
  },
  [QUEUES.RETRAINING]: {
    ...defaultJobOptions,
    priority: 4,      // Lowest priority
    attempts: 1,      // Don't retry retraining automatically
  },
};

// Create queue instances
const queues = {};
const queueEvents = {};

const createQueue = (name) => {
  if (queues[name]) return queues[name];

  const queue = new Queue(name, {
    connection: redis,
    defaultJobOptions: queueConfigs[name] || defaultJobOptions,
  });

  const events = new QueueEvents(name, { connection: redis });

  // Event logging
  events.on('completed', ({ jobId }) => {
    logger.info(`Queue ${name}: Job ${jobId} completed`);
  });

  events.on('failed', ({ jobId, failedReason }) => {
    logger.error(`Queue ${name}: Job ${jobId} failed`, { reason: failedReason });
  });

  events.on('stalled', ({ jobId }) => {
    logger.warn(`Queue ${name}: Job ${jobId} stalled`);
  });

  queues[name] = queue;
  queueEvents[name] = events;

  return queue;
};

// Initialize all queues
const initQueues = async () => {
  try {
    for (const name of Object.values(QUEUES)) {
      createQueue(name);
      logger.info(`Queue initialized: ${name}`);
    }
    return true;
  } catch (error) {
    logger.error('Failed to initialize queues', { error: error.message });
    return false;
  }
};

// Get queue by name
const getQueue = (name) => {
  if (!queues[name]) {
    return createQueue(name);
  }
  return queues[name];
};

// Close all queues
const closeQueues = async () => {
  try {
    for (const [name, queue] of Object.entries(queues)) {
      await queue.close();
      if (queueEvents[name]) {
        await queueEvents[name].close();
      }
      logger.info(`Queue closed: ${name}`);
    }
  } catch (error) {
    logger.error('Error closing queues', { error: error.message });
  }
};

module.exports = {
  QUEUES,
  createQueue,
  initQueues,
  getQueue,
  closeQueues,
  defaultJobOptions,
};
```

### 4.2 Queue Manager

**Create:** `/ai-anti-spam-shield-backend/src/services/queue/queue.manager.js`

```javascript
const { getQueue, QUEUES } = require('../../config/queue');
const logger = require('../../utils/logger');
const crypto = require('crypto');

class QueueManager {
  /**
   * Add a text scan job to the queue
   * @param {Object} data - Job data
   * @param {string} data.message - Text message to scan
   * @param {string} data.userId - Optional user ID
   * @param {Object} options - Job options
   * @returns {Promise<Object>} Job info
   */
  async addTextScanJob(data, options = {}) {
    const queue = getQueue(QUEUES.TEXT_SCAN);

    const jobData = {
      message: data.message,
      userId: data.userId || null,
      messageHash: this.hashMessage(data.message),
      timestamp: Date.now(),
      ...data,
    };

    const job = await queue.add('scan-text', jobData, {
      priority: options.priority || 1,
      ...options,
    });

    logger.info('Text scan job added', {
      jobId: job.id,
      userId: data.userId,
      messageLength: data.message.length,
    });

    return {
      jobId: job.id,
      queue: QUEUES.TEXT_SCAN,
      status: 'queued',
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Add a voice scan job to the queue
   * @param {Object} data - Job data
   * @param {Buffer} data.audioBuffer - Audio file buffer
   * @param {string} data.filename - Original filename
   * @param {string} data.mimeType - Audio MIME type
   * @param {string} data.userId - Optional user ID
   * @returns {Promise<Object>} Job info
   */
  async addVoiceScanJob(data, options = {}) {
    const queue = getQueue(QUEUES.VOICE_SCAN);

    const jobData = {
      audioBase64: data.audioBuffer.toString('base64'),
      filename: data.filename,
      mimeType: data.mimeType,
      userId: data.userId || null,
      timestamp: Date.now(),
    };

    const job = await queue.add('scan-voice', jobData, {
      priority: options.priority || 2,
      ...options,
    });

    logger.info('Voice scan job added', {
      jobId: job.id,
      userId: data.userId,
      filename: data.filename,
    });

    return {
      jobId: job.id,
      queue: QUEUES.VOICE_SCAN,
      status: 'queued',
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Add a URL scan job to the queue
   * @param {Object} data - Job data
   * @param {string} data.url - URL to scan
   * @param {string} data.text - Optional text context
   * @param {boolean} data.deep - Whether to perform deep analysis
   * @param {string} data.userId - Optional user ID
   * @returns {Promise<Object>} Job info
   */
  async addUrlScanJob(data, options = {}) {
    const queue = getQueue(QUEUES.URL_SCAN);

    const jobData = {
      url: data.url,
      text: data.text || null,
      deep: data.deep || false,
      userId: data.userId || null,
      timestamp: Date.now(),
    };

    const job = await queue.add('scan-url', jobData, {
      priority: options.priority || 1,
      ...options,
    });

    logger.info('URL scan job added', {
      jobId: job.id,
      userId: data.userId,
      url: data.url,
    });

    return {
      jobId: job.id,
      queue: QUEUES.URL_SCAN,
      status: 'queued',
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Get job status
   * @param {string} queueName - Queue name
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Job status
   */
  async getJobStatus(queueName, jobId) {
    const queue = getQueue(queueName);
    const job = await queue.getJob(jobId);

    if (!job) {
      return { status: 'not_found', jobId };
    }

    const state = await job.getState();

    return {
      jobId: job.id,
      queue: queueName,
      status: state,
      progress: job.progress,
      data: state === 'completed' ? job.returnvalue : null,
      error: state === 'failed' ? job.failedReason : null,
      attempts: job.attemptsMade,
      createdAt: new Date(job.timestamp).toISOString(),
      processedAt: job.processedOn ? new Date(job.processedOn).toISOString() : null,
      finishedAt: job.finishedOn ? new Date(job.finishedOn).toISOString() : null,
    };
  }

  /**
   * Cancel a pending job
   * @param {string} queueName - Queue name
   * @param {string} jobId - Job ID
   * @returns {Promise<boolean>} Success status
   */
  async cancelJob(queueName, jobId) {
    const queue = getQueue(queueName);
    const job = await queue.getJob(jobId);

    if (!job) {
      return false;
    }

    const state = await job.getState();

    if (state === 'waiting' || state === 'delayed') {
      await job.remove();
      logger.info('Job cancelled', { jobId, queue: queueName });
      return true;
    }

    logger.warn('Cannot cancel job in current state', { jobId, state });
    return false;
  }

  /**
   * Get queue statistics
   * @param {string} queueName - Queue name
   * @returns {Promise<Object>} Queue stats
   */
  async getQueueStats(queueName) {
    const queue = getQueue(queueName);

    const [waiting, active, completed, failed, delayed] = await Promise.all([
      queue.getWaitingCount(),
      queue.getActiveCount(),
      queue.getCompletedCount(),
      queue.getFailedCount(),
      queue.getDelayedCount(),
    ]);

    return {
      queue: queueName,
      waiting,
      active,
      completed,
      failed,
      delayed,
      total: waiting + active + delayed,
    };
  }

  /**
   * Get all queue statistics
   * @returns {Promise<Object>} All queue stats
   */
  async getAllQueueStats() {
    const stats = {};

    for (const queueName of Object.values(QUEUES)) {
      stats[queueName] = await this.getQueueStats(queueName);
    }

    return stats;
  }

  /**
   * Hash message for caching/deduplication
   * @param {string} message - Message to hash
   * @returns {string} Hash
   */
  hashMessage(message) {
    return crypto
      .createHash('sha256')
      .update(message.toLowerCase().trim())
      .digest('hex');
  }
}

module.exports = new QueueManager();
```

### 4.3 Text Worker

**Create:** `/ai-anti-spam-shield-backend/src/services/queue/workers/text.worker.js`

```javascript
const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const cacheService = require('../../common/cache.service');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { io } = require('../../../websocket');

// Worker configuration
const workerConfig = {
  connection: redis,
  concurrency: 5,           // Process 5 jobs concurrently
  limiter: {
    max: 100,               // Max 100 jobs
    duration: 1000,         // Per second
  },
};

// Create the worker
const textWorker = new Worker(
  QUEUES.TEXT_SCAN,
  async (job) => {
    const { message, userId, messageHash } = job.data;

    logger.info('Processing text scan job', {
      jobId: job.id,
      userId,
      messageLength: message.length,
    });

    try {
      // Update progress
      await job.updateProgress(10);

      // Check cache first
      const cached = await cacheService.getCachedPrediction(messageHash);
      if (cached) {
        logger.info('Cache hit for text scan', { jobId: job.id });
        await job.updateProgress(100);
        return { ...cached, fromCache: true };
      }

      await job.updateProgress(30);

      // Call AI service
      const result = await aiClient.predictText(message);

      await job.updateProgress(70);

      // Cache the result
      await cacheService.cachePrediction(messageHash, result);

      // Save to database if user is authenticated
      if (userId) {
        await prisma.scanHistory.create({
          data: {
            userId,
            messageEncrypted: message, // TODO: Encrypt in Phase 8
            messageHash,
            isSpam: result.is_spam,
            confidence: result.confidence,
            prediction: result.prediction,
            scanType: 'text',
            details: JSON.stringify(result.details || {}),
            modelVersion: result.model_version || 'v1',
          },
        });
      }

      await job.updateProgress(90);

      // Notify via WebSocket
      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:complete', {
          jobId: job.id,
          type: 'text',
          result,
        });
      }

      await job.updateProgress(100);

      logger.info('Text scan job completed', {
        jobId: job.id,
        isSpam: result.is_spam,
      });

      return result;

    } catch (error) {
      logger.error('Text scan job failed', {
        jobId: job.id,
        error: error.message,
      });

      // Notify failure via WebSocket
      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:error', {
          jobId: job.id,
          type: 'text',
          error: error.message,
        });
      }

      throw error;
    }
  },
  workerConfig
);

// Worker event handlers
textWorker.on('completed', (job) => {
  logger.info(`Text worker: Job ${job.id} completed`);
});

textWorker.on('failed', (job, err) => {
  logger.error(`Text worker: Job ${job?.id} failed`, { error: err.message });
});

textWorker.on('error', (err) => {
  logger.error('Text worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('Text worker: Shutting down...');
  await textWorker.close();
  logger.info('Text worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Text worker started');

module.exports = textWorker;
```

### 4.4 Voice Worker

**Create:** `/ai-anti-spam-shield-backend/src/services/queue/workers/voice.worker.js`

```javascript
const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { io } = require('../../../websocket');

// Worker configuration
const workerConfig = {
  connection: redis,
  concurrency: 2,           // Voice processing is heavy, fewer concurrent jobs
  limiter: {
    max: 20,                // Max 20 jobs
    duration: 1000,         // Per second
  },
};

// Create the worker
const voiceWorker = new Worker(
  QUEUES.VOICE_SCAN,
  async (job) => {
    const { audioBase64, filename, mimeType, userId } = job.data;

    logger.info('Processing voice scan job', {
      jobId: job.id,
      userId,
      filename,
    });

    try {
      await job.updateProgress(10);

      // Convert base64 back to buffer
      const audioBuffer = Buffer.from(audioBase64, 'base64');

      await job.updateProgress(20);

      // Call AI service
      const result = await aiClient.predictVoice(audioBuffer, filename, mimeType);

      await job.updateProgress(80);

      // Save to database if user is authenticated
      if (userId) {
        await prisma.scanHistory.create({
          data: {
            userId,
            messageEncrypted: result.transcribed_text || '',
            messageHash: '', // Voice doesn't use hash caching
            isSpam: result.is_spam,
            confidence: result.confidence,
            prediction: result.prediction,
            scanType: 'voice',
            details: JSON.stringify({
              transcribed_text: result.transcribed_text,
              audio_indicators: result.audio_indicators,
              ...result.details,
            }),
            modelVersion: result.model_version || 'v1',
          },
        });
      }

      await job.updateProgress(90);

      // Notify via WebSocket
      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:complete', {
          jobId: job.id,
          type: 'voice',
          result,
        });
      }

      await job.updateProgress(100);

      logger.info('Voice scan job completed', {
        jobId: job.id,
        isSpam: result.is_spam,
      });

      return result;

    } catch (error) {
      logger.error('Voice scan job failed', {
        jobId: job.id,
        error: error.message,
      });

      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:error', {
          jobId: job.id,
          type: 'voice',
          error: error.message,
        });
      }

      throw error;
    }
  },
  workerConfig
);

// Worker event handlers
voiceWorker.on('completed', (job) => {
  logger.info(`Voice worker: Job ${job.id} completed`);
});

voiceWorker.on('failed', (job, err) => {
  logger.error(`Voice worker: Job ${job?.id} failed`, { error: err.message });
});

voiceWorker.on('error', (err) => {
  logger.error('Voice worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('Voice worker: Shutting down...');
  await voiceWorker.close();
  logger.info('Voice worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Voice worker started');

module.exports = voiceWorker;
```

### 4.5 URL Worker

**Create:** `/ai-anti-spam-shield-backend/src/services/queue/workers/url.worker.js`

```javascript
const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const cacheService = require('../../common/cache.service');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { io } = require('../../../websocket');
const crypto = require('crypto');

// Worker configuration
const workerConfig = {
  connection: redis,
  concurrency: 5,
  limiter: {
    max: 50,
    duration: 1000,
  },
};

// Create the worker
const urlWorker = new Worker(
  QUEUES.URL_SCAN,
  async (job) => {
    const { url, text, deep, userId } = job.data;

    logger.info('Processing URL scan job', {
      jobId: job.id,
      userId,
      url,
      deep,
    });

    try {
      await job.updateProgress(10);

      // Create cache key
      const cacheKey = crypto
        .createHash('sha256')
        .update(`${url}:${deep}`)
        .digest('hex');

      // Check cache
      const cached = await cacheService.getCachedPrediction(cacheKey);
      if (cached) {
        logger.info('Cache hit for URL scan', { jobId: job.id });
        await job.updateProgress(100);
        return { ...cached, fromCache: true };
      }

      await job.updateProgress(30);

      // Call AI service
      let result;
      if (deep) {
        result = await aiClient.analyzeUrlDeep(url);
      } else {
        result = await aiClient.scanUrl(url);
      }

      // If text was provided, also analyze for phishing
      if (text) {
        const textResult = await aiClient.predictPhishing(text);
        result = {
          ...result,
          text_analysis: textResult,
          combined_confidence: (result.confidence + textResult.confidence) / 2,
        };
      }

      await job.updateProgress(70);

      // Cache the result (shorter TTL for URLs - 1 hour)
      await cacheService.cachePrediction(cacheKey, result, 3600);

      // Save to database if user is authenticated
      if (userId) {
        await prisma.phishingScanHistory.create({
          data: {
            userId,
            inputText: text || '',
            inputUrl: url,
            isPhishing: result.is_phishing,
            confidence: result.confidence,
            phishingType: result.phishing_type || 'URL',
            threatLevel: result.threat_level || 'NONE',
            indicators: JSON.stringify(result.indicators || []),
            urlsAnalyzed: JSON.stringify([url]),
            brandDetected: result.brand_impersonation || null,
          },
        });
      }

      await job.updateProgress(90);

      // Notify via WebSocket
      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:complete', {
          jobId: job.id,
          type: 'url',
          result,
        });
      }

      await job.updateProgress(100);

      logger.info('URL scan job completed', {
        jobId: job.id,
        isPhishing: result.is_phishing,
      });

      return result;

    } catch (error) {
      logger.error('URL scan job failed', {
        jobId: job.id,
        error: error.message,
      });

      if (userId && io) {
        io.to(`user:${userId}`).emit('scan:error', {
          jobId: job.id,
          type: 'url',
          error: error.message,
        });
      }

      throw error;
    }
  },
  workerConfig
);

// Worker event handlers
urlWorker.on('completed', (job) => {
  logger.info(`URL worker: Job ${job.id} completed`);
});

urlWorker.on('failed', (job, err) => {
  logger.error(`URL worker: Job ${job?.id} failed`, { error: err.message });
});

urlWorker.on('error', (err) => {
  logger.error('URL worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('URL worker: Shutting down...');
  await urlWorker.close();
  logger.info('URL worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('URL worker started');

module.exports = urlWorker;
```

---

## 5. Common Services

### 5.1 AI Client

**Create:** `/ai-anti-spam-shield-backend/src/services/common/ai.client.js`

```javascript
const axios = require('axios');
const FormData = require('form-data');
const logger = require('../../utils/logger');
const config = require('../../config');

class AIClient {
  constructor() {
    this.baseUrl = config.ai.serviceUrl || 'http://localhost:8000';
    this.apiKey = config.ai.apiKey;

    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'X-API-Key': this.apiKey }),
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => this.handleError(error)
    );
  }

  handleError(error) {
    if (error.code === 'ECONNREFUSED') {
      logger.error('AI service unavailable', { url: this.baseUrl });
      throw new Error('AI service unavailable');
    }

    if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      logger.error('AI service timeout');
      throw new Error('AI service timeout');
    }

    if (error.response) {
      const { status, data } = error.response;
      logger.error('AI service error', { status, data });
      throw new Error(data?.detail || `AI service error: ${status}`);
    }

    throw error;
  }

  /**
   * Predict spam for text message
   */
  async predictText(message, version = 'v1') {
    const endpoint = version === 'v2' ? '/predict-v2' : '/predict';

    logger.debug('Calling AI service for text prediction', {
      endpoint,
      messageLength: message.length,
    });

    const response = await this.client.post(endpoint, { message });
    return response.data;
  }

  /**
   * Predict spam for voice message
   */
  async predictVoice(audioBuffer, filename, mimeType, version = 'v1') {
    const endpoint = version === 'v2' ? '/predict-voice-v2' : '/predict-voice';

    const formData = new FormData();
    formData.append('audio', audioBuffer, {
      filename,
      contentType: mimeType,
    });

    logger.debug('Calling AI service for voice prediction', {
      endpoint,
      filename,
    });

    const response = await this.client.post(endpoint, formData, {
      headers: formData.getHeaders(),
      timeout: 60000, // Voice processing takes longer
    });

    return response.data;
  }

  /**
   * Predict phishing for text
   */
  async predictPhishing(text) {
    logger.debug('Calling AI service for phishing prediction', {
      textLength: text.length,
    });

    const response = await this.client.post('/predict-phishing', {
      text,
      scan_type: 'text',
    });

    return response.data;
  }

  /**
   * Scan URL for phishing
   */
  async scanUrl(url) {
    logger.debug('Calling AI service for URL scan', { url });

    const response = await this.client.post('/scan-url', { url });
    return response.data;
  }

  /**
   * Deep URL analysis (Phase 3)
   */
  async analyzeUrlDeep(url) {
    logger.debug('Calling AI service for deep URL analysis', { url });

    const response = await this.client.post('/analyze-url-deep', {
      url,
      include_screenshot: false,
    });

    return response.data;
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
}

module.exports = new AIClient();
```

### 5.2 Cache Service

**Create:** `/ai-anti-spam-shield-backend/src/services/common/cache.service.js`

```javascript
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
```

---

## 6. Database Migration

### 6.1 Updated Prisma Schema

**Modify:** `/ai-anti-spam-shield-backend/prisma/schema.prisma`

```prisma
// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ===========================================
// USER MODEL
// ===========================================
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  password  String
  name      String?
  phone     String?
  role      String   @default("USER")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // Relations
  scanHistories         ScanHistory[]
  reports               Report[]
  phishingScanHistories PhishingScanHistory[]
  scanJobs              ScanJob[]
  feedback              UserFeedback[]

  @@index([email])
  @@index([role])
}

// ===========================================
// SCAN HISTORY (Enhanced)
// ===========================================
model ScanHistory {
  id               String   @id @default(uuid())
  userId           String
  messageEncrypted String   // Will be encrypted in Phase 8
  messageHash      String   // For deduplication
  isSpam           Boolean
  confidence       Float
  prediction       String
  scanType         String   // text, voice
  details          String?  // JSON string
  modelVersion     String?  // Track which model version was used
  scannedAt        DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@index([scannedAt])
  @@index([messageHash])
  @@index([modelVersion])
}

// ===========================================
// PHISHING SCAN HISTORY
// ===========================================
model PhishingScanHistory {
  id            String   @id @default(uuid())
  userId        String
  inputText     String
  inputUrl      String?
  isPhishing    Boolean
  confidence    Float
  phishingType  String   // EMAIL, SMS, URL, NONE
  threatLevel   String   // CRITICAL, HIGH, MEDIUM, LOW, NONE
  indicators    String   // JSON array of indicators
  urlsAnalyzed  String?  // JSON array of URLs
  brandDetected String?  // Detected brand impersonation
  modelVersion  String?
  scannedAt     DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@index([scannedAt])
  @@index([phishingType])
  @@index([threatLevel])
}

// ===========================================
// REPORT MODEL
// ===========================================
model Report {
  id          String   @id @default(uuid())
  userId      String
  messageText String
  reportType  String   // SPAM, PHISHING, SCAM, SUSPICIOUS, OTHER
  description String?
  url         String?
  phoneNumber String?
  senderInfo  String?
  status      String   @default("PENDING") // PENDING, REVIEWING, RESOLVED, DISMISSED
  resolvedBy  String?
  resolvedAt  DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@index([status])
  @@index([reportType])
  @@index([createdAt])
}

// ===========================================
// SCAN JOB (NEW - Async Processing)
// ===========================================
model ScanJob {
  id          String    @id @default(uuid())
  userId      String?
  type        String    // text, voice, url
  status      String    @default("pending") // pending, processing, completed, failed
  priority    Int       @default(0)
  input       String    // Encrypted input data
  inputHash   String    // For cache lookup
  result      Json?     // Scan result
  error       String?   // Error message if failed
  attempts    Int       @default(0)
  createdAt   DateTime  @default(now())
  startedAt   DateTime?
  completedAt DateTime?

  user User? @relation(fields: [userId], references: [id], onDelete: SetNull)

  @@index([status])
  @@index([userId])
  @@index([inputHash])
  @@index([type])
  @@index([createdAt])
}

// ===========================================
// USER FEEDBACK (NEW - Phase 5)
// ===========================================
model UserFeedback {
  id                 String    @id @default(uuid())
  userId             String
  scanHistoryId      String?
  phishingHistoryId  String?
  originalPrediction String
  actualLabel        String    // spam, ham, phishing, safe
  feedbackType       String    // false_positive, false_negative, confirmed
  userComment        String?
  status             String    @default("pending") // pending, approved, rejected
  reviewedBy         String?
  reviewedAt         DateTime?
  createdAt          DateTime  @default(now())

  // Retraining pipeline
  includedInTraining Boolean  @default(false)
  trainingBatch      String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([status])
  @@index([includedInTraining])
  @@index([feedbackType])
  @@index([userId])
  @@index([createdAt])
}

// ===========================================
// MODEL VERSION (NEW - Phase 5)
// ===========================================
model ModelVersion {
  id            String    @id @default(uuid())
  modelType     String    // sms, voice, phishing
  version       String    // e.g., "v2.1.0"
  modelPath     String    // Path to model file
  metrics       Json      // {accuracy, recall, precision, f1}
  trainedAt     DateTime
  deployedAt    DateTime?
  status        String    // training, testing, deployed, rolled_back
  feedbackBatch String?   // Reference to feedback batch used for training
  changelog     String?
  createdBy     String?

  @@unique([modelType, version])
  @@index([modelType, status])
  @@index([deployedAt])
}
```

### 6.2 Migration Script

**Create:** `/ai-anti-spam-shield-backend/prisma/migrations/001_init_postgres/migration.sql`

```sql
-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "name" TEXT,
    "phone" TEXT,
    "role" TEXT NOT NULL DEFAULT 'USER',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ScanHistory" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "messageEncrypted" TEXT NOT NULL,
    "messageHash" TEXT NOT NULL,
    "isSpam" BOOLEAN NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "prediction" TEXT NOT NULL,
    "scanType" TEXT NOT NULL,
    "details" TEXT,
    "modelVersion" TEXT,
    "scannedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ScanHistory_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PhishingScanHistory" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "inputText" TEXT NOT NULL,
    "inputUrl" TEXT,
    "isPhishing" BOOLEAN NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "phishingType" TEXT NOT NULL,
    "threatLevel" TEXT NOT NULL,
    "indicators" TEXT NOT NULL,
    "urlsAnalyzed" TEXT,
    "brandDetected" TEXT,
    "modelVersion" TEXT,
    "scannedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PhishingScanHistory_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Report" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "messageText" TEXT NOT NULL,
    "reportType" TEXT NOT NULL,
    "description" TEXT,
    "url" TEXT,
    "phoneNumber" TEXT,
    "senderInfo" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "resolvedBy" TEXT,
    "resolvedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Report_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ScanJob" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "type" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "priority" INTEGER NOT NULL DEFAULT 0,
    "input" TEXT NOT NULL,
    "inputHash" TEXT NOT NULL,
    "result" JSONB,
    "error" TEXT,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),

    CONSTRAINT "ScanJob_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserFeedback" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "scanHistoryId" TEXT,
    "phishingHistoryId" TEXT,
    "originalPrediction" TEXT NOT NULL,
    "actualLabel" TEXT NOT NULL,
    "feedbackType" TEXT NOT NULL,
    "userComment" TEXT,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "reviewedBy" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "includedInTraining" BOOLEAN NOT NULL DEFAULT false,
    "trainingBatch" TEXT,

    CONSTRAINT "UserFeedback_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ModelVersion" (
    "id" TEXT NOT NULL,
    "modelType" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "modelPath" TEXT NOT NULL,
    "metrics" JSONB NOT NULL,
    "trainedAt" TIMESTAMP(3) NOT NULL,
    "deployedAt" TIMESTAMP(3),
    "status" TEXT NOT NULL,
    "feedbackBatch" TEXT,
    "changelog" TEXT,
    "createdBy" TEXT,

    CONSTRAINT "ModelVersion_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");
CREATE INDEX "User_email_idx" ON "User"("email");
CREATE INDEX "User_role_idx" ON "User"("role");

CREATE INDEX "ScanHistory_userId_idx" ON "ScanHistory"("userId");
CREATE INDEX "ScanHistory_scannedAt_idx" ON "ScanHistory"("scannedAt");
CREATE INDEX "ScanHistory_messageHash_idx" ON "ScanHistory"("messageHash");
CREATE INDEX "ScanHistory_modelVersion_idx" ON "ScanHistory"("modelVersion");

CREATE INDEX "PhishingScanHistory_userId_idx" ON "PhishingScanHistory"("userId");
CREATE INDEX "PhishingScanHistory_scannedAt_idx" ON "PhishingScanHistory"("scannedAt");
CREATE INDEX "PhishingScanHistory_phishingType_idx" ON "PhishingScanHistory"("phishingType");
CREATE INDEX "PhishingScanHistory_threatLevel_idx" ON "PhishingScanHistory"("threatLevel");

CREATE INDEX "Report_userId_idx" ON "Report"("userId");
CREATE INDEX "Report_status_idx" ON "Report"("status");
CREATE INDEX "Report_reportType_idx" ON "Report"("reportType");
CREATE INDEX "Report_createdAt_idx" ON "Report"("createdAt");

CREATE INDEX "ScanJob_status_idx" ON "ScanJob"("status");
CREATE INDEX "ScanJob_userId_idx" ON "ScanJob"("userId");
CREATE INDEX "ScanJob_inputHash_idx" ON "ScanJob"("inputHash");
CREATE INDEX "ScanJob_type_idx" ON "ScanJob"("type");
CREATE INDEX "ScanJob_createdAt_idx" ON "ScanJob"("createdAt");

CREATE INDEX "UserFeedback_status_idx" ON "UserFeedback"("status");
CREATE INDEX "UserFeedback_includedInTraining_idx" ON "UserFeedback"("includedInTraining");
CREATE INDEX "UserFeedback_feedbackType_idx" ON "UserFeedback"("feedbackType");
CREATE INDEX "UserFeedback_userId_idx" ON "UserFeedback"("userId");
CREATE INDEX "UserFeedback_createdAt_idx" ON "UserFeedback"("createdAt");

CREATE UNIQUE INDEX "ModelVersion_modelType_version_key" ON "ModelVersion"("modelType", "version");
CREATE INDEX "ModelVersion_modelType_status_idx" ON "ModelVersion"("modelType", "status");
CREATE INDEX "ModelVersion_deployedAt_idx" ON "ModelVersion"("deployedAt");

-- AddForeignKey
ALTER TABLE "ScanHistory" ADD CONSTRAINT "ScanHistory_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "PhishingScanHistory" ADD CONSTRAINT "PhishingScanHistory_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Report" ADD CONSTRAINT "Report_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "ScanJob" ADD CONSTRAINT "ScanJob_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "UserFeedback" ADD CONSTRAINT "UserFeedback_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
```

---

## 7. Verification Checklist

### 7.1 Infrastructure

- [ ] `docker-compose up` starts all services without errors
- [ ] PostgreSQL is accessible on port 5432
- [ ] Redis is accessible on port 6379
- [ ] Backend health check passes (`curl http://localhost:3000/health`)
- [ ] ML service health check passes (`curl http://localhost:8000/health`)
- [ ] Kong gateway routes requests correctly (`curl http://localhost:8080/health`)

### 7.2 Async Processing

- [ ] Text scan returns job ID within 100ms
- [ ] Voice scan returns job ID within 100ms
- [ ] URL scan returns job ID within 100ms
- [ ] Job status endpoint returns correct state
- [ ] WebSocket receives completion notification
- [ ] Failed jobs are retried automatically

### 7.3 Database

- [ ] Prisma migrations run successfully
- [ ] User registration works
- [ ] Scan history is saved correctly
- [ ] Indexes improve query performance

### 7.4 Caching

- [ ] Repeated scans hit cache
- [ ] Cache TTL is respected
- [ ] Cache invalidation works

---

## 8. Troubleshooting

### Common Issues

**PostgreSQL connection refused:**
```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U aishield -d aishield
```

**Redis connection failed:**
```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Check memory
docker-compose exec redis redis-cli info memory
```

**Worker not processing jobs:**
```bash
# Check worker logs
docker-compose logs text-worker

# Check queue depth
docker-compose exec redis redis-cli LLEN bull:text-scan:wait
```

**Kong routing issues:**
```bash
# Check Kong config
docker-compose exec gateway kong config parse /etc/kong/kong.yml

# Check routes
curl http://localhost:8001/routes
```

---

## Next Steps

After completing Phase 1:
1. Verify all services are running
2. Run integration tests
3. Proceed to [Phase 2: Model Upgrade](./phase2-model-upgrade.md)
