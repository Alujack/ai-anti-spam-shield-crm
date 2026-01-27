/**
 * Report Integration Tests
 * Tests report submission and management API endpoints
 */

const request = require('supertest');
const prismaMock = require('../mocks/prisma.mock');

// Mock dependencies before requiring app
jest.mock('../../src/config/database', () => require('../mocks/prisma.mock'));

jest.mock('../../src/utils/auth', () => ({
  verifyToken: jest.fn().mockReturnValue({ id: 'user-123', role: 'USER' }),
  generateToken: jest.fn().mockReturnValue('mock-jwt-token'),
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
  getQueue: jest.fn().mockReturnValue(null),
  QUEUES: {},
}));

const express = require('express');
const reportController = require('../../src/controllers/report.controller');

const createTestApp = () => {
  const app = express();
  app.use(express.json());

  // Auth middleware mock
  const requireAuth = (req, res, next) => {
    if (req.headers.authorization) {
      req.user = { id: 'user-123', role: 'USER' };
      next();
    } else {
      res.status(401).json({ error: 'Unauthorized' });
    }
  };

  const requireAdmin = (req, res, next) => {
    if (req.headers.authorization === 'Bearer admin-token') {
      req.user = { id: 'admin-1', role: 'ADMIN' };
      next();
    } else if (req.headers.authorization) {
      res.status(403).json({ error: 'Forbidden' });
    } else {
      res.status(401).json({ error: 'Unauthorized' });
    }
  };

  // Register routes
  app.post('/api/v1/reports', requireAuth, reportController.createReport);
  app.get('/api/v1/reports', requireAuth, reportController.getUserReports);
  app.get('/api/v1/reports/:id', requireAuth, reportController.getReportById);
  app.put('/api/v1/reports/:id/status', requireAdmin, reportController.updateReportStatus);
  app.delete('/api/v1/reports/:id', requireAuth, reportController.deleteReport);
  app.get('/api/v1/reports/stats/summary', requireAuth, reportController.getStatistics);

  // Error handler
  app.use((err, req, res, next) => {
    res.status(err.statusCode || 500).json({
      success: false,
      message: err.message || 'Internal Server Error',
    });
  });

  return app;
};

