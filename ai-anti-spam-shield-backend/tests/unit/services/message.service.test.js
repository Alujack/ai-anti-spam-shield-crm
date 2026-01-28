/**
 * Unit Tests for Message Service
 * Tests spam/scam detection functionality
 */

const axios = require('axios');

// Mock dependencies before requiring the service
jest.mock('axios');
jest.mock('../../../src/config/database', () => ({
  scanHistory: {
    create: jest.fn(),
    findMany: jest.fn(),
    findFirst: jest.fn(),
    count: jest.fn(),
    delete: jest.fn(),
  },
}));
jest.mock('../../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
}));
jest.mock('../../../src/config', () => ({
  ai: {
    serviceUrl: 'http://localhost:8000',
    apiKey: 'test-api-key',
  },
}));

const messageService = require('../../../src/services/message.service');
const prisma = require('../../../src/config/database');

describe('MessageService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('scanTextForSpam', () => {
    describe('Safe Greeting Detection', () => {
      const safeGreetings = [
        'Hi',
        'Hello',
        'Hey',
        'Hi there',
        'Hello friend',
        'Hey everyone',
        'How are you',
        'How are you today',
        'How are you my friend',
        "How's it going",
        "What's up",
        'Good morning',
        'Good afternoon',
        'Good evening',
        'Greetings',
        'Yo',
        'Sup',
        'Howdy',
        'Nice to meet you',
        'How have you been',
        'Long time no see',
      ];

      test.each(safeGreetings)(
        'should mark "%s" as safe without calling AI service',
        async (greeting) => {
          const result = await messageService.scanTextForSpam(greeting);

          expect(result.is_spam).toBe(false);
          expect(result.confidence).toBe(0.95);
          expect(result.is_safe).toBe(true);
          expect(result.risk_level).toBe('NONE');
          expect(result.details.bypass_reason).toBe('safe_greeting_pattern');
          expect(axios.post).not.toHaveBeenCalled();
        }
      );

      test('should save history for safe greeting when userId provided', async () => {
        prisma.scanHistory.create.mockResolvedValue({ id: 'test-id' });

        await messageService.scanTextForSpam('Hello', 'user-123');

        expect(prisma.scanHistory.create).toHaveBeenCalledWith({
          data: expect.objectContaining({
            userId: 'user-123',
            message: 'Hello',
            isSpam: false,
          }),
        });
      });
    });

    describe('Spam Detection', () => {
      test('should detect spam when AI confidence exceeds threshold (0.80)', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.85,
            prediction: 'spam',
            details: {
              features: {
                has_url: true,
                urgency_words: true,
              },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'URGENT! You have won $1,000,000! Click here: http://scam.com'
        );

        expect(result.is_spam).toBe(true);
        expect(result.confidence).toBe(0.85);
        expect(result.risk_level).toBe('HIGH');
        expect(result.danger_causes.length).toBeGreaterThan(0);
        expect(result.confidence_label).toBe('Spam Confidence');
      });

      test('should mark as safe when AI confidence is below threshold', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.30,
            prediction: 'ham',
          },
        });

        const result = await messageService.scanTextForSpam(
          'Meeting tomorrow at 3pm in conference room A'
        );

        expect(result.is_spam).toBe(false);
        expect(result.confidence).toBe(0.70); // 1 - 0.30
        expect(result.is_safe).toBe(true);
        expect(result.risk_level).toBe('NONE');
        expect(result.confidence_label).toBe('Safety Confidence');
      });

      test('should classify CRITICAL risk for confidence >= 0.90', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.95,
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam('Test spam message');

        expect(result.risk_level).toBe('CRITICAL');
      });

      test('should classify HIGH risk for confidence >= 0.85 and < 0.90', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.87,
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam('Test spam message');

        expect(result.risk_level).toBe('HIGH');
      });

      test('should classify MEDIUM risk for confidence >= 0.80 and < 0.85', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.82,
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam('Test spam message');

        expect(result.risk_level).toBe('MEDIUM');
      });
    });

    describe('Short Message Handling', () => {
      test('should apply 40% penalty to short messages (< 3 words)', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.75, // Would normally be below threshold
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam('ok thanks'); // 2 words

        // 0.75 * 0.6 = 0.45 (below 0.80 threshold)
        expect(result.is_spam).toBe(false);
        expect(result.short_message_penalty_applied).toBe(true);
      });

      test('should not apply penalty to long messages', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.85,
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam(
          'This is a longer message with multiple words for testing'
        );

        expect(result.is_spam).toBe(true);
        expect(result.short_message_penalty_applied).toBeUndefined();
      });

      test('should not apply penalty when confidence is very high (>= 0.90)', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.95,
            prediction: 'spam',
          },
        });

        const result = await messageService.scanTextForSpam('ok'); // 1 word

        expect(result.is_spam).toBe(true);
        expect(result.confidence).toBe(0.95);
      });
    });

    describe('Feature-based Danger Causes', () => {
      test('should add URL warning when message contains URLs', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.85,
            prediction: 'spam',
            details: {
              features: { has_url: true },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'Click this link http://suspicious.com'
        );

        const urlCause = result.danger_causes.find(
          (c) => c.type === 'contains_url'
        );
        expect(urlCause).toBeDefined();
        expect(urlCause.title).toBe('Contains External Links');
      });

      test('should add urgency warning when message uses urgent language', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.88,
            prediction: 'spam',
            details: {
              features: { urgency_words: true },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'ACT NOW! Limited time offer!'
        );

        const urgencyCause = result.danger_causes.find(
          (c) => c.type === 'urgency_language'
        );
        expect(urgencyCause).toBeDefined();
        expect(urgencyCause.severity).toBe('high');
      });

      test('should add spam keywords warning', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.90,
            prediction: 'spam',
            details: {
              features: { spam_keywords: true },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'Congratulations! You have won a prize!'
        );

        const keywordCause = result.danger_causes.find(
          (c) => c.type === 'spam_keywords'
        );
        expect(keywordCause).toBeDefined();
      });

      test('should add money reference warning', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.86,
            prediction: 'spam',
            details: {
              features: { currency_symbols: true },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'Transfer $5000 to this account'
        );

        const moneyCause = result.danger_causes.find(
          (c) => c.type === 'money_reference'
        );
        expect(moneyCause).toBeDefined();
      });

      test('should add phone number warning', async () => {
        axios.post.mockResolvedValue({
          data: {
            confidence: 0.84,
            prediction: 'spam',
            details: {
              features: { has_phone: true },
            },
          },
        });

        const result = await messageService.scanTextForSpam(
          'Call us at 1-800-SCAM-NOW'
        );

        const phoneCause = result.danger_causes.find(
          (c) => c.type === 'phone_number'
        );
        expect(phoneCause).toBeDefined();
      });
    });

    describe('Error Handling', () => {
      test('should handle AI service connection refused', async () => {
        const error = new Error('Connection refused');
        error.code = 'ECONNREFUSED';
        axios.post.mockRejectedValue(error);

        await expect(
          messageService.scanTextForSpam('Test message')
        ).rejects.toThrow('AI service is unavailable');
      });

      test('should handle AI service timeout', async () => {
        const error = new Error('Timeout');
        error.code = 'ETIMEDOUT';
        axios.post.mockRejectedValue(error);

        await expect(
          messageService.scanTextForSpam('Test message')
        ).rejects.toThrow('AI service request timed out');
      });

      test('should handle AI service 503 error', async () => {
        axios.post.mockRejectedValue({
          response: {
            status: 503,
            data: { message: 'Service unavailable' },
          },
        });

        await expect(
          messageService.scanTextForSpam('Test message')
        ).rejects.toThrow('AI service is temporarily unavailable');
      });

      test('should handle AI service 400 error', async () => {
        axios.post.mockRejectedValue({
          response: {
            status: 400,
            data: { message: 'Invalid request' },
          },
        });

        await expect(
          messageService.scanTextForSpam('Test message')
        ).rejects.toThrow('AI service error: Invalid request');
      });
    });

    describe('History Saving', () => {
      test('should save to history when userId is provided', async () => {
        axios.post.mockResolvedValue({
          data: { confidence: 0.85, prediction: 'spam' },
        });
        prisma.scanHistory.create.mockResolvedValue({ id: 'history-1' });

        // Use a longer message to avoid short message penalty
        await messageService.scanTextForSpam('This is a longer spam message for testing', 'user-123');

        expect(prisma.scanHistory.create).toHaveBeenCalledWith({
          data: expect.objectContaining({
            userId: 'user-123',
            isSpam: true,
            scanType: 'text',
          }),
        });
      });

      test('should not fail if history save fails', async () => {
        axios.post.mockResolvedValue({
          data: { confidence: 0.85, prediction: 'spam' },
        });
        prisma.scanHistory.create.mockRejectedValue(new Error('DB error'));

        // Should not throw - use longer message to avoid short message penalty
        const result = await messageService.scanTextForSpam(
          'This is a longer spam message for testing',
          'user-123'
        );
        expect(result.is_spam).toBe(true);
      });
    });
  });

  describe('getScanHistory', () => {
    test('should return paginated history', async () => {
      const mockHistories = [
        { id: '1', message: 'Test 1', isSpam: true },
        { id: '2', message: 'Test 2', isSpam: false },
      ];
      prisma.scanHistory.findMany.mockResolvedValue(mockHistories);
      prisma.scanHistory.count.mockResolvedValue(10);

      const result = await messageService.getScanHistory('user-123', {
        page: 1,
        limit: 20,
      });

      expect(result.histories).toHaveLength(2);
      expect(result.pagination.total).toBe(10);
      expect(result.pagination.totalPages).toBe(1);
    });

    test('should filter by spam status', async () => {
      prisma.scanHistory.findMany.mockResolvedValue([]);
      prisma.scanHistory.count.mockResolvedValue(0);

      await messageService.getScanHistory('user-123', { isSpam: true });

      expect(prisma.scanHistory.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            isSpam: true,
          }),
        })
      );
    });
  });

  describe('getScanHistoryById', () => {
    test('should return history item when found', async () => {
      const mockHistory = { id: '1', message: 'Test', userId: 'user-123' };
      prisma.scanHistory.findFirst.mockResolvedValue(mockHistory);

      const result = await messageService.getScanHistoryById('1', 'user-123');

      expect(result).toEqual(mockHistory);
    });

    test('should throw not found error when history not found', async () => {
      prisma.scanHistory.findFirst.mockResolvedValue(null);

      await expect(
        messageService.getScanHistoryById('1', 'user-123')
      ).rejects.toThrow('Scan history not found');
    });
  });

  describe('deleteScanHistory', () => {
    test('should delete history when found', async () => {
      prisma.scanHistory.findFirst.mockResolvedValue({
        id: '1',
        userId: 'user-123',
      });
      prisma.scanHistory.delete.mockResolvedValue({});

      const result = await messageService.deleteScanHistory('1', 'user-123');

      expect(result.message).toBe('Scan history deleted successfully');
      expect(prisma.scanHistory.delete).toHaveBeenCalledWith({
        where: { id: '1' },
      });
    });

    test('should throw not found error when history not found', async () => {
      prisma.scanHistory.findFirst.mockResolvedValue(null);

      await expect(
        messageService.deleteScanHistory('1', 'user-123')
      ).rejects.toThrow('Scan history not found');
    });
  });

  describe('getScanStatistics', () => {
    test('should return correct statistics', async () => {
      prisma.scanHistory.count
        .mockResolvedValueOnce(100) // totalScans
        .mockResolvedValueOnce(30) // spamCount
        .mockResolvedValueOnce(70) // hamCount
        .mockResolvedValueOnce(20) // voiceScans
        .mockResolvedValueOnce(80); // textScans

      const result = await messageService.getScanStatistics('user-123');

      expect(result.totalScans).toBe(100);
      expect(result.spamCount).toBe(30);
      expect(result.spamDetected).toBe(30);
      expect(result.hamCount).toBe(70);
      expect(result.safeMessages).toBe(70);
      expect(result.voiceScans).toBe(20);
      expect(result.textScans).toBe(80);
      expect(result.spamPercentage).toBe('30.00');
    });

    test('should handle zero scans', async () => {
      prisma.scanHistory.count.mockResolvedValue(0);

      const result = await messageService.getScanStatistics('user-123');

      expect(result.totalScans).toBe(0);
      expect(result.spamPercentage).toBe(0);
    });
  });
});
