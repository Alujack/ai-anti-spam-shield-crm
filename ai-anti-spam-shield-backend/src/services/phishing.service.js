const axios = require('axios');
const config = require('../config');
const prisma = require('../config/database');
const ApiError = require('../utils/apiError');
const logger = require('../utils/logger');

/**
 * Phishing Detection Service
 * Handles phishing detection requests and history management
 */
class PhishingService {
  constructor() {
    this.aiServiceUrl = config.ai.serviceUrl;
    this.timeout = 30000; // 30 second timeout
  }

  /**
   * Scan text for phishing
   * @param {string} text - Text to analyze
   * @param {string} scanType - Type of scan (email, sms, url, auto)
   * @param {string|null} userId - User ID for history tracking (optional)
   * @returns {Promise<Object>} Phishing detection result
   */
  async scanTextForPhishing(text, scanType = 'auto', userId = null) {
    try {
      logger.info('Scanning text for phishing', {
        textLength: text?.length,
        scanType,
        hasUser: !!userId
      });

      const response = await axios.post(
        `${this.aiServiceUrl}/predict-phishing`,
        { text, scan_type: scanType },
        {
          timeout: this.timeout,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      /**
       * Confidence Interpretation:
       * - AI model returns "phishing confidence" (how likely it's phishing)
       * - High raw confidence (e.g., 0.85) = 85% likely to be PHISHING
       * - Low raw confidence (e.g., 0.15) = 15% likely to be phishing = 85% likely to be SAFE
       *
       * Detection Logic:
       * - If phishing confidence >= 0.65 (65%) → PHISHING DETECTED with that confidence
       * - If phishing confidence < 0.65 → SAFE with (1 - phishing_confidence) as safety confidence
       */
      const DETECTION_THRESHOLD = 0.65;
      const rawPhishingConfidence = response.data.confidence || 0;

      // Determine if it's phishing based on the phishing confidence
      const isPhishing = rawPhishingConfidence >= DETECTION_THRESHOLD;

      // Calculate display confidence:
      // - If phishing: show phishing confidence (e.g., 85% phishing)
      // - If safe: show safety confidence (e.g., 1 - 0.15 = 85% safe)
      const displayConfidence = isPhishing
        ? rawPhishingConfidence
        : (1 - rawPhishingConfidence);

      // Generate detailed danger causes for phishing analysis
      const dangerCauses = [];
      if (isPhishing) {
        dangerCauses.push({
          type: 'phishing_detected',
          title: 'Phishing Detected',
          description: `Our AI detected this as a phishing attempt with ${(rawPhishingConfidence * 100).toFixed(1)}% confidence. This exceeds our ${(DETECTION_THRESHOLD * 100)}% threshold for phishing detection.`,
          severity: rawPhishingConfidence >= 0.85 ? 'critical' : rawPhishingConfidence >= 0.75 ? 'high' : 'medium'
        });

        if (rawPhishingConfidence >= 0.85) {
          dangerCauses.push({
            type: 'high_phishing_confidence',
            title: 'Very High Phishing Probability',
            description: 'The AI is highly confident this is a phishing attempt. This message contains multiple strong indicators of malicious intent. Do NOT interact with any links or provide any personal information.',
            severity: 'critical'
          });
        }

        if (rawPhishingConfidence >= 0.65 && rawPhishingConfidence < 0.85) {
          dangerCauses.push({
            type: 'moderate_phishing_confidence',
            title: 'Moderate Phishing Probability',
            description: 'The message shows significant phishing characteristics. While not all indicators are present, there are enough suspicious elements to warrant caution.',
            severity: 'high'
          });
        }

        // Add causes based on indicators
        const indicators = response.data.indicators || [];
        if (indicators.length > 0) {
          indicators.forEach((indicator, index) => {
            if (index < 5) {
              dangerCauses.push({
                type: 'indicator',
                title: `Suspicious Pattern #${index + 1}`,
                description: indicator,
                severity: 'medium'
              });
            }
          });
        }

        // Add causes based on brand impersonation
        if (response.data.brand_impersonation?.detected) {
          dangerCauses.push({
            type: 'brand_impersonation',
            title: 'Brand Impersonation Detected',
            description: `This message appears to be impersonating ${response.data.brand_impersonation.brand || 'a known brand'}. Legitimate companies do not ask for sensitive information via unsolicited messages.`,
            severity: 'critical'
          });
        }

        // Add causes based on URL analysis
        const urlsAnalyzed = response.data.urls_analyzed || [];
        const suspiciousUrls = urlsAnalyzed.filter(u => u.is_suspicious || u.isSuspicious);
        if (suspiciousUrls.length > 0) {
          dangerCauses.push({
            type: 'suspicious_urls',
            title: `${suspiciousUrls.length} Suspicious URL(s) Detected`,
            description: 'The message contains links that show characteristics of phishing sites, including suspicious domains, misleading paths, or known malicious patterns.',
            severity: 'critical'
          });
        }
      }

      // Determine threat level based on phishing confidence
      const calculatedThreatLevel = isPhishing
        ? (rawPhishingConfidence >= 0.85 ? 'CRITICAL' : rawPhishingConfidence >= 0.75 ? 'HIGH' : 'MEDIUM')
        : 'NONE';

      // Generate recommendation based on danger level
      const recommendation = isPhishing
        ? rawPhishingConfidence >= 0.85
          ? 'DANGER: This message is highly likely to be a phishing attempt. Do NOT click any links, do NOT reply, and do NOT provide any personal information. Delete this message immediately and block the sender.'
          : rawPhishingConfidence >= 0.75
            ? 'WARNING: This message shows significant signs of being a phishing attempt. Do not interact with any links or requests for information. Verify the sender through official channels before taking any action.'
            : 'CAUTION: This message has suspicious characteristics that suggest phishing. Be careful with any links or requests. When in doubt, contact the supposed sender through official channels to verify.'
        : response.data.recommendation || 'This message appears to be safe. However, always remain vigilant and never share sensitive information unless you are certain of the recipient\'s identity.';

      const result = {
        isPhishing: isPhishing,
        confidence: displayConfidence,
        raw_phishing_confidence: rawPhishingConfidence,
        phishingType: response.data.phishing_type || (isPhishing ? scanType.toUpperCase() : 'NONE'),
        threatLevel: calculatedThreatLevel,
        indicators: response.data.indicators || [],
        urlsAnalyzed: response.data.urls_analyzed || [],
        brandImpersonation: response.data.brand_impersonation,
        recommendation: recommendation,
        details: { ...(response.data.details || {}), danger_causes: dangerCauses },
        timestamp: response.data.timestamp || new Date().toISOString(),
        is_safe: !isPhishing,
        detection_threshold: DETECTION_THRESHOLD,
        danger_causes: dangerCauses,
        risk_level: calculatedThreatLevel,
        confidence_label: isPhishing ? 'Phishing Confidence' : 'Safety Confidence'
      };

      // Save to history if user is authenticated
      if (userId) {
        await this.savePhishingScanHistory(userId, text, result);
      }

      return result;
    } catch (error) {
      logger.error('Phishing scan failed', { error: error.message });

      if (error.code === 'ECONNREFUSED') {
        throw ApiError.internal('AI service unavailable');
      }
      if (error.response?.status === 503) {
        throw ApiError.internal('Phishing detector not available');
      }

      throw ApiError.internal('Failed to scan for phishing');
    }
  }

  /**
   * Scan URL for phishing
   * @param {string} url - URL to analyze
   * @param {string|null} userId - User ID for history tracking (optional)
   * @returns {Promise<Object>} URL phishing analysis result
   */
  async scanUrlForPhishing(url, userId = null) {
    try {
      logger.info('Scanning URL for phishing', { url: url?.substring(0, 50) });

      const response = await axios.post(
        `${this.aiServiceUrl}/scan-url`,
        { url },
        {
          timeout: this.timeout,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      /**
       * Confidence Interpretation:
       * - AI model returns "phishing confidence" (how likely it's phishing)
       * - High raw confidence (e.g., 0.85) = 85% likely to be PHISHING URL
       * - Low raw confidence (e.g., 0.15) = 15% likely to be phishing = 85% likely to be SAFE URL
       *
       * Detection Logic:
       * - If phishing confidence >= 0.65 (65%) → PHISHING URL DETECTED with that confidence
       * - If phishing confidence < 0.65 → SAFE URL with (1 - phishing_confidence) as safety confidence
       */
      const DETECTION_THRESHOLD = 0.65;
      const rawPhishingConfidence = response.data.confidence || 0;

      // Determine if it's phishing based on the phishing confidence
      const isPhishing = rawPhishingConfidence >= DETECTION_THRESHOLD;

      // Calculate display confidence:
      // - If phishing: show phishing confidence (e.g., 85% phishing)
      // - If safe: show safety confidence (e.g., 1 - 0.15 = 85% safe)
      const displayConfidence = isPhishing
        ? rawPhishingConfidence
        : (1 - rawPhishingConfidence);

      // Generate detailed danger causes for URL phishing analysis
      const dangerCauses = [];
      if (isPhishing) {
        dangerCauses.push({
          type: 'phishing_url_detected',
          title: 'Phishing URL Detected',
          description: `Our AI detected this as a phishing URL with ${(rawPhishingConfidence * 100).toFixed(1)}% confidence. This exceeds our ${(DETECTION_THRESHOLD * 100)}% threshold for phishing detection.`,
          severity: rawPhishingConfidence >= 0.85 ? 'critical' : rawPhishingConfidence >= 0.75 ? 'high' : 'medium'
        });

        if (rawPhishingConfidence >= 0.85) {
          dangerCauses.push({
            type: 'high_phishing_confidence',
            title: 'Very High Phishing URL Risk',
            description: 'This URL shows extremely strong characteristics of a phishing site. Do NOT visit this link or enter any personal information. It may steal your credentials or install malware.',
            severity: 'critical'
          });
        }

        if (rawPhishingConfidence >= 0.65 && rawPhishingConfidence < 0.85) {
          dangerCauses.push({
            type: 'moderate_phishing_confidence',
            title: 'Moderate Phishing URL Risk',
            description: 'The URL has several characteristics common in phishing attempts. The domain may be recently registered or mimic a legitimate site.',
            severity: 'high'
          });
        }

        // Add causes based on indicators
        const indicators = response.data.indicators || [];
        if (indicators.length > 0) {
          indicators.forEach((indicator, index) => {
            if (index < 5) {
              dangerCauses.push({
                type: 'indicator',
                title: `URL Warning #${index + 1}`,
                description: indicator,
                severity: 'medium'
              });
            }
          });
        }

        // Analyze URL structure for common phishing patterns
        try {
          const urlObj = new URL(url);

          // Check for suspicious domain patterns
          if (urlObj.hostname.includes('-') && urlObj.hostname.split('-').length > 2) {
            dangerCauses.push({
              type: 'suspicious_domain',
              title: 'Suspicious Domain Pattern',
              description: 'The domain contains multiple hyphens, which is a common technique used to create fake domains that mimic legitimate brands.',
              severity: 'high'
            });
          }

          // Check for IP address instead of domain
          if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(urlObj.hostname)) {
            dangerCauses.push({
              type: 'ip_address_url',
              title: 'IP Address URL',
              description: 'This URL uses an IP address instead of a domain name. Legitimate websites rarely use IP addresses directly. This is a major red flag for phishing.',
              severity: 'critical'
            });
          }

          // Check for suspicious TLDs
          const suspiciousTLDs = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', '.click'];
          if (suspiciousTLDs.some(tld => urlObj.hostname.endsWith(tld))) {
            dangerCauses.push({
              type: 'suspicious_tld',
              title: 'Suspicious Domain Extension',
              description: 'This URL uses a domain extension commonly associated with malicious websites and phishing attempts.',
              severity: 'high'
            });
          }

          // Check for brand name in subdomain (potential spoofing)
          const knownBrands = ['paypal', 'amazon', 'google', 'microsoft', 'apple', 'facebook', 'netflix', 'bank'];
          const hasSpoof = knownBrands.some(brand =>
            urlObj.hostname.includes(brand) && !urlObj.hostname.endsWith(`${brand}.com`)
          );
          if (hasSpoof) {
            dangerCauses.push({
              type: 'brand_spoofing',
              title: 'Potential Brand Impersonation',
              description: 'This URL contains a well-known brand name but is not the official domain. This is a common phishing technique to trick users into thinking they are on a legitimate site.',
              severity: 'critical'
            });
          }
        } catch (e) {
          // Invalid URL format
          dangerCauses.push({
            type: 'invalid_url',
            title: 'Malformed URL',
            description: 'The URL structure is invalid or malformed, which can indicate an attempt to exploit browser vulnerabilities.',
            severity: 'high'
          });
        }

        // Add causes based on brand impersonation
        if (response.data.brand_impersonation?.detected) {
          dangerCauses.push({
            type: 'brand_impersonation',
            title: 'Brand Impersonation Confirmed',
            description: `This URL is attempting to impersonate ${response.data.brand_impersonation.brand || 'a known brand'}. Do NOT enter any credentials or personal information.`,
            severity: 'critical'
          });
        }
      }

      // Determine threat level based on phishing confidence
      const calculatedThreatLevel = isPhishing
        ? (rawPhishingConfidence >= 0.85 ? 'CRITICAL' : rawPhishingConfidence >= 0.75 ? 'HIGH' : 'MEDIUM')
        : 'NONE';

      // Generate recommendation based on danger level
      const recommendation = isPhishing
        ? rawPhishingConfidence >= 0.85
          ? 'DANGER: This URL is highly likely to be a phishing site. Do NOT visit this link under any circumstances. Do NOT enter any login credentials or personal information. Report this URL as phishing.'
          : rawPhishingConfidence >= 0.75
            ? 'WARNING: This URL shows significant signs of being malicious. Do not visit unless you can verify the legitimacy through official channels. Never enter credentials on suspicious sites.'
            : 'CAUTION: This URL has suspicious characteristics that suggest phishing. If you must visit, ensure you do not enter any sensitive information. Verify the site\'s authenticity before proceeding.'
        : response.data.recommendation || 'This URL appears to be safe. However, always verify you are on the correct domain before entering sensitive information.';

      const result = {
        isPhishing: isPhishing,
        confidence: displayConfidence,
        raw_phishing_confidence: rawPhishingConfidence,
        phishingType: response.data.phishing_type || (isPhishing ? 'URL' : 'NONE'),
        threatLevel: calculatedThreatLevel,
        indicators: response.data.indicators || [],
        urlsAnalyzed: response.data.urls_analyzed || [],
        brandImpersonation: response.data.brand_impersonation,
        recommendation: recommendation,
        details: { ...(response.data.details || {}), danger_causes: dangerCauses },
        timestamp: response.data.timestamp || new Date().toISOString(),
        is_safe: !isPhishing,
        detection_threshold: DETECTION_THRESHOLD,
        danger_causes: dangerCauses,
        risk_level: calculatedThreatLevel,
        confidence_label: isPhishing ? 'Phishing Confidence' : 'Safety Confidence'
      };

      // Save to history if user is authenticated
      if (userId) {
        await this.savePhishingScanHistory(userId, url, result, url);
      }

      return result;
    } catch (error) {
      logger.error('URL phishing scan failed', { error: error.message });
      throw ApiError.internal('Failed to scan URL for phishing');
    }
  }

  /**
   * Batch scan multiple items for phishing
   * @param {string[]} items - Array of texts/URLs to scan
   * @param {string} scanType - Type of scan for all items
   * @param {string|null} userId - User ID for history tracking (optional)
   * @returns {Promise<Object>} Batch scan results with summary
   */
  async batchScanForPhishing(items, scanType = 'auto', userId = null) {
    try {
      logger.info('Batch scanning for phishing', {
        itemCount: items?.length,
        scanType
      });

      const response = await axios.post(
        `${this.aiServiceUrl}/batch-phishing`,
        { items, scan_type: scanType },
        {
          timeout: this.timeout * 2, // Double timeout for batch
          headers: { 'Content-Type': 'application/json' }
        }
      );

      return {
        results: response.data.results,
        summary: response.data.summary,
        timestamp: response.data.timestamp || new Date().toISOString()
      };
    } catch (error) {
      logger.error('Batch phishing scan failed', { error: error.message });
      throw ApiError.internal('Failed to perform batch phishing scan');
    }
  }

  /**
   * Save phishing scan to history
   * @param {string} userId - User ID
   * @param {string} inputText - Original input text
   * @param {Object} result - Scan result
   * @param {string|null} inputUrl - Specific URL if applicable
   */
  async savePhishingScanHistory(userId, inputText, result, inputUrl = null) {
    try {
      await prisma.phishingScanHistory.create({
        data: {
          userId,
          inputText: inputText.substring(0, 10000), // Limit text length
          inputUrl,
          isPhishing: result.isPhishing,
          confidence: result.confidence,
          phishingType: result.phishingType,
          threatLevel: result.threatLevel,
          indicators: JSON.stringify(result.indicators),
          urlsAnalyzed: result.urlsAnalyzed ? JSON.stringify(result.urlsAnalyzed) : null,
          brandDetected: result.brandImpersonation?.brand || null,
        }
      });

      logger.info('Phishing scan history saved', { userId });
    } catch (error) {
      // Non-blocking - don't fail the scan if history save fails
      logger.error('Failed to save phishing history', { error: error.message });
    }
  }

  /**
   * Get user's phishing scan history
   * @param {string} userId - User ID
   * @param {Object} filters - Filter options
   * @returns {Promise<Object>} Paginated history
   */
  async getPhishingScanHistory(userId, filters = {}) {
    const { page = 1, limit = 20, phishingOnly = null, threatLevel = null } = filters;
    const skip = (page - 1) * limit;

    try {
      const where = { userId };

      if (phishingOnly !== null) {
        where.isPhishing = phishingOnly === 'true' || phishingOnly === true;
      }

      if (threatLevel) {
        where.threatLevel = threatLevel.toUpperCase();
      }

      const [histories, total] = await Promise.all([
        prisma.phishingScanHistory.findMany({
          where,
          orderBy: { scannedAt: 'desc' },
          skip,
          take: limit,
          select: {
            id: true,
            inputText: true,
            inputUrl: true,
            isPhishing: true,
            confidence: true,
            phishingType: true,
            threatLevel: true,
            indicators: true,
            brandDetected: true,
            scannedAt: true,
          }
        }),
        prisma.phishingScanHistory.count({ where })
      ]);

      // Parse JSON fields
      const parsedHistories = histories.map(h => ({
        ...h,
        indicators: h.indicators ? JSON.parse(h.indicators) : [],
        inputText: h.inputText.substring(0, 200) + (h.inputText.length > 200 ? '...' : '')
      }));

      return {
        histories: parsedHistories,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
          hasMore: skip + histories.length < total
        }
      };
    } catch (error) {
      logger.error('Failed to get phishing history', { error: error.message });
      throw ApiError.internal('Failed to retrieve phishing history');
    }
  }

  /**
   * Get specific phishing scan by ID
   * @param {string} id - Scan ID
   * @param {string} userId - User ID
   * @returns {Promise<Object>} Scan details
   */
  async getPhishingScanById(id, userId) {
    try {
      const scan = await prisma.phishingScanHistory.findFirst({
        where: { id, userId },
      });

      if (!scan) {
        throw ApiError.notFound('Phishing scan not found');
      }

      return {
        ...scan,
        indicators: scan.indicators ? JSON.parse(scan.indicators) : [],
        urlsAnalyzed: scan.urlsAnalyzed ? JSON.parse(scan.urlsAnalyzed) : [],
      };
    } catch (error) {
      if (error.isOperational) throw error;
      logger.error('Failed to get phishing scan', { error: error.message });
      throw ApiError.internal('Failed to retrieve phishing scan');
    }
  }

  /**
   * Delete phishing scan from history
   * @param {string} id - Scan ID
   * @param {string} userId - User ID
   */
  async deletePhishingScan(id, userId) {
    try {
      const scan = await prisma.phishingScanHistory.findFirst({
        where: { id, userId }
      });

      if (!scan) {
        throw ApiError.notFound('Phishing scan not found');
      }

      await prisma.phishingScanHistory.delete({
        where: { id }
      });

      logger.info('Phishing scan deleted', { id, userId });
      return { message: 'Phishing scan deleted successfully' };
    } catch (error) {
      if (error.isOperational) throw error;
      logger.error('Failed to delete phishing scan', { error: error.message });
      throw ApiError.internal('Failed to delete phishing scan');
    }
  }

  /**
   * Get phishing detection statistics for a user
   * @param {string} userId - User ID
   * @returns {Promise<Object>} Statistics
   */
  async getPhishingStatistics(userId) {
    try {
      const [total, phishingCount, threatLevelCounts] = await Promise.all([
        prisma.phishingScanHistory.count({ where: { userId } }),
        prisma.phishingScanHistory.count({ where: { userId, isPhishing: true } }),
        prisma.phishingScanHistory.groupBy({
          by: ['threatLevel'],
          where: { userId },
          _count: { threatLevel: true }
        })
      ]);

      const threatLevels = {};
      threatLevelCounts.forEach(item => {
        threatLevels[item.threatLevel] = item._count.threatLevel;
      });

      return {
        totalScans: total,
        phishingDetected: phishingCount,
        safeScans: total - phishingCount,
        phishingPercentage: total > 0 ? ((phishingCount / total) * 100).toFixed(2) : 0,
        threatLevels
      };
    } catch (error) {
      logger.error('Failed to get phishing statistics', { error: error.message });
      throw ApiError.internal('Failed to retrieve statistics');
    }
  }
}

module.exports = new PhishingService();
