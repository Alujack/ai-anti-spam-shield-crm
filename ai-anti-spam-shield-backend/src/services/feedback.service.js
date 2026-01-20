const prisma = require('../config/database');
const logger = require('../utils/logger');
const ApiError = require('../utils/apiError');
const { getQueue, QUEUES } = require('../config/queue');

/**
 * Feedback Service
 * Handles user feedback on scan results for continuous learning
 */
class FeedbackService {
  /**
   * Submit user feedback on a scan result
   */
  async submitFeedback({
    userId,
    scanId,
    scanType,
    feedbackType,
    actualLabel,
    comment,
  }) {
    // Get the original scan
    let originalPrediction;
    let scanHistoryId = null;
    let phishingHistoryId = null;

    if (scanType === 'phishing') {
      const scan = await prisma.phishingScanHistory.findUnique({
        where: { id: scanId },
      });
      if (!scan) {
        throw ApiError.notFound('Phishing scan not found');
      }
      // Verify user owns the scan
      if (scan.userId !== userId) {
        throw ApiError.forbidden('You can only provide feedback on your own scans');
      }
      originalPrediction = scan.isPhishing ? 'phishing' : 'safe';
      phishingHistoryId = scanId;
    } else {
      const scan = await prisma.scanHistory.findUnique({
        where: { id: scanId },
      });
      if (!scan) {
        throw ApiError.notFound('Scan not found');
      }
      // Verify user owns the scan
      if (scan.userId !== userId) {
        throw ApiError.forbidden('You can only provide feedback on your own scans');
      }
      originalPrediction = scan.prediction;
      scanHistoryId = scanId;
    }

    // Check for duplicate feedback
    const existingFeedback = await prisma.userFeedback.findFirst({
      where: {
        userId,
        OR: [
          { scanHistoryId: scanHistoryId },
          { phishingHistoryId: phishingHistoryId },
        ],
      },
    });

    if (existingFeedback) {
      throw ApiError.conflict('You have already submitted feedback for this scan');
    }

    // Create feedback record
    const feedback = await prisma.userFeedback.create({
      data: {
        userId,
        scanHistoryId,
        phishingHistoryId,
        originalPrediction,
        actualLabel: actualLabel || this._inferActualLabel(feedbackType, originalPrediction),
        feedbackType,
        userComment: comment,
        status: 'pending',
      },
    });

    logger.info('Feedback submitted', {
      feedbackId: feedback.id,
      userId,
      feedbackType,
      originalPrediction,
    });

    // Queue for processing (if queue is available)
    try {
      const queue = getQueue(QUEUES.FEEDBACK);
      if (queue) {
        await queue.add('process-feedback', {
          feedbackId: feedback.id,
        });
        logger.info('Feedback queued for processing', { feedbackId: feedback.id });
      }
    } catch (error) {
      // Queue might not be available, log but don't fail
      logger.warn('Could not queue feedback for processing', { error: error.message });
    }

    return feedback;
  }

