const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const cacheService = require('../../common/cache.service');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { emitToUser, emitToJob } = require('../../../websocket');
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
      if (userId) {
        emitToUser(userId, 'scan:complete', {
          jobId: job.id,
          type: 'url',
          result,
        });
      }

      emitToJob(job.id, 'scan:complete', {
        jobId: job.id,
        type: 'url',
        result,
      });

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

      if (userId) {
        emitToUser(userId, 'scan:error', {
          jobId: job.id,
          type: 'url',
          error: error.message,
        });
      }

      emitToJob(job.id, 'scan:error', {
        jobId: job.id,
        type: 'url',
        error: error.message,
      });

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
