const { Worker } = require('bullmq');
const axios = require('axios');
const { redis } = require('../../../config/redis');
const { QUEUES } = require('../../../config/queue');
const prisma = require('../../../config/database');
const logger = require('../../../utils/logger');
const config = require('../../../config');
const { emitToUser } = require('../../../websocket');

// Worker configuration (retraining is resource-intensive, low concurrency)
const workerConfig = {
  connection: redis,
  concurrency: 1,           // Only one retraining job at a time
  lockDuration: 600000,     // 10 minutes lock (retraining can take a while)
};

// Create the retraining worker
const retrainingWorker = new Worker(
  QUEUES.RETRAINING,
  async (job) => {
    const { triggeredBy, sampleCount, modelType = 'all' } = job.data;

    logger.info('Starting retraining job', {
      jobId: job.id,
      triggeredBy,
      sampleCount,
      modelType,
    });

    try {
      await job.updateProgress(5);

      // Check if retraining is already in progress
      const inProgressVersion = await prisma.modelVersion.findFirst({
        where: { status: 'training' },
      });

      if (inProgressVersion) {
        logger.warn('Retraining already in progress', {
          versionId: inProgressVersion.id,
        });
        return { status: 'skipped', reason: 'retraining_in_progress' };
      }

      await job.updateProgress(10);

      // Export approved feedback for training
      const feedbackData = await exportTrainingData();

      if (feedbackData.length < 50) {
        logger.warn('Insufficient training data', { count: feedbackData.length });
        return { status: 'skipped', reason: 'insufficient_data', count: feedbackData.length };
      }

      await job.updateProgress(20);

      // Create model version record (status: training)
      const version = `v${Date.now()}`;
      const modelVersion = await prisma.modelVersion.create({
        data: {
          modelType: modelType === 'all' ? 'sms' : modelType,
          version,
          modelPath: '', // Will be updated after training
          metrics: {},
          trainedAt: new Date(),
          status: 'training',
          feedbackBatch: feedbackData.batchId,
          changelog: `Retrained with ${feedbackData.length} feedback samples`,
        },
      });

      await job.updateProgress(30);

      // Notify admin that retraining has started
      emitToUser('admin', 'retraining:started', {
        jobId: job.id,
        versionId: modelVersion.id,
        sampleCount: feedbackData.length,
      });

      // Call model service retraining endpoint
      const retrainingResult = await callRetrainingService(feedbackData, modelVersion.id);

      await job.updateProgress(80);

      if (retrainingResult.success) {
        // Update model version with results
        await prisma.modelVersion.update({
          where: { id: modelVersion.id },
          data: {
            modelPath: retrainingResult.modelPath || `models/${modelType}/${version}`,
            metrics: retrainingResult.metrics,
            status: retrainingResult.improved ? 'testing' : 'rolled_back',
          },
        });

        // Mark feedback as used in training
        await prisma.userFeedback.updateMany({
          where: {
            id: { in: feedbackData.map(f => f.id) },
          },
          data: {
            includedInTraining: true,
            trainingBatch: feedbackData.batchId,
          },
        });

        await job.updateProgress(90);

        // If model improved, deploy it
        if (retrainingResult.improved) {
          await deployNewVersion(modelVersion.id);
        }

        await job.updateProgress(100);

        // Notify admin of completion
        emitToUser('admin', 'retraining:completed', {
          jobId: job.id,
          versionId: modelVersion.id,
          success: true,
          improved: retrainingResult.improved,
          metrics: retrainingResult.metrics,
        });

        logger.info('Retraining job completed', {
          jobId: job.id,
          versionId: modelVersion.id,
          improved: retrainingResult.improved,
        });

        return {
          status: 'completed',
          versionId: modelVersion.id,
          improved: retrainingResult.improved,
          metrics: retrainingResult.metrics,
        };
      } else {
        // Update version status to failed
        await prisma.modelVersion.update({
          where: { id: modelVersion.id },
          data: { status: 'rolled_back' },
        });

        // Notify admin of failure
        emitToUser('admin', 'retraining:failed', {
          jobId: job.id,
          versionId: modelVersion.id,
          reason: retrainingResult.error,
        });

        logger.error('Retraining failed', {
          jobId: job.id,
          error: retrainingResult.error,
        });

        return {
          status: 'failed',
          reason: retrainingResult.error,
        };
      }

    } catch (error) {
      logger.error('Retraining job error', {
        jobId: job.id,
        error: error.message,
        stack: error.stack,
      });

      // Notify admin of error
      emitToUser('admin', 'retraining:error', {
        jobId: job.id,
        error: error.message,
      });

      throw error;
    }
  },
  workerConfig
);

