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
