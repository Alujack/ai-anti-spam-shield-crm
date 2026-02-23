const { ImapFlow } = require('imapflow');
const { simpleParser } = require('mailparser');
const axios = require('axios');
const config = require('../config');
const prisma = require('../config/database');
const { encrypt, decrypt } = require('../utils/encryption');
const ApiError = require('../utils/apiError');
const logger = require('../utils/logger');

// IMAP provider presets
const PROVIDER_PRESETS = {
  gmail: { host: 'imap.gmail.com', port: 993 },
  outlook: { host: 'outlook.office365.com', port: 993 },
  yahoo: { host: 'imap.mail.yahoo.com', port: 993 },
  other: null,
};

// Max emails to fetch per scan batch
const MAX_EMAILS_PER_SCAN = 100;

// Default lookback period for first scan (7 days)
const DEFAULT_LOOKBACK_DAYS = 7;

class EmailService {
  /**
   * Create an IMAP client connection
   */
  _createImapClient(host, port, email, password) {
    return new ImapFlow({
      host,
      port,
      secure: true,
      auth: {
        user: email,
        pass: password,
      },
      logger: false,
    });
  }

  /**
   * Test IMAP connection with provided credentials
   */
  async testConnection(imapHost, imapPort, email, password) {
    const client = this._createImapClient(imapHost, imapPort, email, password);
    try {
      await client.connect();
      await client.logout();
      return true;
    } catch (error) {
      logger.error('IMAP connection test failed', {
        host: imapHost,
        email,
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Connect a new email account
   */
  async connectAccount(userId, { email, password, imapHost, imapPort, provider }) {
    // Resolve IMAP settings from provider presets
    const preset = PROVIDER_PRESETS[provider];
    const host = imapHost || (preset ? preset.host : null);
    const port = imapPort || (preset ? preset.port : 993);

    if (!host) {
      throw ApiError.badRequest('IMAP host is required for custom providers');
    }

    // Test connection before saving
    const isConnected = await this.testConnection(host, port, email, password);
    if (!isConnected) {
      throw ApiError.badRequest(
        'Failed to connect to email server. Please check your credentials and IMAP settings. For Gmail, make sure you use an App Password.'
      );
    }

    // Check if account already exists
    const existing = await prisma.emailAccount.findUnique({
      where: { userId_email: { userId, email } },
    });

    if (existing) {
      throw ApiError.badRequest('This email account is already connected');
    }

    // Encrypt password and save
    const encryptedPassword = encrypt(password);

    const account = await prisma.emailAccount.create({
      data: {
        userId,
        email,
        imapHost: host,
        imapPort: port,
        password: encryptedPassword,
        provider: provider || 'other',
        isActive: true,
        autoScanInterval: 0,
      },
    });

    logger.info('Email account connected', { accountId: account.id, userId, email });

    return {
      id: account.id,
      email: account.email,
      provider: account.provider,
      imapHost: account.imapHost,
      imapPort: account.imapPort,
      isActive: account.isActive,
      autoScanInterval: account.autoScanInterval,
      createdAt: account.createdAt,
    };
  }

  /**
   * Get all email accounts for a user
   */
  async getAccounts(userId) {
    const accounts = await prisma.emailAccount.findMany({
      where: { userId },
      select: {
        id: true,
        email: true,
        provider: true,
        imapHost: true,
        imapPort: true,
        isActive: true,
        autoScanInterval: true,
        lastScanAt: true,
        lastScanStatus: true,
        totalScanned: true,
        totalFlagged: true,
        createdAt: true,
        updatedAt: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    return accounts;
  }

  /**
   * Get a single email account by ID (with ownership check)
   */
  async getAccountById(accountId, userId) {
    const account = await prisma.emailAccount.findFirst({
      where: { id: accountId, userId },
      select: {
        id: true,
        email: true,
        provider: true,
        imapHost: true,
        imapPort: true,
        isActive: true,
        autoScanInterval: true,
        lastScanAt: true,
        lastScanStatus: true,
        totalScanned: true,
        totalFlagged: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    if (!account) {
      throw ApiError.notFound('Email account not found');
    }

    // Get flagged count
    const flaggedCount = await prisma.emailScanResult.count({
      where: { emailAccountId: accountId, isFlagged: true, isCleaned: false },
    });

    return { ...account, pendingFlaggedCount: flaggedCount };
  }

  /**
   * Disconnect (delete) an email account and all its scan results
   */
  async disconnectAccount(accountId, userId) {
    const account = await prisma.emailAccount.findFirst({
      where: { id: accountId, userId },
    });

    if (!account) {
      throw ApiError.notFound('Email account not found');
    }

    await prisma.emailAccount.delete({ where: { id: accountId } });

    logger.info('Email account disconnected', { accountId, userId });
    return { message: 'Email account disconnected successfully' };
  }

  /**
   * Update email account settings (auto-scan interval, isActive)
   */
  async updateSettings(accountId, userId, { autoScanInterval, isActive }) {
    const account = await prisma.emailAccount.findFirst({
      where: { id: accountId, userId },
    });

    if (!account) {
      throw ApiError.notFound('Email account not found');
    }

    const updateData = {};
    if (autoScanInterval !== undefined) updateData.autoScanInterval = autoScanInterval;
    if (isActive !== undefined) updateData.isActive = isActive;

    const updated = await prisma.emailAccount.update({
      where: { id: accountId },
      data: updateData,
      select: {
        id: true,
        email: true,
        provider: true,
        isActive: true,
        autoScanInterval: true,
        lastScanAt: true,
        lastScanStatus: true,
      },
    });

    logger.info('Email account settings updated', { accountId, ...updateData });
    return updated;
  }

  /**
   * Scan emails for a given account
   * This is the core scanning logic used by both manual trigger and worker
   */
  async scanEmails(accountId) {
    const account = await prisma.emailAccount.findUnique({
      where: { id: accountId },
    });

    if (!account) {
      throw ApiError.notFound('Email account not found');
    }

    // Mark as scanning
    await prisma.emailAccount.update({
      where: { id: accountId },
      data: { lastScanStatus: 'scanning' },
    });

    const decryptedPassword = decrypt(account.password);
    const client = this._createImapClient(
      account.imapHost,
      account.imapPort,
      account.email,
      decryptedPassword
    );

    let scannedCount = 0;
    let flaggedCount = 0;

    try {
      await client.connect();

      // Open INBOX
      const mailbox = await client.getMailboxLock('INBOX');

      try {
        // Determine the date to scan from
        const sinceDate = account.lastScanAt
          ? new Date(account.lastScanAt)
          : new Date(Date.now() - DEFAULT_LOOKBACK_DAYS * 24 * 60 * 60 * 1000);

        // Search for emails since the last scan
        const messages = [];
        for await (const message of client.fetch(
          { since: sinceDate },
          { envelope: true, source: true, uid: true }
        )) {
          messages.push(message);
          if (messages.length >= MAX_EMAILS_PER_SCAN) break;
        }

        logger.info('Fetched emails for scanning', {
          accountId,
          count: messages.length,
          since: sinceDate.toISOString(),
        });

        // Process each email
        for (const message of messages) {
          try {
            const result = await this._processEmail(account, message);
            scannedCount++;
            if (result.isFlagged) flaggedCount++;
          } catch (err) {
            logger.error('Failed to process email', {
              accountId,
              uid: message.uid,
              error: err.message,
            });
          }
        }
      } finally {
        mailbox.release();
      }

      await client.logout();

      // Update account stats
      await prisma.emailAccount.update({
        where: { id: accountId },
        data: {
          lastScanAt: new Date(),
          lastScanStatus: 'success',
          totalScanned: { increment: scannedCount },
          totalFlagged: { increment: flaggedCount },
        },
      });

      logger.info('Email scan completed', { accountId, scannedCount, flaggedCount });

      return { scannedCount, flaggedCount };
    } catch (error) {
      await prisma.emailAccount.update({
        where: { id: accountId },
        data: { lastScanStatus: 'failed' },
      });

      logger.error('Email scan failed', { accountId, error: error.message });
      throw ApiError.internal(`Email scan failed: ${error.message}`);
    }
  }

  /**
   * Process a single email: parse, analyze with AI, save result
   */
  async _processEmail(account, message) {
    const uid = String(message.uid);

    // Check if already scanned
    const existing = await prisma.emailScanResult.findUnique({
      where: { emailAccountId_messageId: { emailAccountId: account.id, messageId: uid } },
    });
    if (existing) return existing;

    // Parse email content
    const parsed = await simpleParser(message.source);
    const subject = parsed.subject || '(No Subject)';
    const sender = parsed.from?.text || 'Unknown';
    const receivedAt = parsed.date || new Date();
    const textBody = parsed.text || '';
    const snippet = textBody.substring(0, 200);

    // Combine subject and body for scanning
    const contentToScan = `${subject}\n${textBody}`.substring(0, 2000);

    // Call AI services for spam and phishing detection
    let isSpam = false;
    let spamConfidence = 0;
    let isPhishing = false;
    let phishingConfidence = 0;
    let threatLevel = 'NONE';

    try {
      // Spam detection
      const spamResponse = await axios.post(
        `${config.ai.serviceUrl}/predict`,
        { message: contentToScan },
        { timeout: 15000 }
      );
      spamConfidence = spamResponse.data.confidence || spamResponse.data.probability || 0;
      isSpam = spamConfidence >= 0.80;
    } catch (err) {
      logger.warn('Spam AI service call failed for email', { uid, error: err.message });
    }

    try {
      // Phishing detection
      const phishingResponse = await axios.post(
        `${config.ai.serviceUrl}/predict-phishing`,
        { text: contentToScan, scan_type: 'email' },
        { timeout: 15000 }
      );
      phishingConfidence = phishingResponse.data.confidence || 0;
      isPhishing = phishingConfidence >= 0.70;
    } catch (err) {
      logger.warn('Phishing AI service call failed for email', { uid, error: err.message });
    }

    // Determine threat level
    const maxConfidence = Math.max(
      isSpam ? spamConfidence : 0,
      isPhishing ? phishingConfidence : 0
    );
    if (maxConfidence >= 0.90) threatLevel = 'CRITICAL';
    else if (maxConfidence >= 0.80) threatLevel = 'HIGH';
    else if (maxConfidence >= 0.60) threatLevel = 'MEDIUM';
    else if (maxConfidence >= 0.40) threatLevel = 'LOW';
    else threatLevel = 'NONE';

    const isFlagged = isSpam || isPhishing;

    // Save result
    const scanResult = await prisma.emailScanResult.create({
      data: {
        emailAccountId: account.id,
        userId: account.userId,
        messageId: uid,
        subject,
        sender,
        receivedAt,
        snippet,
        isSpam,
        spamConfidence,
        isPhishing,
        phishingConfidence,
        threatLevel,
        isFlagged,
      },
    });

    return scanResult;
  }

  /**
   * Get scan results for an account (paginated)
   */
  async getScanResults(accountId, userId, filters = {}) {
    // Verify ownership
    const account = await prisma.emailAccount.findFirst({
      where: { id: accountId, userId },
    });
    if (!account) throw ApiError.notFound('Email account not found');

    const { page = 1, limit = 20, flaggedOnly = false } = filters;
    const skip = (page - 1) * limit;

    const where = {
      emailAccountId: accountId,
      ...(flaggedOnly && { isFlagged: true, isCleaned: false }),
    };

    const [results, total] = await Promise.all([
      prisma.emailScanResult.findMany({
        where,
        orderBy: { receivedAt: 'desc' },
        skip,
        take: parseInt(limit),
      }),
      prisma.emailScanResult.count({ where }),
    ]);

    return {
      results,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get flagged (uncleaned) emails for an account
   */
  async getFlaggedEmails(accountId, userId, filters = {}) {
    return this.getScanResults(accountId, userId, { ...filters, flaggedOnly: true });
  }

  /**
   * Clean (trash) flagged emails via IMAP
   */
  async cleanFlaggedEmails(accountId, userId, emailIds = null) {
    const account = await prisma.emailAccount.findFirst({
      where: { id: accountId, userId },
    });
    if (!account) throw ApiError.notFound('Email account not found');

    // Get emails to clean
    const where = {
      emailAccountId: accountId,
      isFlagged: true,
      isCleaned: false,
      ...(emailIds && { id: { in: emailIds } }),
    };

    const emailsToClean = await prisma.emailScanResult.findMany({ where });

    if (emailsToClean.length === 0) {
      return { cleanedCount: 0, message: 'No flagged emails to clean' };
    }

    // Connect to IMAP and move emails to Trash
    const decryptedPassword = decrypt(account.password);
    const client = this._createImapClient(
      account.imapHost,
      account.imapPort,
      account.email,
      decryptedPassword
    );

    let cleanedCount = 0;

    try {
      await client.connect();
      const mailbox = await client.getMailboxLock('INBOX');

      try {
        // Get the Trash folder path (varies by provider)
        const trashPath = await this._getTrashFolder(client, account.provider);

        for (const email of emailsToClean) {
          try {
            // Move message to Trash by UID
            await client.messageMove(email.messageId, trashPath, { uid: true });
            cleanedCount++;
          } catch (err) {
            logger.warn('Failed to move email to trash', {
              messageId: email.messageId,
              error: err.message,
            });
          }
        }
      } finally {
        mailbox.release();
      }

      await client.logout();
    } catch (error) {
      logger.error('IMAP clean operation failed', { accountId, error: error.message });
      throw ApiError.internal(`Failed to clean emails: ${error.message}`);
    }

    // Update database records
    const cleanedIds = emailsToClean.slice(0, cleanedCount).map((e) => e.id);
    if (cleanedIds.length > 0) {
      await prisma.emailScanResult.updateMany({
        where: { id: { in: cleanedIds } },
        data: { isCleaned: true, cleanedAt: new Date() },
      });
    }

    logger.info('Flagged emails cleaned', { accountId, cleanedCount });

    return {
      cleanedCount,
      message: `${cleanedCount} email(s) moved to Trash`,
    };
  }

  /**
   * Get the Trash folder path for the email provider
   */
  async _getTrashFolder(client, provider) {
    // Common Trash folder names by provider
    const trashNames = {
      gmail: '[Gmail]/Trash',
      outlook: 'Deleted Items',
      yahoo: 'Trash',
    };

    if (trashNames[provider]) {
      return trashNames[provider];
    }

    // Try to find Trash folder from mailbox list
    try {
      const mailboxes = await client.list();
      for (const mailbox of mailboxes) {
        if (
          mailbox.specialUse === '\\Trash' ||
          mailbox.name.toLowerCase() === 'trash' ||
          mailbox.name.toLowerCase() === 'deleted items'
        ) {
          return mailbox.path;
        }
      }
    } catch (err) {
      logger.warn('Failed to list mailboxes for trash detection', { error: err.message });
    }

    return 'Trash'; // Fallback
  }

  /**
   * Get overall email scan statistics for a user
   */
  async getStatistics(userId) {
    const [
      totalAccounts,
      activeAccounts,
      totalScanned,
      totalFlagged,
      totalCleaned,
      spamCount,
      phishingCount,
    ] = await Promise.all([
      prisma.emailAccount.count({ where: { userId } }),
      prisma.emailAccount.count({ where: { userId, isActive: true } }),
      prisma.emailScanResult.count({ where: { userId } }),
      prisma.emailScanResult.count({ where: { userId, isFlagged: true } }),
      prisma.emailScanResult.count({ where: { userId, isCleaned: true } }),
      prisma.emailScanResult.count({ where: { userId, isSpam: true } }),
      prisma.emailScanResult.count({ where: { userId, isPhishing: true } }),
    ]);

    return {
      totalAccounts,
      activeAccounts,
      totalScanned,
      totalFlagged,
      totalCleaned,
      pendingClean: totalFlagged - totalCleaned,
      spamCount,
      phishingCount,
      flagRate: totalScanned > 0 ? ((totalFlagged / totalScanned) * 100).toFixed(2) : 0,
    };
  }

  /**
   * Get accounts that are due for auto-scan
   */
  async getAccountsDueForScan() {
    const now = new Date();

    const accounts = await prisma.emailAccount.findMany({
      where: {
        isActive: true,
        autoScanInterval: { gt: 0 },
        lastScanStatus: { not: 'scanning' },
        OR: [
          { lastScanAt: null },
          {
            lastScanAt: {
              // lastScanAt + autoScanInterval minutes < now
              lt: new Date(now.getTime()),
            },
          },
        ],
      },
    });

    // Filter accounts where enough time has passed since last scan
    return accounts.filter((account) => {
      if (!account.lastScanAt) return true;
      const intervalMs = account.autoScanInterval * 60 * 1000;
      return now.getTime() - account.lastScanAt.getTime() >= intervalMs;
    });
  }
}

module.exports = new EmailService();