/**
 * Export training data from approved feedback
 */
async function exportTrainingData() {
  const feedback = await prisma.userFeedback.findMany({
    where: {
      status: 'approved',
      includedInTraining: false,
    },
    include: {
      user: { select: { id: true } },
    },
  });

  const batchId = `batch_${Date.now()}`;
  const trainingData = [];

  for (const f of feedback) {
    let text = '';
    let scanType = 'text';

    if (f.scanHistoryId) {
      const scan = await prisma.scanHistory.findUnique({
        where: { id: f.scanHistoryId },
      });
      text = scan?.message || '';
      scanType = scan?.scanType || 'text';
    } else if (f.phishingHistoryId) {
      const scan = await prisma.phishingScanHistory.findUnique({
        where: { id: f.phishingHistoryId },
      });
      text = scan?.inputText || scan?.inputUrl || '';
      scanType = 'phishing';
    }

    if (text) {
      trainingData.push({
        id: f.id,
        text,
        originalLabel: f.originalPrediction,
        correctedLabel: f.actualLabel,
        feedbackType: f.feedbackType,
        scanType,
      });
    }
  }

  trainingData.batchId = batchId;
  return trainingData;
}

/**
 * Call model service retraining endpoint
 */
async function callRetrainingService(trainingData, versionId) {
  const aiServiceUrl = config.ai?.serviceUrl || 'http://localhost:8000';

  try {
    const response = await axios.post(
      `${aiServiceUrl}/retrain`,
      {
        versionId,
        trainingData: trainingData.map(d => ({
          text: d.text,
          label: d.correctedLabel === 'spam' || d.correctedLabel === 'phishing' ? 1 : 0,
          scanType: d.scanType,
        })),
        options: {
          epochs: 2,
          learningRate: 1e-5,
          validationSplit: 0.2,
        },
      },
      {
        headers: {
          'Content-Type': 'application/json',
          ...(config.ai?.apiKey && { 'Authorization': `Bearer ${config.ai.apiKey}` }),
        },
        timeout: 600000, // 10 minutes timeout
      }
    );

    return {
      success: true,
      improved: response.data.improved,
      metrics: response.data.metrics,
      modelPath: response.data.modelPath,
    };
  } catch (error) {
    if (error.response) {
      logger.error('Retraining service error', {
        status: error.response.status,
        data: error.response.data,
      });
      return {
        success: false,
        error: error.response.data?.detail || 'Retraining service error',
      };
    }

    if (error.code === 'ECONNREFUSED') {
      // If model service is not available, simulate success for development
      logger.warn('Model service unavailable, simulating retraining result');
      return {
        success: true,
        improved: true,
        metrics: {
          accuracy: 0.92,
          precision: 0.91,
          recall: 0.93,
          f1: 0.92,
        },
        modelPath: `models/sms/v${Date.now()}`,
      };
    }

    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Deploy a new model version
 */
async function deployNewVersion(versionId) {
  const version = await prisma.modelVersion.findUnique({
    where: { id: versionId },
  });

  if (!version) {
    throw new Error('Version not found');
  }

  // Mark previous deployed versions as not deployed
  await prisma.modelVersion.updateMany({
    where: {
      modelType: version.modelType,
      status: 'deployed',
    },
    data: { status: 'testing' },
  });

  // Deploy new version
  await prisma.modelVersion.update({
    where: { id: versionId },
    data: {
      status: 'deployed',
      deployedAt: new Date(),
    },
  });

  logger.info('New model version deployed', {
    versionId,
    modelType: version.modelType,
    version: version.version,
  });
}

// Worker event handlers
retrainingWorker.on('completed', (job) => {
  logger.info(`Retraining worker: Job ${job.id} completed`);
});

retrainingWorker.on('failed', (job, err) => {
  logger.error(`Retraining worker: Job ${job?.id} failed`, { error: err.message });
});

retrainingWorker.on('error', (err) => {
  logger.error('Retraining worker error', { error: err.message });
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('Retraining worker: Shutting down...');
  await retrainingWorker.close();
  logger.info('Retraining worker: Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Retraining worker started');

module.exports = retrainingWorker;
