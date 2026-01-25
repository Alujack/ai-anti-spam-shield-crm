// ESLint Configuration for AI Anti-Spam Shield Backend
// EDUCATIONAL NOTE: ESLint helps catch bugs and enforce code style
// Learn more: https://eslint.org/docs/latest/use/getting-started

module.exports = {
  env: {
    node: true,
    es2021: true,
    jest: true, // Enable Jest globals for testing
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // Possible Errors
    'no-console': 'off', // Allow console.log in Node.js
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

    // Best Practices
    'eqeqeq': ['error', 'always'], // Require === instead of ==
    'no-eval': 'error', // Disallow eval()
    'no-implied-eval': 'error',

    // Variables
    'no-use-before-define': ['error', { functions: false }],

    // Style (relaxed for flexibility)
    'semi': ['warn', 'always'],
    'quotes': ['warn', 'single', { avoidEscape: true }],
    'indent': 'off', // Let Prettier handle indentation
    'comma-dangle': 'off',

    // ES6
    'prefer-const': 'warn',
    'no-var': 'error',
  },
  ignorePatterns: [
    'node_modules/',
    'coverage/',
    'dist/',
    '*.min.js',
  ],
};
