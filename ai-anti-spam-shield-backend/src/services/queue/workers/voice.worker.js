const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const aiClient = require('../../common/ai.client');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { emitToUser, emitToJob } = require('../../../websocket');

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
            message: result.transcribed_text || '',
            isSpam: result.is_spam,
            confidence: result.confidence,
            prediction: result.prediction,
            scanType: 'voice',
            details: JSON.stringify({
              transcribed_text: result.transcribed_text,
              audio_indicators: result.audio_indicators,
              ...result.details,
            }),
          },
        });
      }

      await job.updateProgress(90);

      // Notify via WebSocket
      if (userId) {
        emitToUser(userId, 'scan:complete', {
          jobId: job.id,
          type: 'voice',
          result,
        });
      }

      emitToJob(job.id, 'scan:complete', {
        jobId: job.id,
        type: 'voice',
        result,
      });

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

      if (userId) {
        emitToUser(userId, 'scan:error', {
          jobId: job.id,
          type: 'voice',
          error: error.message,
        });
      }

      emitToJob(job.id, 'scan:error', {
        jobId: job.id,
        type: 'voice',
        error: error.message,
      });

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
