const { Worker } = require('bullmq');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const { emitToUser } = require('../../../websocket');

// Worker configuration
const workerConfig = {
  connection: redis,
  concurrency: 3,           // Process 3 jobs concurrently
  limiter: {
    max: 50,                // Max 50 jobs
    duration: 1000,         // Per second
  },
};

// Create the feedback worker
const feedbackWorker = new Worker(
  QUEUES.FEEDBACK,
  async (job) => {
    const { feedbackId } = job.data;

    logger.info('Processing feedback job', {
      jobId: job.id,
      feedbackId,
    });

    try {
      await job.updateProgress(10);

      // Get feedback details
      const feedback = await prisma.userFeedback.findUnique({
        where: { id: feedbackId },
        include: {
          user: {
            select: { id: true, email: true },
          },
        },
      });

      if (!feedback) {
        logger.warn('Feedback not found', { feedbackId });
        return { status: 'not_found' };
      }

      await job.updateProgress(30);

      // Validate feedback data
      const validationResult = await validateFeedback(feedback);
      if (!validationResult.valid) {
        logger.warn('Feedback validation failed', {
          feedbackId,
          reason: validationResult.reason,
        });

        // Mark as rejected if invalid
        await prisma.userFeedback.update({
          where: { id: feedbackId },
          data: {
            status: 'rejected',
            reviewedAt: new Date(),
          },
        });

        return { status: 'invalid', reason: validationResult.reason };
      }

      await job.updateProgress(60);

      // Check for potential abuse (multiple conflicting feedback from same user)
      const abuseCheck = await checkForAbuse(feedback.userId);
      if (abuseCheck.flagged) {
        logger.warn('Potential feedback abuse detected', {
          userId: feedback.userId,
          reason: abuseCheck.reason,
        });
      }

      await job.updateProgress(80);

      // Calculate feedback quality score
      const qualityScore = await calculateQualityScore(feedback);

      // Update feedback with quality metadata
      await prisma.userFeedback.update({
        where: { id: feedbackId },
        data: {
          // Store quality info in a JSON field if needed (or add to notes)
        },
      });

      await job.updateProgress(100);

      // Notify admin of new feedback for review
      emitToUser('admin', 'feedback:new', {
        feedbackId: feedback.id,
        feedbackType: feedback.feedbackType,
        userId: feedback.userId,
        qualityScore,
      });

      logger.info('Feedback processing completed', {
        jobId: job.id,
        feedbackId,
        qualityScore,
      });

      return {
        status: 'processed',
        qualityScore,
        abuseFlag: abuseCheck.flagged,
      };

    } catch (error) {
      logger.error('Feedback processing failed', {
        jobId: job.id,
        feedbackId,
        error: error.message,
      });
      throw error;
    }
  },
  workerConfig
);

/**
 * Validate feedback data
 */
async function validateFeedback(feedback) {
  // Check if scan still exists
  if (feedback.scanHistoryId) {
    const scan = await prisma.scanHistory.findUnique({
      where: { id: feedback.scanHistoryId },
    });
    if (!scan) {
      return { valid: false, reason: 'Associated scan not found' };
    }
  } else if (feedback.phishingHistoryId) {
    const scan = await prisma.phishingScanHistory.findUnique({
      where: { id: feedback.phishingHistoryId },
    });
    if (!scan) {
      return { valid: false, reason: 'Associated scan not found' };
    }
  } else {
    return { valid: false, reason: 'No associated scan' };
  }

  // Validate feedback type consistency
  const validTypes = ['false_positive', 'false_negative', 'confirmed'];
  if (!validTypes.includes(feedback.feedbackType)) {
    return { valid: false, reason: 'Invalid feedback type' };
  }

  return { valid: true };
}

/**
 * Check for potential abuse patterns
 */
async function checkForAbuse(userId) {
  const ABUSE_THRESHOLD = 20; // More than 20 feedback in 24 hours
  const CONFLICTING_THRESHOLD = 5; // More than 5 conflicting feedback

  // Check volume
  const recentFeedback = await prisma.userFeedback.count({
    where: {
      userId,
      createdAt: {
        gte: new Date(Date.now() - 24 * 60 * 60 * 1000), // Last 24 hours
      },
    },
  });

  if (recentFeedback > ABUSE_THRESHOLD) {
    return { flagged: true, reason: 'High volume of feedback' };
  }

  // Check for conflicting patterns (saying same prediction is both right and wrong)
  const recentConflicting = await prisma.$queryRaw`
    SELECT COUNT(DISTINCT feedback_type) as type_count
    FROM user_feedback
    WHERE user_id = ${userId}
      AND created_at > NOW() - INTERVAL '7 days'
      AND original_prediction = actual_label
    GROUP BY scan_history_id
    HAVING COUNT(DISTINCT feedback_type) > 1
  `.catch(() => []);

  if (recentConflicting.length > CONFLICTING_THRESHOLD) {
    return { flagged: true, reason: 'Conflicting feedback patterns' };
  }

  return { flagged: false };
}

/**
 * Calculate feedback quality score (0-100)
 */
async function calculateQualityScore(feedback) {
  let score = 50; // Base score

  // User has submitted feedback before (trusted user)
  const previousApproved = await prisma.userFeedback.count({
    where: {
      userId: feedback.userId,
      status: 'approved',
    },
  });
  if (previousApproved > 0) {
    score += Math.min(previousApproved * 5, 20); // Up to +20 for history
  }

  // Has a comment (more effort = higher quality)
  if (feedback.userComment && feedback.userComment.length > 10) {
    score += 10;
  }

  // False positives/negatives are more valuable than confirmations
  if (feedback.feedbackType !== 'confirmed') {
    score += 10;
  }

  // Recent user activity
  const recentScans = await prisma.scanHistory.count({
    where: {
      userId: feedback.userId,
      scannedAt: {
        gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
      },
    },
  });
  if (recentScans > 10) {
    score += 10; // Active user
  }

  return Math.min(100, score);
}

// Worker event handlers
feedbackWorker.on('completed', (job) => {
  logger.info(`Feedback worker: Job ${job.id} completed`);
});

feedbackWorker.on('failed', (job, err) => {
  logger.error(`Feedback worker: Job ${job?.id} failed`, { error: err.message });
});

feedbackWorker.on('error', (err) => {
  logger.error('Feedback worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('Feedback worker: Shutting down...');
  await feedbackWorker.close();
  logger.info('Feedback worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Feedback worker started');

module.exports = feedbackWorker;