describe('Report Integration Tests', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  beforeEach(() => {
    prismaMock.$reset();
    jest.clearAllMocks();
  });

  describe('POST /api/v1/reports', () => {
    const validReportData = {
      messageText: 'Suspicious spam message: Win $10000 now!',
      reportType: 'SPAM',
      description: 'This message appears to be spam',
      url: 'http://scam.link',
      phoneNumber: '+1234567890',
    };

    it('should create a new spam report', async () => {
      prismaMock.report.create.mockResolvedValue({
        id: 'report-1',
        userId: 'user-123',
        ...validReportData,
        status: 'PENDING',
        createdAt: new Date(),
      });

      const res = await request(app)
        .post('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send(validReportData);

      expect(res.status).toBe(201);
      expect(res.body.status).toBe('success');
      expect(res.body.data.id).toBe('report-1');
      expect(res.body.data.type).toBe('spam'); // Transformed to lowercase
    });

    it('should create a phishing report', async () => {
      const phishingReport = { ...validReportData, reportType: 'PHISHING' };
      prismaMock.report.create.mockResolvedValue({
        id: 'report-2',
        userId: 'user-123',
        ...phishingReport,
        status: 'PENDING',
      });

      const res = await request(app)
        .post('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send(phishingReport);

      expect(res.status).toBe(201);
      expect(res.body.data.type).toBe('phishing');
    });

    it('should create a scam report', async () => {
      const scamReport = { ...validReportData, reportType: 'SCAM' };
      prismaMock.report.create.mockResolvedValue({
        id: 'report-3',
        userId: 'user-123',
        ...scamReport,
        status: 'PENDING',
      });

      const res = await request(app)
        .post('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send(scamReport);

      expect(res.status).toBe(201);
      expect(res.body.data.type).toBe('scam');
    });

    it('should reject invalid report type', async () => {
      const invalidReport = { ...validReportData, reportType: 'INVALID' };

      const res = await request(app)
        .post('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send(invalidReport);

      expect(res.status).toBe(400);
      expect(res.body.message).toContain('Invalid report type');
    });

    it('should reject missing required fields', async () => {
      const res = await request(app)
        .post('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send({ description: 'Missing message text' });

      expect(res.status).toBe(400);
    });

    it('should require authentication', async () => {
      const res = await request(app)
        .post('/api/v1/reports')
        .send(validReportData);

      expect(res.status).toBe(401);
    });
  });

  describe('GET /api/v1/reports', () => {
    it('should return paginated user reports', async () => {
      const mockReports = [
        { id: '1', messageText: 'Report 1', reportType: 'SPAM', status: 'PENDING' },
        { id: '2', messageText: 'Report 2', reportType: 'PHISHING', status: 'RESOLVED' },
      ];
      prismaMock.report.findMany.mockResolvedValue(mockReports);
      prismaMock.report.count.mockResolvedValue(10);

      const res = await request(app)
        .get('/api/v1/reports')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.reports).toHaveLength(2);
      expect(res.body.data.pagination.total).toBe(10);
    });

    it('should filter by status', async () => {
      prismaMock.report.findMany.mockResolvedValue([]);
      prismaMock.report.count.mockResolvedValue(0);

      await request(app)
        .get('/api/v1/reports?status=PENDING')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(prismaMock.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ status: 'PENDING' }),
        })
      );
    });

    it('should require authentication', async () => {
      const res = await request(app).get('/api/v1/reports');

      expect(res.status).toBe(401);
    });
  });

  describe('GET /api/v1/reports/:id', () => {
    it('should return report by ID', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        messageText: 'Test report',
        reportType: 'SPAM',
        status: 'PENDING',
      };
      prismaMock.report.findFirst.mockResolvedValue(mockReport);

      const res = await request(app)
        .get('/api/v1/reports/report-1')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.id).toBe('report-1');
    });

    it('should return 404 for non-existent report', async () => {
      prismaMock.report.findFirst.mockResolvedValue(null);

      const res = await request(app)
        .get('/api/v1/reports/non-existent')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(404);
    });
  });

  describe('PUT /api/v1/reports/:id/status', () => {
    it('should allow admin to update report status', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        status: 'PENDING',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prismaMock.report.findFirst.mockResolvedValue(mockReport);
      prismaMock.report.update.mockResolvedValue({
        ...mockReport,
        status: 'RESOLVED',
      });

      const res = await request(app)
        .put('/api/v1/reports/report-1/status')
        .set('Authorization', 'Bearer admin-token')
        .send({ status: 'RESOLVED' });

      expect(res.status).toBe(200);
      expect(res.body.data.status).toBe('RESOLVED');
    });

    it('should reject non-admin status update', async () => {
      const res = await request(app)
        .put('/api/v1/reports/report-1/status')
        .set('Authorization', 'Bearer mock-jwt-token')
        .send({ status: 'RESOLVED' });

      expect(res.status).toBe(403);
    });

    it('should require authentication', async () => {
      const res = await request(app)
        .put('/api/v1/reports/report-1/status')
        .send({ status: 'RESOLVED' });

      expect(res.status).toBe(401);
    });
  });

  describe('DELETE /api/v1/reports/:id', () => {
    it('should delete user own report', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prismaMock.report.findFirst.mockResolvedValue(mockReport);
      prismaMock.report.delete.mockResolvedValue(mockReport);

      const res = await request(app)
        .delete('/api/v1/reports/report-1')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.message).toContain('deleted');
    });

    it('should return 404 for non-existent report', async () => {
      prismaMock.report.findFirst.mockResolvedValue(null);

      const res = await request(app)
        .delete('/api/v1/reports/non-existent')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(404);
    });
  });

  describe('GET /api/v1/reports/stats/summary', () => {
    it('should return report statistics', async () => {
      prismaMock.report.count
        .mockResolvedValueOnce(100) // total
        .mockResolvedValueOnce(40) // pending
        .mockResolvedValueOnce(20) // reviewed
        .mockResolvedValueOnce(30) // resolved
        .mockResolvedValueOnce(10); // rejected

      prismaMock.report.groupBy.mockResolvedValue([
        { reportType: 'SPAM', _count: 50 },
        { reportType: 'PHISHING', _count: 30 },
        { reportType: 'SCAM', _count: 20 },
      ]);

      const res = await request(app)
        .get('/api/v1/reports/stats/summary')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.data.total).toBe(100);
      expect(res.body.data.pending).toBe(40);
      expect(res.body.data.byType.spam).toBe(50);
    });
  });
});
