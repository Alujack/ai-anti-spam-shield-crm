const feedbackService = require('../services/feedback.service');
const ApiError = require('../utils/apiError');
const logger = require('../utils/logger');

/**
 * Submit feedback on a scan result
 */
const submitFeedback = async (req, res, next) => {
  try {
    const { scanId, scanType, feedbackType, actualLabel, comment } = req.body;

    // Validate input
    if (!scanId || !feedbackType) {
      throw ApiError.badRequest('scanId and feedbackType are required');
    }

    const validFeedbackTypes = ['false_positive', 'false_negative', 'confirmed'];
    if (!validFeedbackTypes.includes(feedbackType)) {
      throw ApiError.badRequest(`feedbackType must be one of: ${validFeedbackTypes.join(', ')}`);
    }

    logger.info('Submitting feedback', {
      userId: req.user.id,
      scanId,
      feedbackType,
    });

    const feedback = await feedbackService.submitFeedback({
      userId: req.user.id,
      scanId,
      scanType: scanType || 'text',
      feedbackType,
      actualLabel,
      comment,
    });

    logger.info('Feedback submitted successfully', {
      feedbackId: feedback.id,
      userId: req.user.id,
    });

    res.status(201).json({
      status: 'success',
      message: 'Feedback submitted successfully',
      data: feedback,
    });
  } catch (error) {
    logger.error('Error submitting feedback', { error: error.message });
    next(error);
  }
};

/**
 * Get pending feedback for admin review
 */
const getPendingFeedback = async (req, res, next) => {
  try {
    const { page = 1, limit = 20, type } = req.query;

    const result = await feedbackService.getPendingFeedback({
      page: parseInt(page),
      limit: parseInt(limit),
      feedbackType: type,
    });

    res.status(200).json({
      status: 'success',
      message: 'Pending feedback retrieved successfully',
      data: result.feedback,
      pagination: result.pagination,
    });
  } catch (error) {
    logger.error('Error getting pending feedback', { error: error.message });
    next(error);
  }
};

/**
 * Review feedback (approve/reject)
 */
const reviewFeedback = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { action, notes } = req.body;

    if (!['approve', 'reject'].includes(action)) {
      throw ApiError.badRequest('action must be approve or reject');
    }

    logger.info('Reviewing feedback', {
      feedbackId: id,
      action,
      reviewerId: req.user.id,
    });

    const feedback = await feedbackService.reviewFeedback({
      feedbackId: id,
      action,
      reviewerId: req.user.id,
      notes,
    });

    res.status(200).json({
      status: 'success',
      message: `Feedback ${action}d successfully`,
      data: feedback,
    });
  } catch (error) {
    logger.error('Error reviewing feedback', { error: error.message });
    next(error);
  }
};

/**
 * Get feedback statistics
 */
const getFeedbackStats = async (req, res, next) => {
  try {
    const stats = await feedbackService.getStatistics();

    res.status(200).json({
      status: 'success',
      message: 'Feedback statistics retrieved successfully',
      data: stats,
    });
  } catch (error) {
    logger.error('Error getting feedback stats', { error: error.message });
    next(error);
  }
};

/**
 * Export approved feedback for training
 */
const exportForTraining = async (req, res, next) => {
  try {
    const { format = 'json', since } = req.query;

    logger.info('Exporting feedback for training', {
      format,
      since,
      userId: req.user.id,
    });

    const data = await feedbackService.exportApprovedFeedback({
      format,
      since: since ? new Date(since) : null,
    });

    if (format === 'csv') {
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename=training_feedback.csv');
      return res.send(data.csv);
    }

    res.status(200).json({
      status: 'success',
      message: 'Feedback exported successfully',
      data,
    });
  } catch (error) {
    logger.error('Error exporting feedback', { error: error.message });
    next(error);
  }
};

/**
 * Get current user's feedback history
 */
const getMyFeedback = async (req, res, next) => {
  try {
    const { page = 1, limit = 20 } = req.query;

    const result = await feedbackService.getUserFeedback({
      userId: req.user.id,
      page: parseInt(page),
      limit: parseInt(limit),
    });

    res.status(200).json({
      status: 'success',
      message: 'Feedback history retrieved successfully',
      data: result.feedback,
      pagination: result.pagination,
    });
  } catch (error) {
    logger.error('Error getting user feedback', { error: error.message });
    next(error);
  }
};

/**
 * Get feedback by ID
 */
const getFeedbackById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const isAdmin = req.user.role === 'ADMIN';

    const feedback = await feedbackService.getFeedbackById(id, userId, isAdmin);

    res.status(200).json({
      status: 'success',
      message: 'Feedback retrieved successfully',
      data: feedback,
    });
  } catch (error) {
    logger.error('Error getting feedback by ID', { error: error.message });
    next(error);
  }
};

module.exports = {
  submitFeedback,
  getPendingFeedback,
  reviewFeedback,
  getFeedbackStats,
  exportForTraining,
  getMyFeedback,
  getFeedbackById,
};
