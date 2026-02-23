const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const emailService = require('../../email.service');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { emitToUser } = require('../../../websocket');

// Worker configuration
const workerConfig = {
  connection: redis,
  concurrency: 2, // Process 2 email scan jobs concurrently (IMAP is IO-heavy)
  limiter: {
    max: 10,
    duration: 1000,
  },
};

// Create the worker
const emailWorker = new Worker(
  QUEUES.EMAIL_SCAN,
  async (job) => {
    const { emailAccountId, userId } = job.data;

    logger.info('Processing email scan job', {
      jobId: job.id,
      emailAccountId,
      userId,
    });

    try {
      await job.updateProgress(10);

      // Perform the email scan
      const result = await emailService.scanEmails(emailAccountId);

      await job.updateProgress(100);

      // Notify via WebSocket
      if (userId) {
        emitToUser(userId, 'email-scan:complete', {
          jobId: job.id,
          emailAccountId,
          result,
        });
      }

      logger.info('Email scan job completed', {
        jobId: job.id,
        emailAccountId,
        scannedCount: result.scannedCount,
        flaggedCount: result.flaggedCount,
      });

      return result;
    } catch (error) {
      logger.error('Email scan job failed', {
        jobId: job.id,
        emailAccountId,
        error: error.message,
      });

      // Notify failure via WebSocket
      if (userId) {
        emitToUser(userId, 'email-scan:error', {
          jobId: job.id,
          emailAccountId,
          error: error.message,
        });
      }

      throw error;
    }
  },
  workerConfig
);

// Worker event handlers
emailWorker.on('completed', (job) => {
  logger.info(`Email worker: Job ${job.id} completed`);
});

emailWorker.on('failed', (job, err) => {
  logger.error(`Email worker: Job ${job?.id} failed`, { error: err.message });
});

emailWorker.on('error', (err) => {
  logger.error('Email worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('Email worker: Shutting down...');
  await emailWorker.close();
  logger.info('Email worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Email worker started');

module.exports = emailWorker;
