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
   * Add a feedback processing job to the queue
   * @param {Object} data - Job data
   * @param {string} data.feedbackId - Feedback ID to process
   * @param {Object} options - Job options
   * @returns {Promise<Object>} Job info
   */
  async addFeedbackJob(data, options = {}) {
    const queue = getQueue(QUEUES.FEEDBACK);

    const jobData = {
      feedbackId: data.feedbackId,
      timestamp: Date.now(),
    };

    const job = await queue.add('process-feedback', jobData, {
      priority: options.priority || 3,
      ...options,
    });

    logger.info('Feedback job added', {
      jobId: job.id,
      feedbackId: data.feedbackId,
    });

    return {
      jobId: job.id,
      queue: QUEUES.FEEDBACK,
      status: 'queued',
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Add a model retraining job to the queue
   * @param {Object} data - Job data
   * @param {string} data.modelType - Type of model to retrain (sms, phishing, voice, all)
   * @param {string} data.triggeredBy - What triggered the retraining
   * @param {Object} options - Job options
   * @returns {Promise<Object>} Job info
   */
  async addRetrainingJob(data, options = {}) {
    const queue = getQueue(QUEUES.RETRAINING);

    const jobData = {
      modelType: data.modelType || 'all',
      triggeredBy: data.triggeredBy || 'manual',
      sampleCount: data.sampleCount || 0,
      timestamp: Date.now(),
    };

    const job = await queue.add('model-retraining', jobData, {
      priority: options.priority || 4,
      attempts: 1, // Don't auto-retry retraining
      ...options,
    });

    logger.info('Retraining job added', {
      jobId: job.id,
      modelType: data.modelType,
      triggeredBy: data.triggeredBy,
    });

    return {
      jobId: job.id,
      queue: QUEUES.RETRAINING,
      status: 'queued',
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Trigger model retraining if threshold is met
   * @param {number} threshold - Minimum samples required
   * @returns {Promise<Object|null>} Job info if triggered, null otherwise
   */
  async triggerRetrainingIfNeeded(threshold = 50) {
    const prisma = require('../../config/database');

    const approvedCount = await prisma.userFeedback.count({
      where: {
        status: 'approved',
        includedInTraining: false,
      },
    });

    if (approvedCount >= threshold) {
      logger.info('Retraining threshold reached', {
        approvedCount,
        threshold,
      });

      return this.addRetrainingJob({
        triggeredBy: 'threshold',
        sampleCount: approvedCount,
      });
    }

    return null;
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
