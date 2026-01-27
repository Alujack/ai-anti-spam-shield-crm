/**
 * Unit Tests for Report Service
 * Tests report submission and management functionality
 */

// Mock dependencies before requiring the service
jest.mock('../../../src/config/database', () => ({
  report: {
    create: jest.fn(),
    findMany: jest.fn(),
    findFirst: jest.fn(),
    count: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    groupBy: jest.fn(),
  },
}));
jest.mock('../../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
}));

const reportService = require('../../../src/services/report.service');
const prisma = require('../../../src/config/database');

describe('ReportService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createReport', () => {
    const validReportData = {
      userId: 'user-123',
      messageText: 'Suspicious spam message content',
      reportType: 'SPAM',
      description: 'This message looks like spam',
      url: 'http://suspicious.com',
      phoneNumber: '+1234567890',
      senderInfo: 'unknown@scam.com',
    };

    test('should create a valid spam report', async () => {
      const mockReport = {
        id: 'report-1',
        ...validReportData,
        status: 'PENDING',
        createdAt: new Date(),
      };
      prisma.report.create.mockResolvedValue(mockReport);

      const result = await reportService.createReport(validReportData);

      expect(prisma.report.create).toHaveBeenCalledWith({
        data: validReportData,
      });
      expect(result.id).toBe('report-1');
      expect(result.type).toBe('spam'); // Transformed to lowercase
      expect(result.content).toBe(validReportData.messageText);
    });

    test('should create a valid phishing report', async () => {
      const phishingData = { ...validReportData, reportType: 'PHISHING' };
      const mockReport = { id: 'report-2', ...phishingData };
      prisma.report.create.mockResolvedValue(mockReport);

      const result = await reportService.createReport(phishingData);

      expect(result.type).toBe('phishing');
    });

    test('should create a valid scam report', async () => {
      const scamData = { ...validReportData, reportType: 'SCAM' };
      const mockReport = { id: 'report-3', ...scamData };
      prisma.report.create.mockResolvedValue(mockReport);

      const result = await reportService.createReport(scamData);

      expect(result.type).toBe('scam');
    });

    test.each(['SPAM', 'PHISHING', 'SCAM', 'SUSPICIOUS', 'OTHER'])(
      'should accept valid report type: %s',
      async (reportType) => {
        const data = { ...validReportData, reportType };
        const mockReport = { id: 'report-x', ...data };
        prisma.report.create.mockResolvedValue(mockReport);

        const result = await reportService.createReport(data);

        expect(result).toBeDefined();
      }
    );

    test('should reject invalid report type', async () => {
      const invalidData = { ...validReportData, reportType: 'INVALID' };

      await expect(reportService.createReport(invalidData)).rejects.toThrow(
        'Invalid report type'
      );
    });
  });

  describe('getAllReports', () => {
    test('should return paginated reports', async () => {
      const mockReports = [
        { id: '1', messageText: 'Report 1', reportType: 'SPAM' },
        { id: '2', messageText: 'Report 2', reportType: 'PHISHING' },
      ];
      prisma.report.findMany.mockResolvedValue(mockReports);
      prisma.report.count.mockResolvedValue(50);

      const result = await reportService.getAllReports({ page: 1, limit: 20 });

      expect(result.reports).toHaveLength(2);
      expect(result.pagination.total).toBe(50);
      expect(result.pagination.totalPages).toBe(3);
      expect(result.reports[0].type).toBe('spam'); // Transformed
    });

    test('should filter by status', async () => {
      prisma.report.findMany.mockResolvedValue([]);
      prisma.report.count.mockResolvedValue(0);

      await reportService.getAllReports({ status: 'PENDING' });

      expect(prisma.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ status: 'PENDING' }),
        })
      );
    });

    test('should filter by reportType', async () => {
      prisma.report.findMany.mockResolvedValue([]);
      prisma.report.count.mockResolvedValue(0);

      await reportService.getAllReports({ reportType: 'SPAM' });

      expect(prisma.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ reportType: 'SPAM' }),
        })
      );
    });

    test('should filter by userId', async () => {
      prisma.report.findMany.mockResolvedValue([]);
      prisma.report.count.mockResolvedValue(0);

      await reportService.getAllReports({ userId: 'user-123' });

      expect(prisma.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ userId: 'user-123' }),
        })
      );
    });
  });

  describe('getReportById', () => {
    test('should return report when found', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        messageText: 'Test report',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);

      const result = await reportService.getReportById('report-1', 'user-123');

      expect(result.id).toBe('report-1');
      expect(result.type).toBe('spam');
    });

    test('should throw not found when report does not exist', async () => {
      prisma.report.findFirst.mockResolvedValue(null);

      await expect(
        reportService.getReportById('non-existent', 'user-123')
      ).rejects.toThrow('Report not found');
    });

    test('should allow admin to access any report', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'other-user',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);

      const result = await reportService.getReportById(
        'report-1',
        'admin-user',
        true
      );

      expect(result.id).toBe('report-1');
    });
  });

  describe('getUserReports', () => {
    test('should return user-specific reports', async () => {
      const mockReports = [
        { id: '1', userId: 'user-123', messageText: 'Report 1', reportType: 'SPAM' },
      ];
      prisma.report.findMany.mockResolvedValue(mockReports);
      prisma.report.count.mockResolvedValue(5);

      const result = await reportService.getUserReports('user-123');

      expect(prisma.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ userId: 'user-123' }),
        })
      );
      expect(result.pagination.total).toBe(5);
    });

    test('should filter user reports by status', async () => {
      prisma.report.findMany.mockResolvedValue([]);
      prisma.report.count.mockResolvedValue(0);

      await reportService.getUserReports('user-123', { status: 'RESOLVED' });

      expect(prisma.report.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { userId: 'user-123', status: 'RESOLVED' },
        })
      );
    });
  });

  describe('updateReport', () => {
    test('should allow admin to update status', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        status: 'PENDING',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);
      prisma.report.update.mockResolvedValue({
        ...mockReport,
        status: 'RESOLVED',
      });

      const result = await reportService.updateReport(
        'report-1',
        { status: 'RESOLVED' },
        'admin-user',
        true
      );

      expect(result.status).toBe('RESOLVED');
    });

    test('should not allow non-admin to update status', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);

      await expect(
        reportService.updateReport(
          'report-1',
          { status: 'RESOLVED' },
          'user-123',
          false
        )
      ).rejects.toThrow('Only admins can update report status');
    });

    test('should allow user to update own report description', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        description: 'Old description',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);
      prisma.report.update.mockResolvedValue({
        ...mockReport,
        description: 'New description',
      });

      const result = await reportService.updateReport(
        'report-1',
        { description: 'New description' },
        'user-123',
        false
      );

      expect(result.description).toBe('New description');
    });

    test('should not allow user to update other users report', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'other-user',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);

      await expect(
        reportService.updateReport(
          'report-1',
          { description: 'New description' },
          'user-123',
          false
        )
      ).rejects.toThrow('You can only update your own reports');
    });
  });

  describe('deleteReport', () => {
    test('should delete report when authorized', async () => {
      const mockReport = {
        id: 'report-1',
        userId: 'user-123',
        messageText: 'Test',
        reportType: 'SPAM',
      };
      prisma.report.findFirst.mockResolvedValue(mockReport);
      prisma.report.delete.mockResolvedValue(mockReport);

      const result = await reportService.deleteReport('report-1', 'user-123');

      expect(result.message).toBe('Report deleted successfully');
      expect(prisma.report.delete).toHaveBeenCalledWith({
        where: { id: 'report-1' },
      });
    });

    test('should throw not found when report does not exist', async () => {
      prisma.report.findFirst.mockResolvedValue(null);

      await expect(
        reportService.deleteReport('non-existent', 'user-123')
      ).rejects.toThrow('Report not found');
    });
  });

  describe('generateStatistics', () => {
    test('should return comprehensive statistics', async () => {
      prisma.report.count
        .mockResolvedValueOnce(100) // total
        .mockResolvedValueOnce(40) // pending
        .mockResolvedValueOnce(20) // reviewed
        .mockResolvedValueOnce(30) // resolved
        .mockResolvedValueOnce(10); // rejected

      prisma.report.groupBy.mockResolvedValue([
        { reportType: 'SPAM', _count: 50 },
        { reportType: 'PHISHING', _count: 30 },
        { reportType: 'SCAM', _count: 20 },
      ]);

      const result = await reportService.generateStatistics();

      expect(result.total).toBe(100);
      expect(result.totalReports).toBe(100);
      expect(result.pending).toBe(40);
      expect(result.pendingReports).toBe(40);
      expect(result.resolved).toBe(30);
      expect(result.byStatus.pending).toBe(40);
      expect(result.byType.spam).toBe(50);
      expect(result.byType.phishing).toBe(30);
    });

    test('should filter statistics by userId', async () => {
      prisma.report.count.mockResolvedValue(0);
      prisma.report.groupBy.mockResolvedValue([]);

      await reportService.generateStatistics({ userId: 'user-123' });

      expect(prisma.report.count).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { userId: 'user-123' },
        })
      );
    });
  });
});
