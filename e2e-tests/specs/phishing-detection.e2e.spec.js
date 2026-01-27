/**
 * E2E Tests: Phishing Detection Flow
 * Tests the complete phishing detection workflow across all system components
 */

const config = require('../config/e2e.config');

describe('E2E: Phishing Detection Flow', () => {
  const env = config.environments[process.env.E2E_ENV || 'local'];
  let authToken;

  beforeAll(async () => {
    // Verify services are healthy
    await verifyServiceHealth(env.backend);
    await verifyServiceHealth(env.mlService);

    // Authenticate test user
    authToken = await authenticateUser(config.testUsers.regularUser);
  });

  describe('Text Phishing Detection', () => {
    test('should detect phishing email content', async () => {
      const phishingMessage = config.testMessages.phishing[0];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: phishingMessage }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.status).toBe('success');
      expect(result.data.is_phishing).toBe(true);
      expect(result.data.confidence).toBeGreaterThan(0.65);
      expect(['HIGH', 'CRITICAL']).toContain(result.data.threat_level);
    }, config.timeouts.medium);

    test('should identify safe email content', async () => {
      const safeMessage = config.testMessages.safe[0];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: safeMessage }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(false);
      expect(result.data.is_safe).toBe(true);
      expect(result.data.threat_level).toBe('NONE');
    }, config.timeouts.medium);

    test('should detect brand impersonation', async () => {
      const brandPhishing = 'Dear PayPal customer, your account has been suspended. Verify at http://paypa1-secure.com';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: brandPhishing }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(true);
      if (result.data.brand_impersonation) {
        expect(result.data.brand_impersonation.detected).toBe(true);
      }
    }, config.timeouts.medium);

    test('should analyze embedded URLs', async () => {
      const messageWithUrl = 'Click here to verify your account: http://suspicious-site.com/login';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: messageWithUrl }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.urls_analyzed).toBeDefined();
      if (result.data.urls_analyzed.length > 0) {
        expect(result.data.urls_analyzed[0].url).toBeDefined();
        expect(result.data.urls_analyzed[0].is_suspicious).toBeDefined();
      }
    }, config.timeouts.medium);
  });

  describe('URL Phishing Detection', () => {
    test('should detect phishing URL', async () => {
      if (!config.features.urlScan) {
        return;
      }

      const phishingUrl = 'http://paypa1-secure-login.com/verify';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ url: phishingUrl }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(true);
      expect(result.data.phishing_type).toBe('URL');
    }, config.timeouts.medium);

    test('should identify safe URL', async () => {
      if (!config.features.urlScan) {
        return;
      }

      const safeUrl = 'https://www.google.com';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ url: safeUrl }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(false);
    }, config.timeouts.medium);

    test('should detect typosquatting domains', async () => {
      if (!config.features.urlScan) {
        return;
      }

      const typosquatUrl = 'http://amaz0n-secure.com/account';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ url: typosquatUrl }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(true);
      // Should detect this as potential typosquatting
    }, config.timeouts.medium);
  });

  describe('SMS Phishing (Smishing) Detection', () => {
    test('should detect smishing message', async () => {
      const smishingMessage = 'URGENT: Your bank account is locked. Reply with PIN to unlock. -BankOfAmerica';

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          text: smishingMessage,
          scan_type: 'sms',
        }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.is_phishing).toBe(true);
    }, config.timeouts.medium);
  });

  describe('Phishing History Management', () => {
    test('should save and retrieve phishing scan history', async () => {
      // First, perform a scan
      await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: 'Test phishing scan for history' }),
      });

      // Retrieve history
      const historyResponse = await fetch(`${env.backend.baseUrl}/api/v1/phishing/history`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const historyResult = await historyResponse.json();

      expect(historyResponse.status).toBe(200);
      expect(historyResult.data.histories).toBeDefined();
    }, config.timeouts.medium);

    test('should filter history by threat level', async () => {
      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/phishing/history?threatLevel=HIGH`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      const result = await response.json();

      expect(response.status).toBe(200);
      // All returned items should have HIGH threat level
      result.data.histories.forEach(item => {
        expect(['HIGH', 'CRITICAL']).toContain(item.threatLevel);
      });
    }, config.timeouts.short);

    test('should delete phishing history item', async () => {
      // First, create a history item
      await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ text: 'Test for deletion' }),
      });

      // Get history to find the item
      const historyResponse = await fetch(`${env.backend.baseUrl}/api/v1/phishing/history`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      const historyResult = await historyResponse.json();

      if (historyResult.data.histories.length > 0) {
        const itemId = historyResult.data.histories[0].id;

        // Delete the item
        const deleteResponse = await fetch(
          `${env.backend.baseUrl}/api/v1/phishing/history/${itemId}`,
          {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
          }
        );

        expect(deleteResponse.status).toBe(200);
      }
    }, config.timeouts.medium);
  });

  describe('Phishing Statistics', () => {
    test('should return phishing statistics', async () => {
      if (!config.features.statistics) {
        return;
      }

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/stats`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.totalScans).toBeDefined();
      expect(result.data.phishingDetected).toBeDefined();
      expect(result.data.safeScans).toBeDefined();
    }, config.timeouts.short);
  });

  describe('Batch Phishing Detection', () => {
    test('should scan multiple texts for phishing', async () => {
      if (!config.features.batchScan) {
        return;
      }

      const texts = [
        config.testMessages.safe[0],
        config.testMessages.phishing[0],
        config.testMessages.safe[1],
      ];

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ texts }),
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.results).toHaveLength(3);
      expect(result.data.summary.total).toBe(3);
      expect(result.data.summary.phishing_detected).toBeGreaterThan(0);
    }, config.timeouts.long);
  });

  describe('Error Handling', () => {
    test('should handle empty text', async () => {
      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: '' }),
      });

      expect(response.status).toBe(400);
    }, config.timeouts.short);

    test('should handle invalid URL format', async () => {
      if (!config.features.urlScan) {
        return;
      }

      const response = await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: 'not-a-valid-url' }),
      });

      expect(response.status).toBe(400);
    }, config.timeouts.short);
  });

  describe('Performance Tests', () => {
    test('phishing scan should complete within threshold', async () => {
      const startTime = Date.now();

      await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: config.testMessages.safe[0] }),
      });

      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(config.performance.maxResponseTime.textScan);
    }, config.timeouts.medium);

    test('URL scan should complete within threshold', async () => {
      if (!config.features.urlScan) {
        return;
      }

      const startTime = Date.now();

      await fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: 'https://www.google.com' }),
      });

      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(config.performance.maxResponseTime.urlScan);
    }, config.timeouts.medium);
  });

  describe('Concurrent Scans', () => {
    test('should handle multiple concurrent requests', async () => {
      const texts = Array(10).fill(config.testMessages.safe[0]);

      const promises = texts.map(text =>
        fetch(`${env.backend.baseUrl}/api/v1/phishing/scan-text`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text }),
        })
      );

      const responses = await Promise.all(promises);

      responses.forEach(response => {
        expect(response.status).toBe(200);
      });
    }, config.timeouts.veryLong);
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
    return 'e2e-test-token';
  }

  const result = await response.json();
  return result.data.accessToken;
}
