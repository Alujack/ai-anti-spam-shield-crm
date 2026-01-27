/**
 * Jest Setup for E2E Tests
 * Global configuration and utilities for end-to-end testing
 */

// Set default timeout for all tests
jest.setTimeout(60000);

// Global test utilities
global.sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Retry utility for flaky operations
global.retry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await global.sleep(delay);
      }
    }
  }
  throw lastError;
};

// Console setup
beforeAll(() => {
  console.log('\n=== E2E Tests Starting ===');
  console.log(`Environment: ${process.env.E2E_ENV || 'local'}`);
  console.log(`Time: ${new Date().toISOString()}\n`);
});

afterAll(() => {
  console.log('\n=== E2E Tests Complete ===\n');
});

// Error handling
process.on('unhandledRejection', (error) => {
  console.error('Unhandled Promise Rejection:', error);
});
