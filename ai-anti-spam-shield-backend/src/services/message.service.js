const axios = require('axios');
const config = require('../config');
const prisma = require('../config/database');
const ApiError = require('../utils/apiError');
const logger = require('../utils/logger');

/**
 * Message Service
 * Handles business logic for message operations
 */

// Detection threshold - minimum spam confidence to flag as spam
// Increased from 0.65 to 0.80 to reduce false positives
const DETECTION_THRESHOLD = 0.80;

// Minimum word count to apply spam detection
// Very short messages (greetings) are more likely to be false positives
const MIN_WORDS_FOR_SPAM_CHECK = 3;

// Common safe greeting patterns that should not be flagged as spam
const SAFE_GREETING_PATTERNS = [
  /^hi+\s*$/i,
  /^hello+\s*$/i,
  /^hey+\s*$/i,
  /^hi+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$/i,
  /^hello+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$/i,
  /^hey+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$/i,
  /^how\s+are\s+you(\s+today)?(\s+my\s+friend)?\s*[?!.]*$/i,
  /^how('s|\s+is)\s+(it\s+going|everything|life|your\s+day)\s*[?!.]*$/i,
  /^what('s|\s+is)\s+up\s*[?!.]*$/i,
  /^good\s+(morning|afternoon|evening|night)\s*[!.]*$/i,
  /^greetings?\s*[!.]*$/i,
  /^yo+\s*[!.]*$/i,
  /^sup\s*[?!.]*$/i,
  /^howdy\s*[!.]*$/i,
  /^nice\s+to\s+(meet|see)\s+you\s*[!.]*$/i,
  /^how\s+have\s+you\s+been\s*[?!.]*$/i,
  /^long\s+time\s+no\s+see\s*[!.]*$/i,
  /^(how\s+are\s+you\s+)?(doing|going)\s*(today|my\s+friend)?\s*[?!.]*$/i
];

// Safe phrase patterns that reduce spam likelihood
const SAFE_PHRASE_PATTERNS = [
  /^(hi|hello|hey)\s+how\s+are\s+you/i,
  /^how\s+are\s+you\s+(my\s+)?(friend|friends|buddy|mate)/i,
  /^(good\s+)?(morning|afternoon|evening)/i,
  /^thanks?\s*(you)?\s*(so\s+much|very\s+much)?\s*[!.]*$/i,
  /^(you're|you\s+are)\s+welcome\s*[!.]*$/i,
  /^(see|talk\s+to)\s+you\s+(later|soon|tomorrow)\s*[!.]*$/i,
  /^take\s+care\s*[!.]*$/i,
  /^have\s+a\s+(good|great|nice)\s+(day|one|evening|night)\s*[!.]*$/i
];

/**
 * Check if a message is a safe greeting or common phrase
 * @param {string} text - The message text
 * @returns {boolean} - True if it's a safe message
 */
function isSafeGreeting(text) {
  const trimmedText = text.trim();

  // Check against safe greeting patterns
  for (const pattern of SAFE_GREETING_PATTERNS) {
    if (pattern.test(trimmedText)) {
      return true;
    }
  }

  // Check against safe phrase patterns
  for (const pattern of SAFE_PHRASE_PATTERNS) {
    if (pattern.test(trimmedText)) {
      return true;
    }
  }

  return false;
}

/**
 * Check if message is too short to reliably detect spam
 * @param {string} text - The message text
 * @returns {boolean} - True if message is too short
 */
function isTooShortForSpamCheck(text) {
  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  return words.length < MIN_WORDS_FOR_SPAM_CHECK;
}

class MessageService {
  /**
   * Scan voice for spam using AI model service
   * @param {Buffer} audioBuffer - The audio file buffer
   * @param {string} filename - The audio filename
   * @param {string} userId - Optional user ID to save history
   * @returns {Promise<Object>} - Spam detection result with transcription
   */
  async scanVoiceForSpam(audioBuffer, filename, userId = null) {
    try {
      const FormData = require('form-data');
      const aiServiceUrl = `${config.ai.serviceUrl}/predict-voice`;
      
      logger.info('Calling AI voice service', { url: aiServiceUrl, filename });

      // Create form data with audio file
      const formData = new FormData();
      formData.append('audio', audioBuffer, filename);

      // Call the AI model service
      const response = await axios.post(
        aiServiceUrl,
        formData,
        {
          headers: {
            ...formData.getHeaders(),
            ...(config.ai.apiKey && { 'Authorization': `Bearer ${config.ai.apiKey}` })
          },
          timeout: 60000, // 60 second timeout for voice processing
          maxContentLength: Infinity,
          maxBodyLength: Infinity
        }
      );

      // Validate response
      if (!response.data) {
        throw ApiError.internal('AI service returned empty response');
      }

      logger.info('AI voice service response received', { 
        status: response.status,
        transcribed: response.data.transcribed_text 
      });

      /**
       * Confidence Interpretation:
       * - AI model returns "spam confidence" (how likely it's spam)
       * - High raw confidence (e.g., 0.85) = 85% likely to be SPAM
       * - Low raw confidence (e.g., 0.15) = 15% likely to be spam = 85% likely to be SAFE
       *
       * Detection Logic:
       * - If spam confidence >= DETECTION_THRESHOLD (80%) → SPAM DETECTED with that confidence
       * - If spam confidence < DETECTION_THRESHOLD → SAFE with (1 - spam_confidence) as safety confidence
       */
      let rawSpamConfidence = response.data.confidence || response.data.probability || 0;

      // Check if transcribed text is a safe greeting
      const transcribedText = response.data.transcribed_text || '';
      if (isSafeGreeting(transcribedText)) {
        logger.info('Voice transcription detected as safe greeting', {
          text: transcribedText.substring(0, 50)
        });
        rawSpamConfidence = Math.min(rawSpamConfidence, 0.20); // Cap at 20%
      }

      // Apply short message penalty for voice transcripts too
      if (isTooShortForSpamCheck(transcribedText) && rawSpamConfidence < 0.90) {
        logger.info('Applying short message penalty to voice spam confidence', {
          original: rawSpamConfidence,
          wordCount: transcribedText.trim().split(/\s+/).length
        });
        rawSpamConfidence = rawSpamConfidence * 0.6;
      }

      // Determine if it's spam based on the spam confidence
      const isSpam = rawSpamConfidence >= DETECTION_THRESHOLD;

      // Calculate display confidence:
      // - If spam: show spam confidence (e.g., 85% spam)
      // - If safe: show safety confidence (e.g., 1 - 0.15 = 85% safe)
      const displayConfidence = isSpam
        ? rawSpamConfidence
        : (1 - rawSpamConfidence);

      // Generate detailed danger causes based on analysis
      const dangerCauses = [];
      if (isSpam) {
        dangerCauses.push({
          type: 'spam_detected',
          title: 'Spam Detected',
          description: `Our AI detected this as spam with ${(rawSpamConfidence * 100).toFixed(1)}% confidence. This exceeds our ${(DETECTION_THRESHOLD * 100).toFixed(0)}% threshold for spam detection.`,
          severity: rawSpamConfidence >= 0.90 ? 'critical' : rawSpamConfidence >= 0.85 ? 'high' : 'medium'
        });

        if (rawSpamConfidence >= 0.90) {
          dangerCauses.push({
            type: 'high_spam_confidence',
            title: 'Very High Spam Probability',
            description: 'The AI is highly confident this is spam. This voice message contains multiple strong indicators of spam or scam content.',
            severity: 'critical'
          });
        }

        if (rawSpamConfidence >= 0.80 && rawSpamConfidence < 0.90) {
          dangerCauses.push({
            type: 'moderate_spam_confidence',
            title: 'Moderate Spam Probability',
            description: 'The message shows significant spam characteristics. While not all indicators are present, there are enough suspicious elements.',
            severity: 'high'
          });
        }

        // Add causes based on features if available
        if (response.data.details?.features) {
          const features = response.data.details.features;
          if (features.has_url) {
            dangerCauses.push({
              type: 'contains_url',
              title: 'Contains External Links',
              description: 'This voice message mentions URLs or web links. Be cautious about clicking unknown links as they may lead to phishing sites.',
              severity: 'medium'
            });
          }
          if (features.urgency_words) {
            dangerCauses.push({
              type: 'urgency_language',
              title: 'Urgency Tactics Detected',
              description: 'The message uses urgent language like "act now", "limited time", or "immediately". Scammers often use urgency to pressure victims into quick decisions.',
              severity: 'high'
            });
          }
          if (features.spam_keywords) {
            dangerCauses.push({
              type: 'spam_keywords',
              title: 'Spam Keywords Detected',
              description: 'Common spam keywords were found such as "win", "prize", "free", "congratulations", or "selected". These are typical in lottery and prize scams.',
              severity: 'high'
            });
          }
          if (features.currency_symbols) {
            dangerCauses.push({
              type: 'money_reference',
              title: 'Money References Detected',
              description: 'The message contains currency symbols or money amounts. Be wary of unsolicited messages discussing money or financial rewards.',
              severity: 'medium'
            });
          }
          if (features.has_phone) {
            dangerCauses.push({
              type: 'phone_number',
              title: 'Phone Number Detected',
              description: 'The message contains phone numbers. Scammers often include callback numbers to premium rate lines or to collect personal information.',
              severity: 'medium'
            });
          }
        }
      }

      const result = {
        is_spam: isSpam,
        confidence: displayConfidence,
        raw_spam_confidence: rawSpamConfidence,
        prediction: isSpam ? 'spam' : 'ham',
        message: response.data.transcribed_text,
        transcribed_text: response.data.transcribed_text,
        timestamp: new Date().toISOString(),
        is_safe: !isSpam,
        detection_threshold: DETECTION_THRESHOLD,
        danger_causes: dangerCauses,
        risk_level: isSpam
          ? (rawSpamConfidence >= 0.90 ? 'CRITICAL' : rawSpamConfidence >= 0.85 ? 'HIGH' : 'MEDIUM')
          : 'NONE',
        confidence_label: isSpam ? 'Spam Confidence' : 'Safety Confidence',
        ...(response.data.details && { details: { ...response.data.details, danger_causes: dangerCauses } })
      };

      // Save to history if user is authenticated (with 'voice' scan type)
      if (userId) {
        await this.saveScanHistory(userId, response.data.transcribed_text, result, 'voice');
      }

      return result;

    } catch (error) {
      // Handle different types of errors
      if (error.isOperational) {
        throw error;
      }

      if (error.code === 'ECONNREFUSED') {
        logger.error('AI service connection refused', {
          url: config.ai.serviceUrl
        });
        throw ApiError.internal('AI service is unavailable. Please try again later.');
      }

      if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
        logger.error('AI service timeout', { error: error.message });
        throw ApiError.internal('AI service request timed out. Please try again.');
      }

      if (error.response) {
        logger.error('AI service error response', {
          status: error.response.status,
          data: error.response.data
        });

        const statusCode = error.response.status;
        const errorMessage = error.response.data?.detail ||
                           error.response.data?.message ||
                           error.response.data?.error ||
                           'AI service error';

        if (statusCode === 400) {
          throw ApiError.badRequest(`AI service error: ${errorMessage}`);
        } else if (statusCode === 503) {
          throw ApiError.internal('AI service is temporarily unavailable');
        } else {
          throw ApiError.internal(`AI service error: ${errorMessage}`);
        }
      }

      logger.error('Unknown error calling AI voice service', {
        error: error.message,
        stack: error.stack
      });
      throw ApiError.internal('Failed to analyze voice message. Please try again.');
    }
  }

  /**
   * Scan text for spam using AI model service
   * @param {string} messageText - The message text to scan
   * @param {string} userId - Optional user ID to save history
   * @returns {Promise<Object>} - Spam detection result
   */
  async scanTextForSpam(messageText, userId = null) {
    try {
      // First, check if this is a safe greeting or common phrase
      // This prevents false positives on friendly messages like "Hi how are you"
      if (isSafeGreeting(messageText)) {
        logger.info('Message detected as safe greeting, skipping spam check', {
          message: messageText.substring(0, 50)
        });

        const result = {
          is_spam: false,
          confidence: 0.95, // High confidence it's safe
          raw_spam_confidence: 0.05,
          prediction: 'ham',
          message: messageText,
          timestamp: new Date().toISOString(),
          is_safe: true,
          detection_threshold: DETECTION_THRESHOLD,
          danger_causes: [],
          risk_level: 'NONE',
          confidence_label: 'Safety Confidence',
          details: {
            features: { is_greeting: true },
            bypass_reason: 'safe_greeting_pattern'
          }
        };

        if (userId) {
          await this.saveScanHistory(userId, messageText, result);
        }

        return result;
      }

      // Check if message is too short to reliably detect spam
      const tooShort = isTooShortForSpamCheck(messageText);

      const aiServiceUrl = `${config.ai.serviceUrl}/predict`;

      logger.info('Calling AI service', { url: aiServiceUrl });

      // Call the AI model service
      const response = await axios.post(
        aiServiceUrl,
        { message: messageText },
        {
          headers: {
            'Content-Type': 'application/json',
            ...(config.ai.apiKey && { 'Authorization': `Bearer ${config.ai.apiKey}` })
          },
          timeout: 30000 // 30 second timeout
        }
      );

      // Validate response
      if (!response.data) {
        throw ApiError.internal('AI service returned empty response');
      }

      logger.info('AI service response received', {
        status: response.status
      });

      /**
       * Confidence Interpretation:
       * - AI model returns "spam confidence" (how likely it's spam)
       * - High raw confidence (e.g., 0.85) = 85% likely to be SPAM
       * - Low raw confidence (e.g., 0.15) = 15% likely to be spam = 85% likely to be SAFE
       *
       * Detection Logic:
       * - If spam confidence >= DETECTION_THRESHOLD (80%) → SPAM DETECTED with that confidence
       * - If spam confidence < DETECTION_THRESHOLD → SAFE with (1 - spam_confidence) as safety confidence
       * - For very short messages, apply additional leniency
       */
      let rawSpamConfidence = response.data.confidence || response.data.probability || 0;

      // For very short messages, reduce spam confidence to avoid false positives
      // Short casual messages are often flagged incorrectly
      if (tooShort && rawSpamConfidence < 0.90) {
        logger.info('Applying short message penalty to spam confidence', {
          original: rawSpamConfidence,
          wordCount: messageText.trim().split(/\s+/).length
        });
        rawSpamConfidence = rawSpamConfidence * 0.6; // Reduce confidence by 40%
      }

      // Determine if it's spam based on the spam confidence
      const isSpam = rawSpamConfidence >= DETECTION_THRESHOLD;

      // Calculate display confidence:
      // - If spam: show spam confidence (e.g., 85% spam)
      // - If safe: show safety confidence (e.g., 1 - 0.15 = 85% safe)
      const displayConfidence = isSpam
        ? rawSpamConfidence
        : (1 - rawSpamConfidence);

      // Generate detailed danger causes based on analysis
      const dangerCauses = [];
      if (isSpam) {
        dangerCauses.push({
          type: 'spam_detected',
          title: 'Spam Detected',
          description: `Our AI detected this as spam with ${(rawSpamConfidence * 100).toFixed(1)}% confidence. This exceeds our ${(DETECTION_THRESHOLD * 100).toFixed(0)}% threshold for spam detection.`,
          severity: rawSpamConfidence >= 0.90 ? 'critical' : rawSpamConfidence >= 0.85 ? 'high' : 'medium'
        });

        if (rawSpamConfidence >= 0.90) {
          dangerCauses.push({
            type: 'high_spam_confidence',
            title: 'Very High Spam Probability',
            description: 'The AI is highly confident this is spam. This message contains multiple strong indicators of spam or scam content.',
            severity: 'critical'
          });
        }

        if (rawSpamConfidence >= 0.80 && rawSpamConfidence < 0.90) {
          dangerCauses.push({
            type: 'moderate_spam_confidence',
            title: 'Moderate Spam Probability',
            description: 'The message shows significant spam characteristics. While not all indicators are present, there are enough suspicious elements.',
            severity: 'high'
          });
        }

        // Add causes based on features if available
        if (response.data.details?.features) {
          const features = response.data.details.features;
          if (features.has_url) {
            dangerCauses.push({
              type: 'contains_url',
              title: 'Contains External Links',
              description: 'This message contains URLs or web links. Be cautious about clicking unknown links as they may lead to phishing sites or download malware.',
              severity: 'medium'
            });
          }
          if (features.has_email) {
            dangerCauses.push({
              type: 'contains_email',
              title: 'Contains Email Address',
              description: 'The message contains email addresses. Scammers often include fake contact emails to collect personal information or send follow-up scams.',
              severity: 'low'
            });
          }
          if (features.urgency_words) {
            dangerCauses.push({
              type: 'urgency_language',
              title: 'Urgency Tactics Detected',
              description: 'The message uses urgent language like "act now", "limited time", "expire", or "immediately". Scammers use urgency to pressure victims into making hasty decisions without thinking.',
              severity: 'high'
            });
          }
          if (features.spam_keywords) {
            dangerCauses.push({
              type: 'spam_keywords',
              title: 'Spam Keywords Detected',
              description: 'Common spam keywords were found such as "win", "prize", "free", "congratulations", "selected", or "lottery". These are typical indicators of lottery scams, fake prize notifications, or promotional spam.',
              severity: 'high'
            });
          }
          if (features.currency_symbols) {
            dangerCauses.push({
              type: 'money_reference',
              title: 'Money References Detected',
              description: 'The message contains currency symbols or money amounts. Be extremely wary of unsolicited messages discussing money, financial rewards, or requesting payments.',
              severity: 'medium'
            });
          }
          if (features.has_phone) {
            dangerCauses.push({
              type: 'phone_number',
              title: 'Phone Number Detected',
              description: 'The message contains phone numbers. Scammers often include callback numbers that may be premium rate lines or used to collect your personal information through social engineering.',
              severity: 'medium'
            });
          }
        }
      }

      const result = {
        is_spam: isSpam,
        confidence: displayConfidence,
        raw_spam_confidence: rawSpamConfidence,
        prediction: isSpam ? 'spam' : 'ham',
        message: messageText,
        timestamp: new Date().toISOString(),
        is_safe: !isSpam,
        detection_threshold: DETECTION_THRESHOLD,
        danger_causes: dangerCauses,
        risk_level: isSpam
          ? (rawSpamConfidence >= 0.90 ? 'CRITICAL' : rawSpamConfidence >= 0.85 ? 'HIGH' : 'MEDIUM')
          : 'NONE',
        confidence_label: isSpam ? 'Spam Confidence' : 'Safety Confidence',
        ...(response.data.details && { details: { ...response.data.details, danger_causes: dangerCauses } }),
        ...(tooShort && { short_message_penalty_applied: true })
      };

      // Save to history if user is authenticated
      if (userId) {
        await this.saveScanHistory(userId, messageText, result);
      }

      return result;

    } catch (error) {
      // Handle different types of errors
      if (error.isOperational) {
        throw error;
      }

      if (error.code === 'ECONNREFUSED') {
        logger.error('AI service connection refused', { 
          url: config.ai.serviceUrl 
        });
        throw ApiError.internal('AI service is unavailable. Please try again later.');
      }

      if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
        logger.error('AI service timeout', { error: error.message });
        throw ApiError.internal('AI service request timed out. Please try again.');
      }

      if (error.response) {
        logger.error('AI service error response', { 
          status: error.response.status,
          data: error.response.data 
        });

        const statusCode = error.response.status;
        const errorMessage = error.response.data?.message || 
                           error.response.data?.error || 
                           'AI service error';

        if (statusCode === 400) {
          throw ApiError.badRequest(`AI service error: ${errorMessage}`);
        } else if (statusCode === 503) {
          throw ApiError.internal('AI service is temporarily unavailable');
        } else {
          throw ApiError.internal(`AI service error: ${errorMessage}`);
        }
      }

      logger.error('Unknown error calling AI service', { 
        error: error.message,
        stack: error.stack 
      });
      throw ApiError.internal('Failed to analyze message. Please try again.');
    }
  }

  /**
   * Save scan history to database
   * @param {string} userId - User ID
   * @param {string} message - Message content
   * @param {Object} scanResult - Scan result
   * @param {string} scanType - Type of scan: 'text' or 'voice'
   */
  async saveScanHistory(userId, message, scanResult, scanType = 'text') {
    try {
      // Stringify details if it's an object (Prisma schema expects String)
      const detailsStr = scanResult.details
        ? (typeof scanResult.details === 'string'
            ? scanResult.details
            : JSON.stringify(scanResult.details))
        : null;

      const history = await prisma.scanHistory.create({
        data: {
          userId,
          message,
          isSpam: scanResult.is_spam,
          confidence: scanResult.confidence,
          prediction: scanResult.prediction,
          details: detailsStr,
          scanType
        }
      });

      logger.info('Scan history saved', { historyId: history.id, userId, scanType });

      return history;
    } catch (error) {
      logger.error('Failed to save scan history', { error: error.message });
      // Don't throw error, just log it - history save shouldn't fail the scan
    }
  }

  /**
   * Get scan history for user
   */
  async getScanHistory(userId, filters = {}) {
    const { page = 1, limit = 20, isSpam } = filters;
    const skip = (page - 1) * limit;

    const where = {
      userId,
      ...(isSpam !== undefined && { isSpam: isSpam === 'true' || isSpam === true })
    };

    const [histories, total] = await Promise.all([
      prisma.scanHistory.findMany({
        where,
        orderBy: { scannedAt: 'desc' },
        skip,
        take: parseInt(limit)
      }),
      prisma.scanHistory.count({ where })
    ]);

    return {
      histories,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit)
      }
    };
  }

  /**
   * Get scan history by ID
   */
  async getScanHistoryById(id, userId) {
    const history = await prisma.scanHistory.findFirst({
      where: {
        id,
        userId
      }
    });

    if (!history) {
      throw ApiError.notFound('Scan history not found');
    }

    return history;
  }

  /**
   * Delete scan history
   */
  async deleteScanHistory(id, userId) {
    const history = await prisma.scanHistory.findFirst({
      where: {
        id,
        userId
      }
    });

    if (!history) {
      throw ApiError.notFound('Scan history not found');
    }

    await prisma.scanHistory.delete({
      where: { id }
    });

    logger.info('Scan history deleted', { historyId: id, userId });

    return { message: 'Scan history deleted successfully' };
  }

  /**
   * Get scan statistics for user
   */
  async getScanStatistics(userId) {
    const [totalScans, spamCount, hamCount, voiceScans, textScans] = await Promise.all([
      prisma.scanHistory.count({ where: { userId } }),
      prisma.scanHistory.count({ where: { userId, isSpam: true } }),
      prisma.scanHistory.count({ where: { userId, isSpam: false } }),
      prisma.scanHistory.count({ where: { userId, scanType: 'voice' } }),
      prisma.scanHistory.count({ where: { userId, scanType: 'text' } })
    ]);

    return {
      totalScans,
      spamCount,
      spamDetected: spamCount,  // Alias for mobile app
      hamCount,
      safeMessages: hamCount,   // Alias for mobile app
      voiceScans,
      textScans,
      spamPercentage: totalScans > 0 ? ((spamCount / totalScans) * 100).toFixed(2) : 0
    };
  }

  /**
   * Analyze a message for spam
   */
  async analyzeMessage(messageData) {
    // TODO: Implement message analysis logic
    throw new Error('Not implemented');
  }

  /**
   * Get all messages
   */
  async getAllMessages(filters = {}) {
    // TODO: Implement get all messages logic
    throw new Error('Not implemented');
  }

  /**
   * Get message by ID
   */
  async getMessageById(id) {
    // TODO: Implement get message by ID logic
    throw new Error('Not implemented');
  }

  /**
   * Delete message
   */
  async deleteMessage(id) {
    // TODO: Implement delete message logic
    throw new Error('Not implemented');
  }

  /**
   * Call AI service for spam detection
   */
  async callAIService(messageContent) {
    // TODO: Implement AI service integration
    throw new Error('Not implemented');
  }
}

module.exports = new MessageService();

