/**
 * Phishing Service Unit Tests
 */

const nock = require('nock');
const prismaMock = require('../../mocks/prisma.mock');
const {
  mockPhishingDetection,
  mockUrlScan,
  mockBatchPhishingScan,
  mockAIServiceError,
  mockAIServiceUnavailable,
  cleanMocks,
  AI_SERVICE_URL
} = require('../../mocks/aiService.mock');
const { phishingText, phishingUrls, phishingHistoryRecord } = require('../../fixtures/phishing.fixture');

// Mock the database module
jest.mock('../../../src/config/database', () => require('../../mocks/prisma.mock'));

// Mock config
jest.mock('../../../src/config', () => ({
  ai: {
    serviceUrl: 'http://localhost:8000'
  }
}));

// Mock the logger
jest.mock('../../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn()
}));

const phishingService = require('../../../src/services/phishing.service');

describe('PhishingService', () => {
  beforeEach(() => {
    prismaMock.$reset();
    cleanMocks();
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanMocks();
  });

  describe('scanTextForPhishing', () => {
    it('should detect phishing text with high confidence', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.80 });

      const result = await phishingService.scanTextForPhishing(phishingText.urgentEmail);

      expect(result.isPhishing).toBe(true);
      expect(result.confidence).toBeGreaterThanOrEqual(0.65);
      expect(result.threatLevel).toBe('HIGH');
      expect(result.is_safe).toBe(false);
    });

    it('should mark safe text as not phishing', async () => {
      mockPhishingDetection({ isPhishing: false, confidence: 0.12 });

      const result = await phishingService.scanTextForPhishing(phishingText.greeting);

      expect(result.isPhishing).toBe(false);
      expect(result.is_safe).toBe(true);
      expect(result.threatLevel).toBe('NONE');
    });

    it('should calculate display confidence correctly for phishing', async () => {
      // When phishing confidence is 0.85, display should be 0.85 (phishing confidence)
      mockPhishingDetection({ isPhishing: true, confidence: 0.85 });

      const result = await phishingService.scanTextForPhishing(phishingText.bankScam);

      expect(result.confidence).toBe(0.85);
      expect(result.raw_phishing_confidence).toBe(0.85);
      expect(result.confidence_label).toBe('Phishing Confidence');
    });

    it('should calculate display confidence correctly for safe text', async () => {
      // When phishing confidence is 0.15, display should be 0.85 (1 - 0.15 = safety confidence)
      mockPhishingDetection({ isPhishing: false, confidence: 0.15 });

      const result = await phishingService.scanTextForPhishing(phishingText.normalEmail);

      expect(result.confidence).toBe(0.85);
      expect(result.raw_phishing_confidence).toBe(0.15);
      expect(result.confidence_label).toBe('Safety Confidence');
    });

    it('should generate danger causes for phishing detection', async () => {
      mockPhishingDetection({
        isPhishing: true,
        confidence: 0.87,
        threatLevel: 'HIGH'
      });

      const result = await phishingService.scanTextForPhishing(phishingText.urgentEmail);

      expect(result.danger_causes).toBeDefined();
      expect(result.danger_causes.length).toBeGreaterThan(0);
      expect(result.danger_causes[0].type).toBe('phishing_detected');
    });

    it('should save to history when userId provided', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.85 });
      prismaMock.phishingScanHistory.create.mockResolvedValue({ id: 'history-id' });

      await phishingService.scanTextForPhishing(
        phishingText.urgentEmail,
        'auto',
        'user-uuid-123'
      );

      expect(prismaMock.phishingScanHistory.create).toHaveBeenCalled();
    });

    it('should not save to history when userId is null', async () => {
      mockPhishingDetection({ isPhishing: false, confidence: 0.15 });

      await phishingService.scanTextForPhishing(phishingText.greeting, 'auto', null);

      expect(prismaMock.phishingScanHistory.create).not.toHaveBeenCalled();
    });

    it('should use correct scan type', async () => {
      mockPhishingDetection({ isPhishing: false, confidence: 0.20 });

      const result = await phishingService.scanTextForPhishing(
        phishingText.normalEmail,
        'email'
      );

      expect(result).toBeDefined();
    });

    it('should determine CRITICAL threat level for high confidence', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.90 });

      const result = await phishingService.scanTextForPhishing(phishingText.prizeScam);

      expect(result.threatLevel).toBe('CRITICAL');
    });

    it('should determine MEDIUM threat level for moderate confidence', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.68 });

      const result = await phishingService.scanTextForPhishing(phishingText.bankScam);

      expect(result.threatLevel).toBe('MEDIUM');
    });

    it('should handle AI service errors gracefully', async () => {
      mockAIServiceError('/predict-phishing', 500);

      await expect(
        phishingService.scanTextForPhishing(phishingText.urgentEmail)
      ).rejects.toThrow();
    });

    it('should handle AI service unavailable', async () => {
      mockAIServiceUnavailable('/predict-phishing');

      await expect(
        phishingService.scanTextForPhishing(phishingText.urgentEmail)
      ).rejects.toThrow('AI service unavailable');
    });
  });

  describe('scanUrlForPhishing', () => {
    it('should detect phishing URL', async () => {
      mockUrlScan({ isPhishing: true, confidence: 0.85 });

      const result = await phishingService.scanUrlForPhishing(phishingUrls.fakeBrand);

      expect(result.isPhishing).toBe(true);
      expect(result.phishingType).toBe('URL');
    });

    it('should mark safe URL as not phishing', async () => {
      mockUrlScan({ isPhishing: false, confidence: 0.10 });

      const result = await phishingService.scanUrlForPhishing(phishingUrls.normalUrl);

      expect(result.isPhishing).toBe(false);
      expect(result.is_safe).toBe(true);
    });

    it('should detect IP address URLs as suspicious', async () => {
      mockUrlScan({ isPhishing: true, confidence: 0.88 });

      const result = await phishingService.scanUrlForPhishing(phishingUrls.suspiciousIp);

      expect(result.isPhishing).toBe(true);
      // Check if danger causes contain IP address warning
      const hasIpWarning = result.danger_causes.some(
        cause => cause.type === 'ip_address_url'
      );
      expect(hasIpWarning).toBe(true);
    });

    it('should detect suspicious TLDs', async () => {
      mockUrlScan({ isPhishing: true, confidence: 0.80 });

      const result = await phishingService.scanUrlForPhishing(phishingUrls.suspiciousTld);

      expect(result.isPhishing).toBe(true);
    });

    it('should save URL scan to history when userId provided', async () => {
      mockUrlScan({ isPhishing: false, confidence: 0.12 });
      prismaMock.phishingScanHistory.create.mockResolvedValue({ id: 'url-history-id' });

      await phishingService.scanUrlForPhishing(phishingUrls.normalUrl, 'user-uuid-123');

      expect(prismaMock.phishingScanHistory.create).toHaveBeenCalled();
    });
  });

  describe('batchScanForPhishing', () => {
    it('should scan multiple items in batch', async () => {
      mockBatchPhishingScan({ itemCount: 3 });

      const items = [phishingText.urgentEmail, phishingText.normalEmail, phishingText.greeting];
      const result = await phishingService.batchScanForPhishing(items);

      expect(result.results).toBeDefined();
      expect(result.summary).toBeDefined();
      expect(result.summary.total).toBe(3);
    });
  });

  describe('getPhishingScanHistory', () => {
    it('should return paginated history', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([phishingHistoryRecord]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(1);

      const result = await phishingService.getPhishingScanHistory('user-uuid-123');

      expect(result.histories).toHaveLength(1);
      expect(result.pagination.total).toBe(1);
      expect(result.pagination.page).toBe(1);
    });

    it('should filter by phishing status', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([phishingHistoryRecord]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(1);

      const result = await phishingService.getPhishingScanHistory('user-uuid-123', {
        phishingOnly: true
      });

      expect(result.histories).toHaveLength(1);
      expect(result.histories[0].isPhishing).toBe(true);
    });

    it('should filter by threat level', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([phishingHistoryRecord]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(1);

      await phishingService.getPhishingScanHistory('user-uuid-123', {
        threatLevel: 'HIGH'
      });

      expect(prismaMock.phishingScanHistory.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            threatLevel: 'HIGH'
          })
        })
      );
    });

    it('should handle pagination parameters', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(50);

      const result = await phishingService.getPhishingScanHistory('user-uuid-123', {
        page: 2,
        limit: 10
      });

      expect(result.pagination.page).toBe(2);
      expect(result.pagination.limit).toBe(10);
      expect(result.pagination.totalPages).toBe(5);
    });
  });

  describe('getPhishingScanById', () => {
    it('should return specific scan', async () => {
      prismaMock.phishingScanHistory.findFirst.mockResolvedValue(phishingHistoryRecord);

      const result = await phishingService.getPhishingScanById(
        'phishing-scan-uuid-123',
        'user-uuid-123'
      );

      expect(result.id).toBe('phishing-scan-uuid-123');
    });

    it('should throw error if scan not found', async () => {
      prismaMock.phishingScanHistory.findFirst.mockResolvedValue(null);

      await expect(
        phishingService.getPhishingScanById('non-existent', 'user-uuid-123')
      ).rejects.toThrow('Phishing scan not found');
    });
  });

  describe('deletePhishingScan', () => {
    it('should delete scan successfully', async () => {
      prismaMock.phishingScanHistory.findFirst.mockResolvedValue(phishingHistoryRecord);
      prismaMock.phishingScanHistory.delete.mockResolvedValue(phishingHistoryRecord);

      const result = await phishingService.deletePhishingScan(
        'phishing-scan-uuid-123',
        'user-uuid-123'
      );

      expect(result.message).toBe('Phishing scan deleted successfully');
    });

    it('should throw error if scan not found', async () => {
      prismaMock.phishingScanHistory.findFirst.mockResolvedValue(null);

      await expect(
        phishingService.deletePhishingScan('non-existent', 'user-uuid-123')
      ).rejects.toThrow('Phishing scan not found');
    });
  });

  describe('getPhishingStatistics', () => {
    it('should return statistics', async () => {
      prismaMock.phishingScanHistory.count
        .mockResolvedValueOnce(100)  // total
        .mockResolvedValueOnce(25);  // phishing count
      prismaMock.phishingScanHistory.groupBy.mockResolvedValue([
        { threatLevel: 'HIGH', _count: { threatLevel: 15 } },
        { threatLevel: 'MEDIUM', _count: { threatLevel: 10 } },
        { threatLevel: 'NONE', _count: { threatLevel: 75 } }
      ]);

      const result = await phishingService.getPhishingStatistics('user-uuid-123');

      expect(result.totalScans).toBe(100);
      expect(result.phishingDetected).toBe(25);
      expect(result.safeScans).toBe(75);
      expect(result.phishingPercentage).toBe('25.00');
      expect(result.threatLevels).toHaveProperty('HIGH', 15);
    });

    it('should handle zero total scans', async () => {
      prismaMock.phishingScanHistory.count.mockResolvedValue(0);
      prismaMock.phishingScanHistory.groupBy.mockResolvedValue([]);

      const result = await phishingService.getPhishingStatistics('user-uuid-123');

      expect(result.totalScans).toBe(0);
      expect(result.phishingPercentage).toBe(0);
    });
  });
});
