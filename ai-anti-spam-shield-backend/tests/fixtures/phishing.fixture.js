/**
 * Phishing Test Fixtures
 */

const phishingText = {
  urgentEmail: 'URGENT: Your PayPal account has been suspended. Click here immediately to verify: http://paypa1-secure.tk/login',
  bankScam: 'Your Bank of America account needs verification. Enter your SSN and password at: http://boa-verify.xyz',
  prizeScam: 'Congratulations! You won $1,000,000! Claim now at: http://claim-prize-now.ml',
  normalEmail: 'Hi John, just wanted to check if you received my earlier message about the meeting tomorrow.',
  greeting: 'Hello, how are you doing today?'
};

const phishingUrls = {
  suspiciousIp: 'http://192.168.1.1/login',
  fakeBrand: 'http://paypa1-secure.tk/verify',
  shortener: 'http://bit.ly/3xyzabc',
  normalUrl: 'https://www.google.com',
  suspiciousTld: 'http://secure-bank.xyz/login'
};

const phishingScanResult = {
  isPhishing: true,
  confidence: 0.87,
  raw_phishing_confidence: 0.87,
  phishingType: 'EMAIL',
  threatLevel: 'HIGH',
  indicators: ['Urgency language detected', 'Suspicious URL found'],
  urlsAnalyzed: [{
    url: 'http://paypa1-secure.tk/login',
    is_suspicious: true,
    reasons: ['Suspicious TLD', 'Brand impersonation']
  }],
  brandImpersonation: {
    detected: true,
    brand: 'PayPal'
  },
  recommendation: 'Do not click any links',
  is_safe: false,
  danger_causes: [
    {
      type: 'phishing_detected',
      title: 'Phishing Detected',
      description: 'High confidence phishing attempt',
      severity: 'critical'
    }
  ]
};

const safeScanResult = {
  isPhishing: false,
  confidence: 0.92,
  raw_phishing_confidence: 0.08,
  phishingType: 'NONE',
  threatLevel: 'NONE',
  indicators: [],
  urlsAnalyzed: [],
  brandImpersonation: null,
  recommendation: 'This message appears safe',
  is_safe: true,
  danger_causes: []
};

const phishingHistoryRecord = {
  id: 'phishing-scan-uuid-123',
  userId: 'user-uuid-123',
  inputText: 'URGENT: Verify your account...',
  inputUrl: null,
  isPhishing: true,
  confidence: 0.87,
  phishingType: 'EMAIL',
  threatLevel: 'HIGH',
  indicators: JSON.stringify(['Urgency detected']),
  urlsAnalyzed: null,
  brandDetected: 'PayPal',
  scannedAt: new Date('2024-01-15')
};

module.exports = {
  phishingText,
  phishingUrls,
  phishingScanResult,
  safeScanResult,
  phishingHistoryRecord
};
