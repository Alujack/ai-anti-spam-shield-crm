/**
 * AI Service Mock
 * Mocks axios calls to the AI service for testing
 */

const nock = require('nock');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

/**
 * Create mock for spam prediction endpoint
 */
const mockSpamPrediction = (options = {}) => {
  const {
    isSpam = false,
    confidence = 0.85,
    prediction = isSpam ? 'spam' : 'ham',
    statusCode = 200
  } = options;

  return nock(AI_SERVICE_URL)
    .post('/predict')
    .reply(statusCode, {
      is_spam: isSpam,
      confidence,
      prediction,
      probability: isSpam ? confidence : 1 - confidence,
      probabilities: {
        spam: isSpam ? confidence : 1 - confidence,
        ham: isSpam ? 1 - confidence : confidence
      },
      details: {
        features: {
          has_url: false,
          urgency_words: isSpam,
          currency_symbols: isSpam
        }
      },
      timestamp: new Date().toISOString()
    });
};

/**
 * Create mock for phishing detection endpoint
 */
const mockPhishingDetection = (options = {}) => {
  const {
    isPhishing = false,
    confidence = isPhishing ? 0.85 : 0.15,
    threatLevel = isPhishing ? 'HIGH' : 'NONE',
    statusCode = 200
  } = options;

  return nock(AI_SERVICE_URL)
    .post('/predict-phishing')
    .reply(statusCode, {
      is_phishing: isPhishing,
      confidence,
      phishing_type: isPhishing ? 'EMAIL' : 'NONE',
      threat_level: threatLevel,
      indicators: isPhishing ? ['Urgency language detected', 'Suspicious URL pattern'] : [],
      urls_analyzed: [],
      brand_impersonation: isPhishing ? { detected: true, brand: 'PayPal' } : null,
      recommendation: isPhishing
        ? 'Do not click any links in this message'
        : 'This message appears safe',
      details: {},
      timestamp: new Date().toISOString()
    });
};

/**
 * Create mock for URL scanning endpoint
 */
const mockUrlScan = (options = {}) => {
  const {
    isPhishing = false,
    confidence = isPhishing ? 0.85 : 0.15,
    threatLevel = isPhishing ? 'HIGH' : 'NONE',
    statusCode = 200
  } = options;

  return nock(AI_SERVICE_URL)
    .post('/scan-url')
    .reply(statusCode, {
      is_phishing: isPhishing,
      confidence,
      phishing_type: isPhishing ? 'URL' : 'NONE',
      threat_level: threatLevel,
      indicators: isPhishing ? ['Suspicious domain', 'Recently registered'] : [],
      urls_analyzed: [{
        url: 'http://test.com',
        is_suspicious: isPhishing,
        reasons: isPhishing ? ['Suspicious TLD'] : []
      }],
      brand_impersonation: null,
      recommendation: isPhishing
        ? 'Do not visit this URL'
        : 'This URL appears safe',
      timestamp: new Date().toISOString()
    });
};

/**
 * Create mock for batch phishing scan
 */
const mockBatchPhishingScan = (options = {}) => {
  const { statusCode = 200, itemCount = 2 } = options;

  const results = Array(itemCount).fill(null).map((_, i) => ({
    item: `Test item ${i + 1}`,
    is_phishing: i === 0,
    confidence: i === 0 ? 0.85 : 0.15,
    threat_level: i === 0 ? 'HIGH' : 'NONE'
  }));

  return nock(AI_SERVICE_URL)
    .post('/batch-phishing')
    .reply(statusCode, {
      results,
      summary: {
        total: itemCount,
        phishing_detected: 1,
        safe: itemCount - 1
      },
      timestamp: new Date().toISOString()
    });
};

/**
 * Create mock for voice scan endpoint
 */
const mockVoiceScan = (options = {}) => {
  const {
    isSpam = false,
    confidence = 0.85,
    statusCode = 200
  } = options;

  return nock(AI_SERVICE_URL)
    .post('/predict-voice')
    .reply(statusCode, {
      is_spam: isSpam,
      confidence,
      prediction: isSpam ? 'spam' : 'ham',
      transcribed_text: 'This is the transcribed text from the audio',
      timestamp: new Date().toISOString()
    });
};

/**
 * Create mock for AI service error
 */
const mockAIServiceError = (endpoint = '/predict', statusCode = 500) => {
  return nock(AI_SERVICE_URL)
    .post(endpoint)
    .reply(statusCode, { error: 'Internal server error' });
};

/**
 * Create mock for AI service unavailable
 */
const mockAIServiceUnavailable = (endpoint = '/predict') => {
  return nock(AI_SERVICE_URL)
    .post(endpoint)
    .replyWithError({ code: 'ECONNREFUSED' });
};

/**
 * Clean all nock mocks
 */
const cleanMocks = () => {
  nock.cleanAll();
};

/**
 * Check if all mocks have been used
 */
const checkAllMocksUsed = () => {
  return nock.isDone();
};

// Jest mock for axios (used by integration tests that mock axios directly)
const axiosMock = {
  post: jest.fn(),
  get: jest.fn(),
  create: jest.fn(() => axiosMock),
  defaults: { headers: { common: {} } }
};

module.exports = {
  mockSpamPrediction,
  mockPhishingDetection,
  mockUrlScan,
  mockBatchPhishingScan,
  mockVoiceScan,
  mockAIServiceError,
  mockAIServiceUnavailable,
  cleanMocks,
  checkAllMocksUsed,
  AI_SERVICE_URL,
  // Export axios mock methods for integration tests
  post: axiosMock.post,
  get: axiosMock.get,
  create: axiosMock.create,
  defaults: axiosMock.defaults
};
