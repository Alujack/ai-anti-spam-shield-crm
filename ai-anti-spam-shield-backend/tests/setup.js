/**
 * Global test setup for Jest
 */

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-jwt-secret-key-for-testing';
process.env.JWT_REFRESH_SECRET = 'test-jwt-refresh-secret-key';
process.env.AI_SERVICE_URL = 'http://localhost:8000';

// Increase timeout for async operations
jest.setTimeout(10000);

// Global beforeAll
beforeAll(() => {
  // Suppress console.log during tests (optional)
  // jest.spyOn(console, 'log').mockImplementation(() => {});
  // jest.spyOn(console, 'info').mockImplementation(() => {});
});

// Global afterAll
afterAll(() => {
  // Clean up any resources
});

// Global afterEach
afterEach(() => {
  // Reset all mocks after each test
  jest.clearAllMocks();
});
