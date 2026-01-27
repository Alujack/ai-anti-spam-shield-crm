/**
 * Message Scanning Integration Tests
 * Tests spam/scam detection API endpoints
 */

const request = require('supertest');
const prismaMock = require('../mocks/prisma.mock');
const aiServiceMock = require('../mocks/aiService.mock');

// Mock dependencies before requiring app
jest.mock('../../src/config/database', () => require('../mocks/prisma.mock'));
jest.mock('axios', () => require('../mocks/aiService.mock'));

jest.mock('../../src/utils/auth', () => ({
  hashPassword: jest.fn().mockResolvedValue('$2a$10$hashedpassword'),
  comparePassword: jest.fn(),
  generateToken: jest.fn().mockReturnValue('mock-jwt-token'),
  generateRefreshToken: jest.fn().mockReturnValue('mock-refresh-token'),
  verifyToken: jest.fn().mockReturnValue({ id: 'user-123' }),
}));

jest.mock('../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
  stream: { write: jest.fn() },
}));

jest.mock('../../src/config/redis', () => ({
  createClient: jest.fn().mockReturnValue({
    connect: jest.fn(),
    on: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn(),
  }),
}));

jest.mock('../../src/config/queue', () => ({
  textQueue: { add: jest.fn() },
  voiceQueue: { add: jest.fn() },
  urlQueue: { add: jest.fn() },
  getQueue: jest.fn().mockReturnValue(null),
  QUEUES: {},
}));

const express = require('express');
const messageController = require('../../src/controllers/message.controller');

const createTestApp = () => {
  const app = express();
  app.use(express.json());

  // Auth middleware mock
  const optionalAuth = (req, res, next) => {
    if (req.headers.authorization) {
      req.user = { id: 'user-123' };
    }
    next();
  };

  const requireAuth = (req, res, next) => {
    if (req.headers.authorization) {
      req.user = { id: 'user-123' };
      next();
    } else {
      res.status(401).json({ error: 'Unauthorized' });
    }
  };

  // Register routes
  app.post('/api/v1/messages/scan-text', optionalAuth, messageController.scanText);
  app.get('/api/v1/messages/history', requireAuth, messageController.getHistory);
  app.get('/api/v1/messages/history/:id', requireAuth, messageController.getHistoryById);
  app.delete('/api/v1/messages/history/:id', requireAuth, messageController.deleteHistory);
  app.get('/api/v1/messages/stats', requireAuth, messageController.getStatistics);

  // Error handler
  app.use((err, req, res, next) => {
    res.status(err.statusCode || 500).json({
      success: false,
      message: err.message || 'Internal Server Error',
    });
  });

  return app;
};