  /**
   * Get pending feedback for admin review
   */
  async getPendingFeedback({ page, limit, feedbackType }) {
    const skip = (page - 1) * limit;

    const where = {
      status: 'pending',
      ...(feedbackType && { feedbackType }),
    };

    const [feedback, total] = await Promise.all([
      prisma.userFeedback.findMany({
        where,
        include: {
          user: {
            select: { id: true, name: true, email: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      prisma.userFeedback.count({ where }),
    ]);

    // Enrich with original scan data
    const enriched = await Promise.all(
      feedback.map(async (f) => {
        let scanData = null;
        if (f.scanHistoryId) {
          scanData = await prisma.scanHistory.findUnique({
            where: { id: f.scanHistoryId },
            select: {
              message: true,
              isSpam: true,
              confidence: true,
              scanType: true,
            },
          });
        } else if (f.phishingHistoryId) {
          scanData = await prisma.phishingScanHistory.findUnique({
            where: { id: f.phishingHistoryId },
            select: {
              inputText: true,
              inputUrl: true,
              isPhishing: true,
              confidence: true,
            },
          });
        }
        return { ...f, scanData };
      })
    );

    return {
      feedback: enriched,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Review feedback (approve/reject)
   */
  async reviewFeedback({ feedbackId, action, reviewerId, notes }) {
    const existingFeedback = await prisma.userFeedback.findUnique({
      where: { id: feedbackId },
    });

    if (!existingFeedback) {
      throw ApiError.notFound('Feedback not found');
    }

    if (existingFeedback.status !== 'pending') {
      throw ApiError.badRequest('Feedback has already been reviewed');
    }

    const status = action === 'approve' ? 'approved' : 'rejected';

    const feedback = await prisma.userFeedback.update({
      where: { id: feedbackId },
      data: {
        status,
        reviewedBy: reviewerId,
        reviewedAt: new Date(),
      },
    });

    logger.info('Feedback reviewed', {
      feedbackId,
      action,
      reviewerId,
    });

    // If approved, check if we should trigger retraining
    if (status === 'approved') {
      await this._checkRetrainingTrigger();
    }

    return feedback;
  }

  /**
   * Get feedback statistics
   */
  async getStatistics() {
    const [byStatus, byType, recentTrend, totalCount] = await Promise.all([
      // By status
      prisma.userFeedback.groupBy({
        by: ['status'],
        _count: true,
      }),

      // By feedback type
      prisma.userFeedback.groupBy({
        by: ['feedbackType'],
        _count: true,
      }),

      // Recent trend (last 30 days) - using a simpler approach
      prisma.$queryRaw`
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM user_feedback
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
      `.catch(() => []), // Return empty if query fails

      // Total count
      prisma.userFeedback.count(),
    ]);

    // Calculate false positive/negative rates
    const approved = await prisma.userFeedback.findMany({
      where: { status: 'approved' },
      select: { feedbackType: true, originalPrediction: true },
    });

    const falsePositives = approved.filter(f => f.feedbackType === 'false_positive').length;
    const falseNegatives = approved.filter(f => f.feedbackType === 'false_negative').length;
    const totalApproved = approved.length;

    return {
      total: totalCount,
      byStatus: byStatus.reduce((acc, s) => ({ ...acc, [s.status]: s._count }), {}),
      byType: byType.reduce((acc, t) => ({ ...acc, [t.feedbackType]: t._count }), {}),
      rates: {
        falsePositiveRate: totalApproved > 0 ? (falsePositives / totalApproved).toFixed(4) : 0,
        falseNegativeRate: totalApproved > 0 ? (falseNegatives / totalApproved).toFixed(4) : 0,
      },
      recentTrend,
      pendingCount: byStatus.find(s => s.status === 'pending')?._count || 0,
      approvedCount: byStatus.find(s => s.status === 'approved')?._count || 0,
      rejectedCount: byStatus.find(s => s.status === 'rejected')?._count || 0,
    };
  }

  /**
   * Export approved feedback for training
   */
  async exportApprovedFeedback({ format, since }) {
    const where = {
      status: 'approved',
      includedInTraining: false,
      ...(since && { createdAt: { gte: since } }),
    };

    const feedback = await prisma.userFeedback.findMany({
      where,
      include: {
        user: {
          select: { id: true },
        },
      },
    });

    // Get associated scan data
    const trainingData = await Promise.all(
      feedback.map(async (f) => {
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

        return {
          id: f.id,
          text,
          originalLabel: f.originalPrediction,
          correctedLabel: f.actualLabel,
          feedbackType: f.feedbackType,
          scanType,
          timestamp: f.createdAt.toISOString(),
        };
      })
    );

    // Generate batch ID
    const batchId = `batch_${Date.now()}`;

    // Mark as exported
    const feedbackIds = feedback.map(f => f.id);
    if (feedbackIds.length > 0) {
      await prisma.userFeedback.updateMany({
        where: { id: { in: feedbackIds } },
        data: {
          includedInTraining: true,
          trainingBatch: batchId,
        },
      });
    }

    logger.info('Feedback exported for training', {
      batchId,
      count: trainingData.length,
    });

    // Handle CSV format
    if (format === 'csv') {
      const csv = this._convertToCSV(trainingData);
      return {
        batchId,
        count: trainingData.length,
        csv,
      };
    }

    return {
      batchId,
      count: trainingData.length,
      data: trainingData,
    };
  }

  /**
   * Get user's own feedback history
   */
  async getUserFeedback({ userId, page, limit }) {
    const skip = (page - 1) * limit;

    const [feedback, total] = await Promise.all([
      prisma.userFeedback.findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      prisma.userFeedback.count({ where: { userId } }),
    ]);

    return {
      feedback,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get feedback by ID
   */
  async getFeedbackById(id, userId, isAdmin) {
    const feedback = await prisma.userFeedback.findUnique({
      where: { id },
      include: {
        user: {
          select: { id: true, name: true, email: true },
        },
      },
    });

    if (!feedback) {
      throw ApiError.notFound('Feedback not found');
    }

    // Non-admin users can only view their own feedback
    if (!isAdmin && feedback.userId !== userId) {
      throw ApiError.forbidden('You can only view your own feedback');
    }

    // Enrich with scan data
    let scanData = null;
    if (feedback.scanHistoryId) {
      scanData = await prisma.scanHistory.findUnique({
        where: { id: feedback.scanHistoryId },
        select: {
          message: true,
          isSpam: true,
          confidence: true,
          scanType: true,
        },
      });
    } else if (feedback.phishingHistoryId) {
      scanData = await prisma.phishingScanHistory.findUnique({
        where: { id: feedback.phishingHistoryId },
        select: {
          inputText: true,
          inputUrl: true,
          isPhishing: true,
          confidence: true,
        },
      });
    }

    return { ...feedback, scanData };
  }

  /**
   * Infer actual label from feedback type
   */
  _inferActualLabel(feedbackType, originalPrediction) {
    if (feedbackType === 'confirmed') {
      return originalPrediction;
    }
    if (feedbackType === 'false_positive') {
      // Predicted spam/phishing but was actually safe
      return originalPrediction === 'spam' ? 'ham' : 'safe';
    }
    if (feedbackType === 'false_negative') {
      // Predicted safe but was actually spam/phishing
      return originalPrediction === 'ham' ? 'spam' : 'phishing';
    }
    return originalPrediction;
  }

  /**
   * Check if we should trigger retraining based on approved feedback count
   */
  async _checkRetrainingTrigger() {
    const MIN_SAMPLES_FOR_RETRAIN = 50;

    const approvedNotTrained = await prisma.userFeedback.count({
      where: {
        status: 'approved',
        includedInTraining: false,
      },
    });

    if (approvedNotTrained >= MIN_SAMPLES_FOR_RETRAIN) {
      logger.info('Retraining threshold reached', {
        approvedCount: approvedNotTrained,
        threshold: MIN_SAMPLES_FOR_RETRAIN,
      });

      // Queue retraining job
      try {
        const queue = getQueue(QUEUES.RETRAINING);
        if (queue) {
          await queue.add('trigger-retraining', {
            triggeredBy: 'feedback_threshold',
            sampleCount: approvedNotTrained,
            timestamp: Date.now(),
          });
          logger.info('Retraining job queued');
        }
      } catch (error) {
        logger.warn('Could not queue retraining job', { error: error.message });
      }
    }
  }

  /**
   * Convert training data to CSV format
   */
  _convertToCSV(data) {
    if (data.length === 0) {
      return 'id,text,originalLabel,correctedLabel,feedbackType,scanType,timestamp\n';
    }

    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(item => {
      return Object.values(item).map(value => {
        // Escape quotes and wrap in quotes if needed
        const str = String(value);
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      }).join(',');
    }).join('\n');

    return `${headers}\n${rows}`;
  }
}

module.exports = new FeedbackService();
