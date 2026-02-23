const emailService = require('../services/email.service');
const { getQueue, QUEUES } = require('../config/queue');
const ApiError = require('../utils/apiError');
const logger = require('../utils/logger');

/**
 * Connect a new email account
 */
const connectAccount = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { email, password, provider, imapHost, imapPort } = req.body;

    if (!email || !password) {
      throw ApiError.badRequest('Email and password are required');
    }

    if (!provider) {
      throw ApiError.badRequest('Provider is required (gmail, outlook, yahoo, or other)');
    }

    const account = await emailService.connectAccount(userId, {
      email,
      password,
      imapHost,
      imapPort,
      provider,
    });

    res.status(201).json({
      status: 'success',
      message: 'Email account connected successfully',
      data: account,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * List connected email accounts
 */
const getAccounts = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const accounts = await emailService.getAccounts(userId);

    res.status(200).json({
      status: 'success',
      message: 'Email accounts retrieved successfully',
      data: accounts,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get email account details
 */
const getAccountById = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;

    const account = await emailService.getAccountById(id, userId);

    res.status(200).json({
      status: 'success',
      message: 'Email account retrieved successfully',
      data: account,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Disconnect an email account
 */
const disconnectAccount = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;

    const result = await emailService.disconnectAccount(id, userId);

    res.status(200).json({
      status: 'success',
      message: result.message,
      data: null,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Update email account settings
 */
const updateSettings = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;
    const { autoScanInterval, isActive } = req.body;

    const account = await emailService.updateSettings(id, userId, {
      autoScanInterval,
      isActive,
    });

    res.status(200).json({
      status: 'success',
      message: 'Settings updated successfully',
      data: account,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Trigger a manual email scan
 */
const triggerScan = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;

    // Verify ownership
    await emailService.getAccountById(id, userId);

    // Enqueue scan job
    try {
      const queue = getQueue(QUEUES.EMAIL_SCAN);
      await queue.add('email-scan', { emailAccountId: id, userId }, { priority: 1 });

      res.status(202).json({
        status: 'success',
        message: 'Email scan started. You will be notified when it completes.',
        data: { accountId: id, status: 'queued' },
      });
    } catch (queueError) {
      // If queue is not available, scan directly
      logger.warn('Queue not available, scanning directly', { error: queueError.message });

      const result = await emailService.scanEmails(id);

      res.status(200).json({
        status: 'success',
        message: 'Email scan completed',
        data: result,
      });
    }
  } catch (error) {
    next(error);
  }
};

/**
 * Get scan results for an account
 */
const getScanResults = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;
    const { page, limit, flaggedOnly } = req.query;

    const results = await emailService.getScanResults(id, userId, {
      page,
      limit,
      flaggedOnly: flaggedOnly === 'true',
    });

    res.status(200).json({
      status: 'success',
      message: 'Scan results retrieved successfully',
      data: results,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get flagged emails for an account
 */
const getFlaggedEmails = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;
    const { page, limit } = req.query;

    const results = await emailService.getFlaggedEmails(id, userId, { page, limit });

    res.status(200).json({
      status: 'success',
      message: 'Flagged emails retrieved successfully',
      data: results,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Clean (trash) flagged emails
 */
const cleanFlaggedEmails = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;
    const { emailIds } = req.body;

    const result = await emailService.cleanFlaggedEmails(id, userId, emailIds);

    res.status(200).json({
      status: 'success',
      message: result.message,
      data: result,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get overall email scan statistics
 */
const getStatistics = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const stats = await emailService.getStatistics(userId);

    res.status(200).json({
      status: 'success',
      message: 'Statistics retrieved successfully',
      data: stats,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  connectAccount,
  getAccounts,
  getAccountById,
  disconnectAccount,
  updateSettings,
  triggerScan,
  getScanResults,
  getFlaggedEmails,
  cleanFlaggedEmails,
  getStatistics,
};
