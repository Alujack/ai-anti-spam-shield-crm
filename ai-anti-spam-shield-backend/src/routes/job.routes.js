const express = require('express');
const router = express.Router();
const queueManager = require('../services/queue/queue.manager');
const { QUEUES } = require('../config/queue');
const { authenticate } = require('../middlewares/auth');

/**
 * @swagger
 * /jobs/{queueName}/{jobId}:
 *   get:
 *     summary: Get job status
 *     tags: [Jobs]
 *     parameters:
 *       - in: path
 *         name: queueName
 *         required: true
 *         schema:
 *           type: string
 *           enum: [text-scan, voice-scan, url-scan]
 *       - in: path
 *         name: jobId
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Job status
 *       404:
 *         description: Job not found
 */
router.get('/:queueName/:jobId', async (req, res, next) => {
  try {
    const { queueName, jobId } = req.params;

    // Validate queue name
    if (!Object.values(QUEUES).includes(queueName)) {
      return res.status(400).json({
        status: 'error',
        message: 'Invalid queue name',
        validQueues: Object.values(QUEUES),
      });
    }

    const status = await queueManager.getJobStatus(queueName, jobId);

    if (status.status === 'not_found') {
      return res.status(404).json({
        status: 'error',
        message: 'Job not found',
      });
    }

    res.json({
      status: 'success',
      data: status,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /jobs/{queueName}/{jobId}:
 *   delete:
 *     summary: Cancel a pending job
 *     tags: [Jobs]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: queueName
 *         required: true
 *         schema:
 *           type: string
 *       - in: path
 *         name: jobId
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Job cancelled
 *       400:
 *         description: Cannot cancel job
 *       404:
 *         description: Job not found
 */
router.delete('/:queueName/:jobId', authenticate, async (req, res, next) => {
  try {
    const { queueName, jobId } = req.params;

    const cancelled = await queueManager.cancelJob(queueName, jobId);

    if (!cancelled) {
      return res.status(400).json({
        status: 'error',
        message: 'Cannot cancel job (not found or already processing)',
      });
    }

    res.json({
      status: 'success',
      message: 'Job cancelled',
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /jobs/stats:
 *   get:
 *     summary: Get queue statistics
 *     tags: [Jobs]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Queue statistics
 */
router.get('/stats', authenticate, async (req, res, next) => {
  try {
    const stats = await queueManager.getAllQueueStats();

    res.json({
      status: 'success',
      data: stats,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /jobs/stats/{queueName}:
 *   get:
 *     summary: Get statistics for a specific queue
 *     tags: [Jobs]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: queueName
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Queue statistics
 */
router.get('/stats/:queueName', authenticate, async (req, res, next) => {
  try {
    const { queueName } = req.params;

    if (!Object.values(QUEUES).includes(queueName)) {
      return res.status(400).json({
        status: 'error',
        message: 'Invalid queue name',
      });
    }

    const stats = await queueManager.getQueueStats(queueName);

    res.json({
      status: 'success',
      data: stats,
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
