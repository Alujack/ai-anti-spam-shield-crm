/**
 * E2E Tests: Report Submission and Management Flow
 * Tests the complete report workflow from submission to review
 */

const config = require('../config/e2e.config');

describe('E2E: Report Submission and Management Flow', () => {
  const env = config.environments[process.env.E2E_ENV || 'local'];
  let userToken;
  let adminToken;

  beforeAll(async () => {
    // Verify services are healthy
    await verifyServiceHealth(env.backend);

    // Authenticate users
    userToken = await authenticateUser(config.testUsers.regularUser);
    adminToken = await authenticateUser(config.testUsers.adminUser);
  });

  describe('Report Submission', () => {
    test('should submit spam report successfully', async () => {
      if (!config.features.reporting) {
        return;
      }

      const reportData = {
        messageText: 'URGENT: You won $10,000! Claim now!',
        reportType: 'SPAM',
        description: 'This message appears to be spam promising money',
      };

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify(reportData),
      });

      const result = await response.json();

      expect(response.status).toBe(201);
      expect(result.status).toBe('success');
      expect(result.data.id).toBeDefined();
      expect(result.data.type).toBe('spam');
      expect(result.data.status).toBe('PENDING');
    }, config.timeouts.medium);

    test('should submit phishing report with URL', async () => {
      if (!config.features.reporting) {
        return;
      }

      const reportData = {
        messageText: 'Your account has been suspended. Verify at http://fake-bank.com',
        reportType: 'PHISHING',
        description: 'Email claiming to be from my bank',
        url: 'http://fake-bank.com',
        phoneNumber: '+1234567890',
      };

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify(reportData),
      });

      const result = await response.json();

      expect(response.status).toBe(201);
      expect(result.data.type).toBe('phishing');
    }, config.timeouts.medium);

    test('should submit scam report', async () => {
      if (!config.features.reporting) {
        return;
      }

      const reportData = {
        messageText: 'You owe taxes. Pay immediately or face arrest.',
        reportType: 'SCAM',
        description: 'Phone call claiming to be from IRS',
        phoneNumber: '+1-800-FAKE-IRS',
      };

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify(reportData),
      });

      const result = await response.json();

      expect(response.status).toBe(201);
      expect(result.data.type).toBe('scam');
    }, config.timeouts.medium);

    test('should reject invalid report type', async () => {
      if (!config.features.reporting) {
        return;
      }

      const reportData = {
        messageText: 'Test message',
        reportType: 'INVALID_TYPE',
        description: 'Test description',
      };

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify(reportData),
      });

      expect(response.status).toBe(400);
    }, config.timeouts.short);

    test('should require authentication', async () => {
      if (!config.features.reporting) {
        return;
      }

      const reportData = {
        messageText: 'Test message',
        reportType: 'SPAM',
        description: 'Test description',
      };

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      });

      expect(response.status).toBe(401);
    }, config.timeouts.short);
  });

  describe('Report Retrieval', () => {
    test('should get user reports', async () => {
      if (!config.features.reporting) {
        return;
      }

      const response = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        headers: {
          'Authorization': `Bearer ${userToken}`,
        },
      });

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.reports).toBeDefined();
      expect(result.data.pagination).toBeDefined();
    }, config.timeouts.short);

    test('should filter reports by status', async () => {
      if (!config.features.reporting) {
        return;
      }

      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/reports?status=PENDING`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      const result = await response.json();

      expect(response.status).toBe(200);
      result.data.reports.forEach(report => {
        expect(report.status).toBe('PENDING');
      });
    }, config.timeouts.short);

    test('should get report by ID', async () => {
      if (!config.features.reporting) {
        return;
      }

      // First create a report
      const createResponse = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          messageText: 'Test for retrieval',
          reportType: 'SPAM',
          description: 'Test description',
        }),
      });

      const createResult = await createResponse.json();
      const reportId = createResult.data.id;

      // Get the report by ID
      const getResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      const getResult = await getResponse.json();

      expect(getResponse.status).toBe(200);
      expect(getResult.data.id).toBe(reportId);
    }, config.timeouts.medium);

    test('should return 404 for non-existent report', async () => {
      if (!config.features.reporting) {
        return;
      }

      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/non-existent-id`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      expect(response.status).toBe(404);
    }, config.timeouts.short);
  });

  describe('Report Status Updates (Admin)', () => {
    test('admin should update report status to REVIEWED', async () => {
      if (!config.features.reporting) {
        return;
      }

      // Create a report first
      const createResponse = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          messageText: 'Test for status update',
          reportType: 'SPAM',
          description: 'Test description',
        }),
      });

      const createResult = await createResponse.json();
      const reportId = createResult.data.id;

      // Update status as admin
      const updateResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`,
          },
          body: JSON.stringify({ status: 'REVIEWED' }),
        }
      );

      const updateResult = await updateResponse.json();

      expect(updateResponse.status).toBe(200);
      expect(updateResult.data.status).toBe('REVIEWED');
    }, config.timeouts.medium);

    test('admin should update report status to RESOLVED', async () => {
      if (!config.features.reporting) {
        return;
      }

      // Create a report first
      const createResponse = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          messageText: 'Test for resolve',
          reportType: 'PHISHING',
          description: 'Test description',
        }),
      });

      const createResult = await createResponse.json();
      const reportId = createResult.data.id;

      // Resolve as admin
      const updateResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`,
          },
          body: JSON.stringify({ status: 'RESOLVED' }),
        }
      );

      expect(updateResponse.status).toBe(200);
    }, config.timeouts.medium);

    test('regular user should not update report status', async () => {
      if (!config.features.reporting) {
        return;
      }

      // Create a report first
      const createResponse = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          messageText: 'Test unauthorized update',
          reportType: 'SPAM',
          description: 'Test description',
        }),
      });

      const createResult = await createResponse.json();
      const reportId = createResult.data.id;

      // Try to update as regular user
      const updateResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`,
          },
          body: JSON.stringify({ status: 'RESOLVED' }),
        }
      );

      expect(updateResponse.status).toBe(403);
    }, config.timeouts.medium);
  });

  describe('Report Deletion', () => {
    test('user should delete own report', async () => {
      if (!config.features.reporting) {
        return;
      }

      // Create a report first
      const createResponse = await fetch(`${env.backend.baseUrl}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          messageText: 'Test for deletion',
          reportType: 'SPAM',
          description: 'Test description',
        }),
      });

      const createResult = await createResponse.json();
      const reportId = createResult.data.id;

      // Delete the report
      const deleteResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      expect(deleteResponse.status).toBe(200);

      // Verify it's deleted
      const getResponse = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/${reportId}`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      expect(getResponse.status).toBe(404);
    }, config.timeouts.medium);
  });

  describe('Report Statistics', () => {
    test('should get report statistics', async () => {
      if (!config.features.reporting || !config.features.statistics) {
        return;
      }

      const response = await fetch(
        `${env.backend.baseUrl}/api/v1/reports/stats/summary`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.data.total).toBeDefined();
      expect(result.data.pending).toBeDefined();
      expect(result.data.byType).toBeDefined();
    }, config.timeouts.short);
  });

  describe('Report Pagination', () => {
    test('should paginate reports correctly', async () => {
      if (!config.features.reporting) {
        return;
      }

      // Get first page
      const page1Response = await fetch(
        `${env.backend.baseUrl}/api/v1/reports?page=1&limit=5`,
        {
          headers: {
            'Authorization': `Bearer ${userToken}`,
          },
        }
      );

      const page1Result = await page1Response.json();

      expect(page1Response.status).toBe(200);
      expect(page1Result.data.pagination.page).toBe(1);
      expect(page1Result.data.pagination.limit).toBe(5);
    }, config.timeouts.short);
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
    // For admin, return admin token; for regular user, return user token
    return user.role === 'ADMIN' ? 'e2e-admin-token' : 'e2e-user-token';
  }

  const result = await response.json();
  return result.data.accessToken;
}
