/**
 * Unit Tests for Feedback Service
 * Tests user feedback submission and continuous learning functionality
 */

// Mock dependencies before requiring the service
jest.mock('../../../src/config/database', () => ({
  userFeedback: {
    create: jest.fn(),
    findMany: jest.fn(),
    findFirst: jest.fn(),
    findUnique: jest.fn(),
    count: jest.fn(),
    update: jest.fn(),
    updateMany: jest.fn(),
    groupBy: jest.fn(),
  },
  scanHistory: {
    findUnique: jest.fn(),
  },
  phishingScanHistory: {
    findUnique: jest.fn(),
  },
  $queryRaw: jest.fn().mockResolvedValue([]),
}));
jest.mock('../../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
}));
jest.mock('../../../src/config/queue', () => ({
  getQueue: jest.fn().mockReturnValue(null),
  QUEUES: {
    FEEDBACK: 'feedback',
    RETRAINING: 'retraining',
  },
}));

const feedbackService = require('../../../src/services/feedback.service');
const prisma = require('../../../src/config/database');

describe('FeedbackService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('submitFeedback', () => {
    describe('Text Scan Feedback', () => {
      test('should submit feedback for text scan', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'user-123',
          prediction: 'spam',
          isSpam: true,
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue(null); // No existing feedback
        prisma.userFeedback.create.mockResolvedValue({
          id: 'feedback-1',
          userId: 'user-123',
          scanHistoryId: 'scan-1',
          feedbackType: 'false_positive',
          originalPrediction: 'spam',
          actualLabel: 'ham',
          status: 'pending',
        });

        const result = await feedbackService.submitFeedback({
          userId: 'user-123',
          scanId: 'scan-1',
          scanType: 'text',
          feedbackType: 'false_positive',
        });

        expect(result.id).toBe('feedback-1');
        expect(result.feedbackType).toBe('false_positive');
        expect(result.actualLabel).toBe('ham');
      });

      test('should reject feedback for non-owned scan', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'other-user',
          prediction: 'spam',
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);

        await expect(
          feedbackService.submitFeedback({
            userId: 'user-123',
            scanId: 'scan-1',
            scanType: 'text',
            feedbackType: 'false_positive',
          })
        ).rejects.toThrow('You can only provide feedback on your own scans');
      });

      test('should reject feedback for non-existent scan', async () => {
        prisma.scanHistory.findUnique.mockResolvedValue(null);

        await expect(
          feedbackService.submitFeedback({
            userId: 'user-123',
            scanId: 'non-existent',
            scanType: 'text',
            feedbackType: 'confirmed',
          })
        ).rejects.toThrow('Scan not found');
      });

      test('should reject duplicate feedback', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'user-123',
          prediction: 'spam',
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue({ id: 'existing' });

        await expect(
          feedbackService.submitFeedback({
            userId: 'user-123',
            scanId: 'scan-1',
            scanType: 'text',
            feedbackType: 'confirmed',
          })
        ).rejects.toThrow('You have already submitted feedback for this scan');
      });
    });

    describe('Phishing Scan Feedback', () => {
      test('should submit feedback for phishing scan', async () => {
        const mockScan = {
          id: 'phishing-1',
          userId: 'user-123',
          isPhishing: true,
        };
        prisma.phishingScanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue(null);
        prisma.userFeedback.create.mockResolvedValue({
          id: 'feedback-2',
          userId: 'user-123',
          phishingHistoryId: 'phishing-1',
          feedbackType: 'confirmed',
          originalPrediction: 'phishing',
          actualLabel: 'phishing',
          status: 'pending',
        });

        const result = await feedbackService.submitFeedback({
          userId: 'user-123',
          scanId: 'phishing-1',
          scanType: 'phishing',
          feedbackType: 'confirmed',
        });

        expect(result.phishingHistoryId).toBe('phishing-1');
        expect(result.originalPrediction).toBe('phishing');
      });

      test('should reject feedback for non-existent phishing scan', async () => {
        prisma.phishingScanHistory.findUnique.mockResolvedValue(null);

        await expect(
          feedbackService.submitFeedback({
            userId: 'user-123',
            scanId: 'non-existent',
            scanType: 'phishing',
            feedbackType: 'confirmed',
          })
        ).rejects.toThrow('Phishing scan not found');
      });
    });

    describe('Label Inference', () => {
      test('should infer ham for false_positive on spam prediction', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'user-123',
          prediction: 'spam',
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue(null);
        prisma.userFeedback.create.mockResolvedValue({
          id: 'feedback-1',
          actualLabel: 'ham',
        });

        const result = await feedbackService.submitFeedback({
          userId: 'user-123',
          scanId: 'scan-1',
          scanType: 'text',
          feedbackType: 'false_positive',
        });

        expect(prisma.userFeedback.create).toHaveBeenCalledWith({
          data: expect.objectContaining({
            actualLabel: 'ham',
          }),
        });
      });

      test('should infer spam for false_negative on ham prediction', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'user-123',
          prediction: 'ham',
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue(null);
        prisma.userFeedback.create.mockResolvedValue({
          id: 'feedback-1',
          actualLabel: 'spam',
        });

        await feedbackService.submitFeedback({
          userId: 'user-123',
          scanId: 'scan-1',
          scanType: 'text',
          feedbackType: 'false_negative',
        });

        expect(prisma.userFeedback.create).toHaveBeenCalledWith({
          data: expect.objectContaining({
            actualLabel: 'spam',
          }),
        });
      });

      test('should keep original label for confirmed feedback', async () => {
        const mockScan = {
          id: 'scan-1',
          userId: 'user-123',
          prediction: 'spam',
        };
        prisma.scanHistory.findUnique.mockResolvedValue(mockScan);
        prisma.userFeedback.findFirst.mockResolvedValue(null);
        prisma.userFeedback.create.mockResolvedValue({
          id: 'feedback-1',
          actualLabel: 'spam',
        });

        await feedbackService.submitFeedback({
          userId: 'user-123',
          scanId: 'scan-1',
          scanType: 'text',
          feedbackType: 'confirmed',
        });

        expect(prisma.userFeedback.create).toHaveBeenCalledWith({
          data: expect.objectContaining({
            actualLabel: 'spam',
          }),
        });
      });
    });
  });

  describe('getPendingFeedback', () => {
    test('should return paginated pending feedback', async () => {
      const mockFeedback = [
        { id: '1', status: 'pending', scanHistoryId: 'scan-1' },
        { id: '2', status: 'pending', phishingHistoryId: 'phishing-1' },
      ];
      prisma.userFeedback.findMany.mockResolvedValue(mockFeedback);
      prisma.userFeedback.count.mockResolvedValue(10);
      prisma.scanHistory.findUnique.mockResolvedValue({
        message: 'Test',
        isSpam: true,
      });
      prisma.phishingScanHistory.findUnique.mockResolvedValue({
        inputText: 'Phishing text',
        isPhishing: true,
      });

      const result = await feedbackService.getPendingFeedback({
        page: 1,
        limit: 20,
      });

      expect(result.feedback).toHaveLength(2);
      expect(result.pagination.total).toBe(10);
    });

    test('should filter by feedback type', async () => {
      prisma.userFeedback.findMany.mockResolvedValue([]);
      prisma.userFeedback.count.mockResolvedValue(0);

      await feedbackService.getPendingFeedback({
        page: 1,
        limit: 20,
        feedbackType: 'false_positive',
      });

      expect(prisma.userFeedback.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            feedbackType: 'false_positive',
          }),
        })
      );
    });
  });

  describe('reviewFeedback', () => {
    test('should approve pending feedback', async () => {
      prisma.userFeedback.findUnique.mockResolvedValue({
        id: 'feedback-1',
        status: 'pending',
      });
      prisma.userFeedback.update.mockResolvedValue({
        id: 'feedback-1',
        status: 'approved',
      });
      prisma.userFeedback.count.mockResolvedValue(10); // Below threshold

      const result = await feedbackService.reviewFeedback({
        feedbackId: 'feedback-1',
        action: 'approve',
        reviewerId: 'admin-1',
      });

      expect(result.status).toBe('approved');
      expect(prisma.userFeedback.update).toHaveBeenCalledWith({
        where: { id: 'feedback-1' },
        data: expect.objectContaining({
          status: 'approved',
          reviewedBy: 'admin-1',
        }),
      });
    });

    test('should reject pending feedback', async () => {
      prisma.userFeedback.findUnique.mockResolvedValue({
        id: 'feedback-1',
        status: 'pending',
      });
      prisma.userFeedback.update.mockResolvedValue({
        id: 'feedback-1',
        status: 'rejected',
      });

      const result = await feedbackService.reviewFeedback({
        feedbackId: 'feedback-1',
        action: 'reject',
        reviewerId: 'admin-1',
      });

      expect(result.status).toBe('rejected');
    });

    test('should throw error for non-existent feedback', async () => {
      prisma.userFeedback.findUnique.mockResolvedValue(null);

      await expect(
        feedbackService.reviewFeedback({
          feedbackId: 'non-existent',
          action: 'approve',
          reviewerId: 'admin-1',
        })
      ).rejects.toThrow('Feedback not found');
    });

    test('should throw error for already reviewed feedback', async () => {
      prisma.userFeedback.findUnique.mockResolvedValue({
        id: 'feedback-1',
        status: 'approved', // Already reviewed
      });

      await expect(
        feedbackService.reviewFeedback({
          feedbackId: 'feedback-1',
          action: 'approve',
          reviewerId: 'admin-1',
        })
      ).rejects.toThrow('Feedback has already been reviewed');
    });
  });

  describe('getStatistics', () => {
    test('should return comprehensive statistics', async () => {
      prisma.userFeedback.groupBy
        .mockResolvedValueOnce([
          // byStatus
          { status: 'pending', _count: 20 },
          { status: 'approved', _count: 50 },
          { status: 'rejected', _count: 10 },
        ])
        .mockResolvedValueOnce([
          // byType
          { feedbackType: 'false_positive', _count: 30 },
          { feedbackType: 'false_negative', _count: 20 },
          { feedbackType: 'confirmed', _count: 30 },
        ]);

      prisma.userFeedback.count.mockResolvedValue(80);
      prisma.userFeedback.findMany.mockResolvedValue([
        { feedbackType: 'false_positive', originalPrediction: 'spam' },
        { feedbackType: 'false_positive', originalPrediction: 'spam' },
        { feedbackType: 'false_negative', originalPrediction: 'ham' },
      ]);

      const result = await feedbackService.getStatistics();

      expect(result.total).toBe(80);
      expect(result.byStatus.pending).toBe(20);
      expect(result.byStatus.approved).toBe(50);
      expect(result.byType.false_positive).toBe(30);
      expect(result.pendingCount).toBe(20);
      expect(result.approvedCount).toBe(50);
    });
  });

  describe('getUserFeedback', () => {
    test('should return user-specific feedback', async () => {
      const mockFeedback = [
        { id: '1', userId: 'user-123', feedbackType: 'confirmed' },
      ];
      prisma.userFeedback.findMany.mockResolvedValue(mockFeedback);
      prisma.userFeedback.count.mockResolvedValue(5);

      const result = await feedbackService.getUserFeedback({
        userId: 'user-123',
        page: 1,
        limit: 20,
      });

      expect(result.feedback).toHaveLength(1);
      expect(result.pagination.total).toBe(5);
    });
  });

  describe('getFeedbackById', () => {
    test('should return feedback when user owns it', async () => {
      const mockFeedback = {
        id: 'feedback-1',
        userId: 'user-123',
        scanHistoryId: 'scan-1',
      };
      prisma.userFeedback.findUnique.mockResolvedValue(mockFeedback);
      prisma.scanHistory.findUnique.mockResolvedValue({
        message: 'Test',
        isSpam: true,
      });

      const result = await feedbackService.getFeedbackById(
        'feedback-1',
        'user-123',
        false
      );

      expect(result.id).toBe('feedback-1');
      expect(result.scanData).toBeDefined();
    });

    test('should allow admin to view any feedback', async () => {
      const mockFeedback = {
        id: 'feedback-1',
        userId: 'other-user',
        scanHistoryId: 'scan-1',
      };
      prisma.userFeedback.findUnique.mockResolvedValue(mockFeedback);
      prisma.scanHistory.findUnique.mockResolvedValue({ message: 'Test' });

      const result = await feedbackService.getFeedbackById(
        'feedback-1',
        'admin-user',
        true
      );

      expect(result.id).toBe('feedback-1');
    });

    test('should reject non-owner non-admin access', async () => {
      const mockFeedback = {
        id: 'feedback-1',
        userId: 'other-user',
      };
      prisma.userFeedback.findUnique.mockResolvedValue(mockFeedback);

      await expect(
        feedbackService.getFeedbackById('feedback-1', 'user-123', false)
      ).rejects.toThrow('You can only view your own feedback');
    });

    test('should throw not found for non-existent feedback', async () => {
      prisma.userFeedback.findUnique.mockResolvedValue(null);

      await expect(
        feedbackService.getFeedbackById('non-existent', 'user-123', false)
      ).rejects.toThrow('Feedback not found');
    });
  });

  describe('exportApprovedFeedback', () => {
    test('should export approved feedback for training', async () => {
      const mockFeedback = [
        {
          id: 'feedback-1',
          scanHistoryId: 'scan-1',
          originalPrediction: 'spam',
          actualLabel: 'ham',
          feedbackType: 'false_positive',
          createdAt: new Date(),
        },
      ];
      prisma.userFeedback.findMany.mockResolvedValue(mockFeedback);
      prisma.scanHistory.findUnique.mockResolvedValue({
        message: 'Test message',
        scanType: 'text',
      });
      prisma.userFeedback.updateMany.mockResolvedValue({});

      const result = await feedbackService.exportApprovedFeedback({
        format: 'json',
      });

      expect(result.count).toBe(1);
      expect(result.data[0].originalLabel).toBe('spam');
      expect(result.data[0].correctedLabel).toBe('ham');
    });

    test('should export as CSV format', async () => {
      const mockFeedback = [
        {
          id: 'feedback-1',
          scanHistoryId: 'scan-1',
          originalPrediction: 'spam',
          actualLabel: 'ham',
          feedbackType: 'false_positive',
          createdAt: new Date(),
        },
      ];
      prisma.userFeedback.findMany.mockResolvedValue(mockFeedback);
      prisma.scanHistory.findUnique.mockResolvedValue({
        message: 'Test message',
        scanType: 'text',
      });
      prisma.userFeedback.updateMany.mockResolvedValue({});

      const result = await feedbackService.exportApprovedFeedback({
        format: 'csv',
      });

      expect(result.csv).toBeDefined();
      expect(result.csv).toContain('id,text,originalLabel');
    });
  });
});
