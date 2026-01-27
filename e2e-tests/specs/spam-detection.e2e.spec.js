/**
 * E2E Tests: Spam Detection Flow
 * Tests the complete spam detection workflow from user input to result display
 */

const config = require('../config/e2e.config');

describe('E2E: Spam Detection Flow', () => {
  const env = config.environments[process.env.E2E_ENV || 'local'];
  let authToken;

  beforeAll(async () => {
    // Verify services are healthy
    await verifyServiceHealth(env.backend);
    await verifyServiceHealth(env.mlService);

    // Authenticate test user
    authToken = await authenticateUser(config.testUsers.regularUser);
  });

  describe('Text Spam Scanning', () => {
    test('should detect spam message and return high risk result', async () => {
      const spamMessage = config.testMessages.spam[0];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ message: spamMessage }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.status).toBe('success');
      expect(result.data.is_spam).toBe(true);
      expect(result.data.confidence).toBeGreaterThan(0.7);
      expect(['HIGH', 'CRITICAL']).toContain(result.data.risk_level);
      expect(result.data.danger_causes).toBeDefined();
      expect(result.data.danger_causes.length).toBeGreaterThan(0);
    }, config.timeouts.medium);

    test('should identify safe message correctly', async () => {
      const safeMessage = config.testMessages.safe[0];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ message: safeMessage }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_spam).toBe(false);
      expect(result.data.is_safe).toBe(true);
      expect(result.data.risk_level).toBe('NONE');
    }, config.timeouts.medium);

    test('should work without authentication (anonymous scan)', async () => {
      const message = config.testMessages.safe[1];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.status).toBe('success');
    }, config.timeouts.medium);

    test('should save scan history for authenticated users', async () => {
      const message = 'Test message for history check';

      await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ message }),
      });

      const historyResponse = await fetch(`${env.backend.baseUrl}/api/v1/messages/history`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const historyResult = await historyResponse.json();

      expect(historyResponse.status).toBe(200);
      expect(historyResult.data.histories.length).toBeGreaterThan(0);
    }, config.timeouts.medium);

    test('should apply short message penalty correctly', async () => {
      const shortMessage = 'ok thanks'; // Very short message

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: shortMessage }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      // Short messages should have penalty applied
      expect(result.data.is_spam).toBe(false);
    }, config.timeouts.medium);
  });

  describe('Batch Spam Scanning', () => {
    test('should scan multiple messages in batch', async () => {
      if (!config.features.batchScan) {
        return;
      }

      const messages = [
        config.testMessages.safe[0],
        config.testMessages.spam[0],
        config.testMessages.safe[1],
      ];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ messages }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.results).toHaveLength(3);
      expect(result.data.summary.total).toBe(3);
    }, config.timeouts.long);
  });

  describe('Scan History Management', () => {
    test('should return paginated history', async () => {
      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/messages/history?page=1&limit=10`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.histories).toBeDefined();
      expect(result.data.pagination).toBeDefined();
      expect(result.data.pagination.page).toBe(1);
    }, config.timeouts.short);

    test('should filter history by spam status', async () => {
      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/messages/history?isSpam=true`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      const result = await response.json();

      expect(response.status).toBe(200);
      // All returned items should be spam
      result.data.histories.forEach(item => {
        expect(item.isSpam).toBe(true);
      });
    }, config.timeouts.short);

    test('should delete history item', async () => {
      // First, create a history item
      await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ message: 'Test for deletion' }),
      });

      // Get history to find the item
      const historyResponse = await fetch(`${env.backend.baseUrl}/api/v1/messages/history`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      const historyResult = await historyResponse.json();
      const itemId = historyResult.data.histories[0].id;

      // Delete the item
      const deleteResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/messages/history/${itemId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      expect(deleteResponse.status).toBe(200);
    }, config.timeouts.medium);
  });

  describe('User Statistics', () => {
    test('should return user scan statistics', async () => {
      if (!config.features.statistics) {
        return;
      }

      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/stats`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.totalScans).toBeDefined();
      expect(result.data.spamDetected).toBeDefined();
      expect(result.data.safeMessages).toBeDefined();
    }, config.timeouts.short);
  });

  describe('Error Handling', () => {
    test('should handle empty message', async () => {
      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: '' }),
      });

      expect(response.status).toBe(400);
    }, config.timeouts.short);

    test('should handle missing message field', async () => {
      const response = await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      expect(response.status).toBe(400);
    }, config.timeouts.short);
  });

  describe('Performance Tests', () => {
    test('text scan should complete within threshold', async () => {
      const startTime = Date.now();

      await fetch(`${env.backend.baseUrl}/api/v1/messages/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: config.testMessages.safe[0] }),
      });

      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(config.performance.maxResponseTime.textScan);
    }, config.timeouts.medium);
  });
});

// Helper functions
async function verifyServiceHealth(service) {
  const response = await fetch(`${service.baseUrl}${service.healthCheck}`);
  if (!response.ok) {
    throw new Error(`Service unhealthy: ${service.baseUrl}`);
  }
}

async function authenticateUser(user) {
  const response = await fetch(`${config.environments.local.backend.baseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: user.email,
      password: user.password,
    }),
  });

  if (!response.ok) {
    // For testing, return a mock token if auth fails
    return 'e2e-test-token';
  }

  const result = await response.json();
  return result.data.accessToken;
}
