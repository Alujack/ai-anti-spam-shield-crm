const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const cacheService = require('../../common/cache.service');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { emitToUser, emitToJob } = require('../../../websocket');

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
            message: message,
            messageHash,
            isSpam: result.is_spam,
            confidence: result.confidence,
            prediction: result.prediction,
            scanType: 'text',
            details: JSON.stringify(result.details || {}),
          },
        });
      }

      await job.updateProgress(90);

      // Notify via WebSocket
      if (userId) {
        emitToUser(userId, 'scan:complete', {
          jobId: job.id,
          type: 'text',
          result,
        });
      }

      // Also emit to job-specific room
      emitToJob(job.id, 'scan:complete', {
        jobId: job.id,
        type: 'text',
        result,
      });

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
      if (userId) {
        emitToUser(userId, 'scan:error', {
          jobId: job.id,
          type: 'text',
          error: error.message,
        });
      }

      emitToJob(job.id, 'scan:error', {
        jobId: job.id,
        type: 'text',
        error: error.message,
      });

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