describe('Message Scanning Integration Tests', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  beforeEach(() => {
    prismaMock.$reset();
    aiServiceMock.post.mockReset();
    jest.clearAllMocks();
  });

  describe('POST /api/v1/messages/scan-text', () => {
    describe('Spam Detection', () => {
      it('should detect spam message and return high risk result', async () => {
        aiServiceMock.post.mockResolvedValue({
          data: {
            confidence: 0.92,
            prediction: 'spam',
            details: {
              features: {
                has_url: true,
                urgency_words: true,
                spam_keywords: true,
              },
            },
          },
        });

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({
            message: 'URGENT! You won $10,000! Click http://scam.link to claim NOW!',
          });

        expect(res.status).toBe(200);
        expect(res.body.status).toBe('success');
        expect(res.body.data.is_spam).toBe(true);
        expect(res.body.data.risk_level).toBe('CRITICAL');
        expect(res.body.data.danger_causes.length).toBeGreaterThan(0);
        expect(res.body.data.confidence_label).toBe('Spam Confidence');
      });

      it('should detect safe message and return safe result', async () => {
        aiServiceMock.post.mockResolvedValue({
          data: {
            confidence: 0.15,
            prediction: 'ham',
          },
        });

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({
            message: 'Meeting tomorrow at 3pm in the conference room.',
          });

        expect(res.status).toBe(200);
        expect(res.body.data.is_spam).toBe(false);
        expect(res.body.data.is_safe).toBe(true);
        expect(res.body.data.risk_level).toBe('NONE');
        expect(res.body.data.confidence_label).toBe('Safety Confidence');
      });

      it('should bypass AI service for safe greetings', async () => {
        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: 'Hi, how are you?' });

        expect(res.status).toBe(200);
        expect(res.body.data.is_spam).toBe(false);
        expect(res.body.data.is_safe).toBe(true);
        expect(res.body.data.details.bypass_reason).toBe('safe_greeting_pattern');
        expect(aiServiceMock.post).not.toHaveBeenCalled();
      });

      it('should apply short message penalty', async () => {
        aiServiceMock.post.mockResolvedValue({
          data: {
            confidence: 0.75, // Would be spam without penalty
            prediction: 'spam',
          },
        });

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: 'ok thanks' }); // 2 words

        expect(res.status).toBe(200);
        // 0.75 * 0.6 = 0.45 < 0.80 threshold
        expect(res.body.data.is_spam).toBe(false);
        expect(res.body.data.short_message_penalty_applied).toBe(true);
      });
    });

    describe('Authentication', () => {
      it('should save history when authenticated', async () => {
        aiServiceMock.post.mockResolvedValue({
          data: { confidence: 0.85, prediction: 'spam' },
        });
        prismaMock.scanHistory.create.mockResolvedValue({ id: 'history-1' });

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .set('Authorization', 'Bearer mock-jwt-token')
          .send({ message: 'Spam message here' });

        expect(res.status).toBe(200);
        expect(prismaMock.scanHistory.create).toHaveBeenCalled();
      });

      it('should work without authentication (no history saved)', async () => {
        aiServiceMock.post.mockResolvedValue({
          data: { confidence: 0.85, prediction: 'spam' },
        });

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: 'Spam message here' });

        expect(res.status).toBe(200);
        expect(prismaMock.scanHistory.create).not.toHaveBeenCalled();
      });
    });

    describe('Validation', () => {
      it('should reject empty message', async () => {
        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: '' });

        expect(res.status).toBe(400);
      });

      it('should reject missing message field', async () => {
        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({});

        expect(res.status).toBe(400);
      });
    });

    describe('Error Handling', () => {
      it('should handle AI service unavailable', async () => {
        const error = new Error('Connection refused');
        error.code = 'ECONNREFUSED';
        aiServiceMock.post.mockRejectedValue(error);

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: 'Test message' });

        expect(res.status).toBe(500);
        expect(res.body.message).toContain('unavailable');
      });

      it('should handle AI service timeout', async () => {
        const error = new Error('Timeout');
        error.code = 'ETIMEDOUT';
        aiServiceMock.post.mockRejectedValue(error);

        const res = await request(app)
          .post('/api/v1/messages/scan-text')
          .send({ message: 'Test message' });

        expect(res.status).toBe(500);
        expect(res.body.message).toContain('timed out');
      });
    });
  });

  describe('GET /api/v1/messages/history', () => {
    it('should return paginated history', async () => {
      const mockHistories = [
        { id: '1', message: 'Test 1', isSpam: true, confidence: 0.85 },
        { id: '2', message: 'Test 2', isSpam: false, confidence: 0.90 },
      ];
      prismaMock.scanHistory.findMany.mockResolvedValue(mockHistories);
      prismaMock.scanHistory.count.mockResolvedValue(50);

      const res = await request(app)
        .get('/api/v1/messages/history')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.histories).toHaveLength(2);
      expect(res.body.data.pagination.total).toBe(50);
    });

    it('should filter by spam status', async () => {
      prismaMock.scanHistory.findMany.mockResolvedValue([]);
      prismaMock.scanHistory.count.mockResolvedValue(0);

      await request(app)
        .get('/api/v1/messages/history?isSpam=true')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(prismaMock.scanHistory.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ isSpam: true }),
        })
      );
    });

    it('should require authentication', async () => {
      const res = await request(app).get('/api/v1/messages/history');

      expect(res.status).toBe(401);
    });
  });

  describe('GET /api/v1/messages/history/:id', () => {
    it('should return specific history item', async () => {
      const mockHistory = {
        id: 'history-1',
        userId: 'user-123',
        message: 'Test message',
        isSpam: true,
      };
      prismaMock.scanHistory.findFirst.mockResolvedValue(mockHistory);

      const res = await request(app)
        .get('/api/v1/messages/history/history-1')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.id).toBe('history-1');
    });

    it('should return 404 for non-existent history', async () => {
      prismaMock.scanHistory.findFirst.mockResolvedValue(null);

      const res = await request(app)
        .get('/api/v1/messages/history/non-existent')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(404);
    });
  });

  describe('DELETE /api/v1/messages/history/:id', () => {
    it('should delete history item', async () => {
      prismaMock.scanHistory.findFirst.mockResolvedValue({
        id: 'history-1',
        userId: 'user-123',
      });
      prismaMock.scanHistory.delete.mockResolvedValue({});

      const res = await request(app)
        .delete('/api/v1/messages/history/history-1')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.message).toContain('deleted');
    });

    it('should return 404 for non-existent history', async () => {
      prismaMock.scanHistory.findFirst.mockResolvedValue(null);

      const res = await request(app)
        .delete('/api/v1/messages/history/non-existent')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(404);
    });
  });

  describe('GET /api/v1/messages/stats', () => {
    it('should return user statistics', async () => {
      prismaMock.scanHistory.count
        .mockResolvedValueOnce(100) // total
        .mockResolvedValueOnce(30) // spam
        .mockResolvedValueOnce(70) // ham
        .mockResolvedValueOnce(20) // voice
        .mockResolvedValueOnce(80); // text

      const res = await request(app)
        .get('/api/v1/messages/stats')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.totalScans).toBe(100);
      expect(res.body.data.spamDetected).toBe(30);
      expect(res.body.data.safeMessages).toBe(70);
    });

    it('should require authentication', async () => {
      const res = await request(app).get('/api/v1/messages/stats');

      expect(res.status).toBe(401);
    });
  });
});
