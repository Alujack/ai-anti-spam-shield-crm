/**
 * Jest Configuration for E2E Tests
 */

module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/specs/**/*.e2e.spec.js'],
  setupFilesAfterEnv: ['./setup/jest.setup.js'],
  testTimeout: 60000,
  verbose: true,
  collectCoverageFrom: ['specs/**/*.js'],
  coverageDirectory: 'coverage',
  reporters: [
    'default',
    [
      'jest-html-reporters',
      {
        publicPath: './reports',
        filename: 'e2e-report.html',
        expand: true,
      },
    ],
    [
      'jest-junit',
      {
        outputDirectory: './reports',
        outputName: 'e2e-junit.xml',
      },
    ],
  ],
  maxWorkers: 4,
  bail: false,
  forceExit: true,
};
