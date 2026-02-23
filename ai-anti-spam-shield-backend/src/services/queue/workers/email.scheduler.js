const { getQueue, QUEUES } = require('../../../config/queue');
const emailService = require('../../email.service');
const logger = require('../../../utils/logger');

// Check every 60 seconds for accounts due for auto-scan
const SCHEDULER_INTERVAL_MS = 60 * 1000;

let schedulerInterval = null;

/**
 * Check for email accounts that are due for auto-scan and enqueue jobs
 */
async function checkAndEnqueueScans() {
  try {
    const accountsDue = await emailService.getAccountsDueForScan();

    if (accountsDue.length === 0) return;

    logger.info(`Email scheduler: Found ${accountsDue.length} account(s) due for scan`);

    const queue = getQueue(QUEUES.EMAIL_SCAN);

    for (const account of accountsDue) {
      try {
        await queue.add(
          'email-scan-scheduled',
          {
            emailAccountId: account.id,
            userId: account.userId,
            scheduled: true,
          },
          { priority: 3 } // Lower priority than manual scans
        );

        logger.info('Email scheduler: Enqueued scan job', {
          accountId: account.id,
          email: account.email,
        });
      } catch (err) {
        logger.error('Email scheduler: Failed to enqueue scan job', {
          accountId: account.id,
          error: err.message,
        });
      }
    }
  } catch (error) {
    logger.error('Email scheduler: Check failed', { error: error.message });
  }
}

/**
 * Start the email scan scheduler
 */
function startScheduler() {
  logger.info('Email scheduler started');
  schedulerInterval = setInterval(checkAndEnqueueScans, SCHEDULER_INTERVAL_MS);
  // Run immediately on start
  checkAndEnqueueScans();
}

/**
 * Stop the scheduler
 */
function stopScheduler() {
  if (schedulerInterval) {
    clearInterval(schedulerInterval);
    schedulerInterval = null;
  }
  logger.info('Email scheduler stopped');
}

// Graceful shutdown
const shutdown = () => {
  stopScheduler();
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Auto-start when this module is loaded as a standalone process
startScheduler();

module.exports = { startScheduler, stopScheduler };
