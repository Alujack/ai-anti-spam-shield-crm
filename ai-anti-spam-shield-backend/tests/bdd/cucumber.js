/**
 * Cucumber Configuration
 * BDD test configuration for AI Anti-Spam Shield
 */

module.exports = {
  default: {
    requireModule: [],
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/**/*.feature'],
    format: [
      'progress-bar',
      'html:reports/cucumber-report.html',
      'json:reports/cucumber-report.json',
    ],
    formatOptions: {
      snippetInterface: 'async-await',
    },
    publishQuiet: true,
    parallel: 2,
    retry: 1,
    strict: true,
    tags: 'not @skip',
    worldParameters: {
      baseUrl: process.env.API_BASE_URL || 'http://localhost:3000',
      aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
    },
  },

  // Smoke tests - quick sanity checks
  smoke: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/**/*.feature'],
    format: ['progress-bar'],
    tags: '@smoke',
    parallel: 1,
  },

  // Integration tests
  integration: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/**/*.feature'],
    format: ['progress-bar', 'json:reports/integration-report.json'],
    tags: '@integration',
  },

  // Spam detection tests only
  spam: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/spam-detection.feature'],
    format: ['progress-bar'],
  },

  // Phishing detection tests only
  phishing: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/phishing-detection.feature'],
    format: ['progress-bar'],
  },

  // Authentication tests only
  auth: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/user-authentication.feature'],
    format: ['progress-bar'],
  },

  // Report tests only
  reports: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/reports.feature'],
    format: ['progress-bar'],
  },

  // Feedback tests only
  feedback: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/feedback.feature'],
    format: ['progress-bar'],
  },

  // CI/CD pipeline configuration
  ci: {
    require: ['./step_definitions/**/*.js', './support/**/*.js'],
    paths: ['./features/**/*.feature'],
    format: [
      'progress-bar',
      'json:reports/cucumber-ci-report.json',
      'junit:reports/cucumber-junit.xml',
    ],
    parallel: 4,
    retry: 2,
    strict: true,
    tags: 'not @skip and not @manual',
  },
};
