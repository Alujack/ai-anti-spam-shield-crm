/**
 * Phishing Detection Integration Tests
 */

const request = require('supertest');
const nock = require('nock');
const prismaMock = require('../mocks/prisma.mock');
const {
  mockPhishingDetection,
  mockUrlScan,
  cleanMocks,
  AI_SERVICE_URL
} = require('../mocks/aiService.mock');
const { phishingText, phishingUrls, phishingHistoryRecord } = require('../fixtures/phishing.fixture');
const { validUser } = require('../fixtures/users.fixture');

// Mock dependencies
jest.mock('../../src/config/database', () => require('../mocks/prisma.mock'));

jest.mock('../../src/config', () => ({
  ai: { serviceUrl: 'http://localhost:8000' },
  jwt: { secret: 'test-secret' }
}));

jest.mock('../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  stream: { write: jest.fn() }
}));

jest.mock('../../src/utils/auth', () => ({
  verifyToken: jest.fn().mockReturnValue({ userId: 'user-uuid-123' }),
  hashPassword: jest.fn(),
  comparePassword: jest.fn(),
  generateToken: jest.fn(),
  generateRefreshToken: jest.fn()
}));

// Create minimal express app for testing
const express = require('express');
const phishingController = require('../../src/controllers/phishing.controller');

const createTestApp = () => {
  const app = express();
  app.use(express.json());

  // Mock auth middleware
  const authMiddleware = (req, res, next) => {
    if (req.headers.authorization) {
      req.user = { userId: validUser.id };
    }
    next();
  };

  // Register routes
  app.post('/api/v1/phishing/scan-text', authMiddleware, phishingController.scanText);
  app.post('/api/v1/phishing/scan-url', authMiddleware, phishingController.scanUrl);
  app.get('/api/v1/phishing/history', authMiddleware, phishingController.getHistory);
  app.get('/api/v1/phishing/statistics', authMiddleware, phishingController.getStatistics);

  // Error handler
  app.use((err, req, res, next) => {
    res.status(err.statusCode || 500).json({
      success: false,
      message: err.message || 'Internal Server Error'
    });
  });

  return app;
};

describe('Phishing Integration Tests', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  beforeEach(() => {
    prismaMock.$reset();
    cleanMocks();
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanMocks();
  });

  describe('POST /api/v1/phishing/scan-text', () => {
    it('should detect phishing in suspicious text', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.87 });
      prismaMock.phishingScanHistory.create.mockResolvedValue({ id: 'scan-id' });

      const res = await request(app)
        .post('/api/v1/phishing/scan-text')
        .set('Authorization', 'Bearer mock-token')
        .send({ text: phishingText.urgentEmail });

      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.isPhishing).toBe(true);
      expect(res.body.data.threatLevel).toBeDefined();
    });

    it('should mark safe text correctly', async () => {
      mockPhishingDetection({ isPhishing: false, confidence: 0.12 });

      const res = await request(app)
        .post('/api/v1/phishing/scan-text')
        .set('Authorization', 'Bearer mock-token')
        .send({ text: phishingText.greeting });

      expect(res.status).toBe(200);
      expect(res.body.data.isPhishing).toBe(false);
      expect(res.body.data.is_safe).toBe(true);
    });

    it('should work without authentication', async () => {
      mockPhishingDetection({ isPhishing: false, confidence: 0.10 });

      const res = await request(app)
        .post('/api/v1/phishing/scan-text')
        .send({ text: phishingText.normalEmail });

      expect(res.status).toBe(200);
    });

    it('should return danger causes for phishing', async () => {
      mockPhishingDetection({ isPhishing: true, confidence: 0.90 });
      prismaMock.phishingScanHistory.create.mockResolvedValue({ id: 'scan-id' });

      const res = await request(app)
        .post('/api/v1/phishing/scan-text')
        .set('Authorization', 'Bearer mock-token')
        .send({ text: phishingText.bankScam });

      expect(res.body.data.danger_causes).toBeDefined();
      expect(res.body.data.danger_causes.length).toBeGreaterThan(0);
    });
  });

  describe('POST /api/v1/phishing/scan-url', () => {
    it('should detect phishing URL', async () => {
      mockUrlScan({ isPhishing: true, confidence: 0.85 });
      prismaMock.phishingScanHistory.create.mockResolvedValue({ id: 'url-scan-id' });

      const res = await request(app)
        .post('/api/v1/phishing/scan-url')
        .set('Authorization', 'Bearer mock-token')
        .send({ url: phishingUrls.fakeBrand });

      expect(res.status).toBe(200);
      expect(res.body.data.isPhishing).toBe(true);
      expect(res.body.data.phishingType).toBe('URL');
    });

    it('should mark safe URL correctly', async () => {
      mockUrlScan({ isPhishing: false, confidence: 0.08 });

      const res = await request(app)
        .post('/api/v1/phishing/scan-url')
        .set('Authorization', 'Bearer mock-token')
        .send({ url: phishingUrls.normalUrl });

      expect(res.status).toBe(200);
      expect(res.body.data.is_safe).toBe(true);
    });
  });

  describe('GET /api/v1/phishing/history', () => {
    it('should return paginated history', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([phishingHistoryRecord]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(1);

      const res = await request(app)
        .get('/api/v1/phishing/history')
        .set('Authorization', 'Bearer mock-token');

      expect(res.status).toBe(200);
      expect(res.body.data.histories).toHaveLength(1);
      expect(res.body.data.pagination).toBeDefined();
    });

    it('should support pagination parameters', async () => {
      prismaMock.phishingScanHistory.findMany.mockResolvedValue([]);
      prismaMock.phishingScanHistory.count.mockResolvedValue(50);

      const res = await request(app)
        .get('/api/v1/phishing/history?page=2&limit=10')
        .set('Authorization', 'Bearer mock-token');

      expect(res.status).toBe(200);
      expect(res.body.data.pagination.page).toBe(2);
    });
  });

  describe('GET /api/v1/phishing/statistics', () => {
    it('should return phishing statistics', async () => {
      prismaMock.phishingScanHistory.count
        .mockResolvedValueOnce(100)
        .mockResolvedValueOnce(25);
      prismaMock.phishingScanHistory.groupBy.mockResolvedValue([
        { threatLevel: 'HIGH', _count: { threatLevel: 15 } },
        { threatLevel: 'NONE', _count: { threatLevel: 75 } }
      ]);

      const res = await request(app)
        .get('/api/v1/phishing/statistics')
        .set('Authorization', 'Bearer mock-token');

      expect(res.status).toBe(200);
      expect(res.body.data.totalScans).toBe(100);
      expect(res.body.data.phishingDetected).toBe(25);
    });
  });
});
