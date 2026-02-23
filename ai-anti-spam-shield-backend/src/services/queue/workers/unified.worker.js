/**
 * Unified Worker - Single process that handles all queue types
 * Used in production DigitalOcean deployment to save memory
 * Instead of running 6+ separate worker processes, this runs all in one
 */

const logger = require('../../../utils/logger');

logger.info('Unified worker starting - loading all workers...');

// Load all individual workers (each one creates its own BullMQ Worker instance)
const textWorker = require('./text.worker');
const voiceWorker = require('./voice.worker');
const urlWorker = require('./url.worker');
const emailWorker = require('./email.worker');
const feedbackWorker = require('./feedback.worker');
const retrainingWorker = require('./retraining.worker');

// Load email scheduler (auto-starts on require)
const { stopScheduler } = require('./email.scheduler');

const workers = [textWorker, voiceWorker, urlWorker, emailWorker, feedbackWorker, retrainingWorker];

logger.info('Unified worker: All workers loaded', {
  workers: ['text', 'voice', 'url', 'email', 'feedback', 'retraining'],
  schedulerEnabled: true,
});

// Override individual worker shutdown handlers with a unified one
const shutdown = async () => {
  logger.info('Unified worker: Shutting down all workers...');

  // Stop the email scheduler
  stopScheduler();

  // Close all workers
  await Promise.allSettled(workers.map(w => w.close()));

  logger.info('Unified worker: Shutdown complete');
  process.exit(0);
};

// Remove existing handlers and set unified ones
process.removeAllListeners('SIGTERM');
process.removeAllListeners('SIGINT');
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Unified worker started successfully');
