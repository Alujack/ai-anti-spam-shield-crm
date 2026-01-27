/**
 * E2E Test Configuration
 * Configuration for end-to-end testing across all system components
 */

module.exports = {
  // Environment settings
  environments: {
    local: {
      backend: {
        baseUrl: 'http://localhost:3000',
        healthCheck: '/api/v1/health',
        timeout: 30000,
      },
      mlService: {
        baseUrl: 'http://localhost:8000',
        healthCheck: '/health',
        timeout: 60000, // ML predictions may take longer
      },
      database: {
        host: 'localhost',
        port: 5432,
        name: 'anti_spam_shield_test',
      },
      redis: {
        host: 'localhost',
        port: 6379,
      },
    },
    staging: {
      backend: {
        baseUrl: process.env.STAGING_BACKEND_URL || 'https://staging-api.anti-spam-shield.com',
        healthCheck: '/api/v1/health',
        timeout: 30000,
      },
      mlService: {
        baseUrl: process.env.STAGING_ML_URL || 'https://staging-ml.anti-spam-shield.com',
        healthCheck: '/health',
        timeout: 60000,
      },
    },
    production: {
      backend: {
        baseUrl: process.env.PROD_BACKEND_URL || 'https://api.anti-spam-shield.com',
        healthCheck: '/api/v1/health',
        timeout: 30000,
      },
      mlService: {
        baseUrl: process.env.PROD_ML_URL || 'https://ml.anti-spam-shield.com',
        healthCheck: '/health',
        timeout: 60000,
      },
    },
  },

  // Test user credentials for E2E testing
  testUsers: {
    regularUser: {
      email: 'e2e-user@test.com',
      password: 'E2ETestPassword123!',
      role: 'USER',
    },
    adminUser: {
      email: 'e2e-admin@test.com',
      password: 'E2EAdminPassword123!',
      role: 'ADMIN',
    },
  },

  // Test data for spam/phishing detection
  testMessages: {
    safe: [
      'Hello, how are you doing today?',
      'Meeting tomorrow at 3pm in the conference room.',
      'Thanks for your help with the project!',
      'Can you send me the document when you have time?',
    ],
    spam: [
      'URGENT: You won $10,000! Click here to claim NOW!',
      'Congratulations! You have been selected for a special offer!',
      'LIMITED TIME ONLY: Get rich quick with this amazing opportunity!',
      'FREE iPhone! Just enter your credit card details!',
    ],
    phishing: [
      'Your PayPal account has been suspended. Click here to verify: http://paypa1-secure.com',
      'Dear customer, your bank account requires immediate verification.',
      'Your Netflix subscription is expiring. Update payment: http://netf1ix-billing.com',
      'Apple ID locked. Verify immediately: http://app1e-support.com/verify',
    ],
  },

  // Timeouts and retries
  timeouts: {
    short: 5000,
    medium: 15000,
    long: 30000,
    veryLong: 60000,
  },

  retries: {
    max: 3,
    delay: 1000, // ms between retries
  },

  // Reporter configuration
  reporters: {
    console: {
      enabled: true,
      verbose: true,
    },
    html: {
      enabled: true,
      outputDir: './e2e-tests/reports',
      filename: 'e2e-report.html',
    },
    json: {
      enabled: true,
      outputDir: './e2e-tests/reports',
      filename: 'e2e-results.json',
    },
    junit: {
      enabled: true,
      outputDir: './e2e-tests/reports',
      filename: 'e2e-junit.xml',
    },
  },

  // Screenshot and video capture (for UI tests)
  capture: {
    screenshots: {
      enabled: true,
      onFailure: true,
      onSuccess: false,
      directory: './e2e-tests/screenshots',
    },
    videos: {
      enabled: false,
      directory: './e2e-tests/videos',
    },
  },

  // Parallel execution settings
  parallel: {
    enabled: true,
    workers: 4, // Number of parallel workers
  },

  // Test categories/tags
  tags: {
    smoke: ['@smoke'],
    regression: ['@regression'],
    critical: ['@critical'],
    security: ['@security'],
    performance: ['@performance'],
  },

  // Feature flags for conditional testing
  features: {
    voiceScan: true,
    urlScan: true,
    batchScan: true,
    reporting: true,
    feedback: true,
    statistics: true,
  },

  // Performance thresholds
  performance: {
    maxResponseTime: {
      textScan: 2000, // ms
      voiceScan: 5000, // ms
      urlScan: 3000, // ms
      batchScan: 10000, // ms
    },
    minThroughput: {
      scansPerMinute: 60,
    },
  },

  // Security test configuration
  security: {
    testXSS: true,
    testSQLInjection: true,
    testCSRF: true,
    testRateLimiting: true,
    rateLimitThreshold: 100, // requests per minute
  },
};
