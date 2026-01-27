import 'package:flutter_test/flutter_test.dart';
import 'package:ai_anti_spam_shield_mobile/models/phishing_result.dart';

void main() {
  group('PhishingDangerCause', () {
    test('fromJson creates correct instance', () {
      final json = {
        'type': 'suspicious_url',
        'title': 'Suspicious URL Detected',
        'description': 'The URL contains suspicious patterns',
        'severity': 'critical',
      };

      final cause = PhishingDangerCause.fromJson(json);

      expect(cause.type, 'suspicious_url');
      expect(cause.title, 'Suspicious URL Detected');
      expect(cause.description, 'The URL contains suspicious patterns');
      expect(cause.severity, 'critical');
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final cause = PhishingDangerCause.fromJson(json);

      expect(cause.type, '');
      expect(cause.title, '');
      expect(cause.description, '');
      expect(cause.severity, 'medium');
    });

    test('toJson creates correct map', () {
      final cause = PhishingDangerCause(
        type: 'brand_impersonation',
        title: 'Brand Impersonation',
        description: 'Attempting to impersonate a legitimate brand',
        severity: 'high',
      );

      final json = cause.toJson();

      expect(json['type'], 'brand_impersonation');
      expect(json['title'], 'Brand Impersonation');
      expect(json['severity'], 'high');
    });

    test('isCritical returns true for critical severity', () {
      final cause = PhishingDangerCause(
        type: 'test',
        title: 'Test',
        description: 'Test',
        severity: 'critical',
      );

      expect(cause.isCritical, true);
      expect(cause.isHigh, false);
    });

    test('isHigh returns true for high severity', () {
      final cause = PhishingDangerCause(
        type: 'test',
        title: 'Test',
        description: 'Test',
        severity: 'high',
      );

      expect(cause.isHigh, true);
      expect(cause.isCritical, false);
    });
  });

  group('URLAnalysis', () {
    test('fromJson creates correct instance', () {
      final json = {
        'url': 'http://suspicious-site.com/login',
        'isSuspicious': true,
        'score': 0.85,
        'reasons': ['Domain mismatch', 'Unusual path'],
      };

      final analysis = URLAnalysis.fromJson(json);

      expect(analysis.url, 'http://suspicious-site.com/login');
      expect(analysis.isSuspicious, true);
      expect(analysis.score, 0.85);
      expect(analysis.reasons, ['Domain mismatch', 'Unusual path']);
    });

    test('fromJson handles snake_case keys', () {
      final json = {
        'url': 'http://test.com',
        'is_suspicious': true,
        'score': 0.5,
        'reasons': [],
      };

      final analysis = URLAnalysis.fromJson(json);

      expect(analysis.isSuspicious, true);
    });

    test('toJson creates correct map', () {
      final analysis = URLAnalysis(
        url: 'http://test.com',
        isSuspicious: false,
        score: 0.1,
        reasons: ['Low risk'],
      );

      final json = analysis.toJson();

      expect(json['url'], 'http://test.com');
      expect(json['is_suspicious'], false);
      expect(json['score'], 0.1);
    });
  });

  group('BrandImpersonation', () {
    test('fromJson creates correct instance', () {
      final json = {
        'detected': true,
        'brand': 'PayPal',
        'similarityScore': 0.92,
      };

      final brand = BrandImpersonation.fromJson(json);

      expect(brand.detected, true);
      expect(brand.brand, 'PayPal');
      expect(brand.similarityScore, 0.92);
    });

    test('fromJson handles alternative keys', () {
      final json = {
        'detected': true,
        'brand': 'Google',
        'confidence': 0.88,
      };

      final brand = BrandImpersonation.fromJson(json);

      expect(brand.similarityScore, 0.88);
    });

    test('toJson creates correct map', () {
      final brand = BrandImpersonation(
        detected: true,
        brand: 'Amazon',
        similarityScore: 0.95,
      );

      final json = brand.toJson();

      expect(json['detected'], true);
      expect(json['brand'], 'Amazon');
      expect(json['similarity_score'], 0.95);
    });
  });

  group('ThreatLevel', () {
    test('displayName returns correct strings', () {
      expect(ThreatLevel.critical.displayName, 'CRITICAL');
      expect(ThreatLevel.high.displayName, 'HIGH');
      expect(ThreatLevel.medium.displayName, 'MEDIUM');
      expect(ThreatLevel.low.displayName, 'LOW');
      expect(ThreatLevel.none.displayName, 'NONE');
    });

    test('fromString parses correctly', () {
      expect(ThreatLevelExtension.fromString('CRITICAL'), ThreatLevel.critical);
      expect(ThreatLevelExtension.fromString('HIGH'), ThreatLevel.high);
      expect(ThreatLevelExtension.fromString('medium'), ThreatLevel.medium);
      expect(ThreatLevelExtension.fromString('Low'), ThreatLevel.low);
      expect(ThreatLevelExtension.fromString('unknown'), ThreatLevel.none);
    });
  });

  group('PhishingType', () {
    test('displayName returns correct strings', () {
      expect(PhishingType.email.displayName, 'EMAIL');
      expect(PhishingType.sms.displayName, 'SMS');
      expect(PhishingType.url.displayName, 'URL');
      expect(PhishingType.none.displayName, 'NONE');
    });

    test('fromString parses correctly', () {
      expect(PhishingTypeExtension.fromString('EMAIL'), PhishingType.email);
      expect(PhishingTypeExtension.fromString('SMS'), PhishingType.sms);
      expect(PhishingTypeExtension.fromString('SMISHING'), PhishingType.sms);
      expect(PhishingTypeExtension.fromString('URL'), PhishingType.url);
      expect(PhishingTypeExtension.fromString('CREDENTIAL_HARVEST'), PhishingType.email);
      expect(PhishingTypeExtension.fromString('unknown'), PhishingType.none);
    });
  });

  group('PhishingResult', () {
    test('fromJson creates complete instance', () {
      final json = {
        'isPhishing': true,
        'confidence': 0.89,
        'phishingType': 'EMAIL',
        'threatLevel': 'HIGH',
        'indicators': ['Suspicious sender', 'Fake urgency'],
        'urlsAnalyzed': [
          {
            'url': 'http://fake-bank.com',
            'isSuspicious': true,
            'score': 0.9,
            'reasons': ['Domain mismatch'],
          }
        ],
        'brandImpersonation': {
          'detected': true,
          'brand': 'Bank of America',
          'similarityScore': 0.85,
        },
        'recommendation': 'Do not click any links',
        'details': {'source': 'ml_model'},
        'timestamp': '2024-01-15T10:30:00Z',
        'historyId': 'history-123',
        'is_safe': false,
        'detection_threshold': 0.65,
        'danger_causes': [
          {
            'type': 'phishing',
            'title': 'Phishing Detected',
            'description': 'Email appears to be phishing',
            'severity': 'critical',
          }
        ],
        'risk_level': 'HIGH',
        'confidence_label': 'Phishing Confidence',
      };

      final result = PhishingResult.fromJson(json);

      expect(result.isPhishing, true);
      expect(result.confidence, 0.89);
      expect(result.phishingType, PhishingType.email);
      expect(result.threatLevel, ThreatLevel.high);
      expect(result.indicators, ['Suspicious sender', 'Fake urgency']);
      expect(result.urlsAnalyzed.length, 1);
      expect(result.urlsAnalyzed.first.isSuspicious, true);
      expect(result.brandImpersonation, isNotNull);
      expect(result.brandImpersonation!.brand, 'Bank of America');
      expect(result.recommendation, 'Do not click any links');
      expect(result.historyId, 'history-123');
      expect(result.isSafe, false);
      expect(result.dangerCauses.length, 1);
      expect(result.riskLevel, 'HIGH');
      expect(result.confidenceLabel, 'Phishing Confidence');
    });

    test('fromJson handles snake_case keys', () {
      final json = {
        'is_phishing': true,
        'confidence': 0.75,
        'phishing_type': 'SMS',
        'threat_level': 'MEDIUM',
        'indicators': [],
        'urls_analyzed': [],
        'recommendation': '',
        'details': {},
      };

      final result = PhishingResult.fromJson(json);

      expect(result.isPhishing, true);
      expect(result.phishingType, PhishingType.sms);
      expect(result.threatLevel, ThreatLevel.medium);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final result = PhishingResult.fromJson(json);

      expect(result.isPhishing, false);
      expect(result.confidence, 0.0);
      expect(result.phishingType, PhishingType.none);
      expect(result.threatLevel, ThreatLevel.none);
      expect(result.indicators, isEmpty);
      expect(result.urlsAnalyzed, isEmpty);
      expect(result.brandImpersonation, isNull);
      expect(result.isSafe, true);
      expect(result.detectionThreshold, 0.65);
    });

    test('toJson creates correct map', () {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.92,
        phishingType: PhishingType.url,
        threatLevel: ThreatLevel.critical,
        indicators: ['Malicious URL'],
        urlsAnalyzed: [],
        recommendation: 'Avoid this site',
        details: {},
        timestamp: '2024-01-15T10:30:00Z',
        historyId: 'test-123',
        isSafe: false,
        dangerCauses: [
          PhishingDangerCause(
            type: 'malware',
            title: 'Malware Risk',
            description: 'Site may contain malware',
            severity: 'critical',
          ),
        ],
        riskLevel: 'CRITICAL',
        confidenceLabel: 'Phishing Confidence',
      );

      final json = result.toJson();

      expect(json['isPhishing'], true);
      expect(json['confidence'], 0.92);
      expect(json['phishingType'], 'URL');
      expect(json['threatLevel'], 'CRITICAL');
      expect(json['historyId'], 'test-123');
      expect(json['is_safe'], false);
      expect(json['danger_causes'], isA<List>());
    });

    test('confidencePercentage formats correctly', () {
      final result = PhishingResult(
        isPhishing: false,
        confidence: 0.876,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      expect(result.confidencePercentage, '87.6%');
    });

    test('hasSuspiciousUrls returns correct value', () {
      final resultWithSuspicious = PhishingResult(
        isPhishing: true,
        confidence: 0.8,
        phishingType: PhishingType.url,
        threatLevel: ThreatLevel.high,
        indicators: [],
        urlsAnalyzed: [
          URLAnalysis(url: 'http://safe.com', isSuspicious: false, score: 0.1, reasons: []),
          URLAnalysis(url: 'http://bad.com', isSuspicious: true, score: 0.9, reasons: []),
        ],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      expect(resultWithSuspicious.hasSuspiciousUrls, true);
      expect(resultWithSuspicious.suspiciousUrlCount, 1);
    });

    test('isHighRisk returns true for critical and high threat levels', () {
      final criticalResult = PhishingResult(
        isPhishing: true,
        confidence: 0.95,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      final highResult = PhishingResult(
        isPhishing: true,
        confidence: 0.8,
        phishingType: PhishingType.sms,
        threatLevel: ThreatLevel.high,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      final mediumResult = PhishingResult(
        isPhishing: false,
        confidence: 0.5,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.medium,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      expect(criticalResult.isHighRisk, true);
      expect(highResult.isHighRisk, true);
      expect(mediumResult.isHighRisk, false);
    });

    test('hasCriticalDanger returns correct value', () {
      final resultWithCritical = PhishingResult(
        isPhishing: true,
        confidence: 0.9,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
        dangerCauses: [
          PhishingDangerCause(type: 'test', title: 'Test', description: 'Test', severity: 'critical'),
        ],
      );

      final resultWithoutCritical = PhishingResult(
        isPhishing: false,
        confidence: 0.3,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.low,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
        dangerCauses: [
          PhishingDangerCause(type: 'test', title: 'Test', description: 'Test', severity: 'low'),
        ],
      );

      expect(resultWithCritical.hasCriticalDanger, true);
      expect(resultWithoutCritical.hasCriticalDanger, false);
    });
  });

  group('PhishingScanHistory', () {
    test('fromJson creates correct instance', () {
      final json = {
        'id': 'history-1',
        'inputText': 'Suspicious email content',
        'inputUrl': 'http://phishing-site.com',
        'isPhishing': true,
        'confidence': 0.88,
        'phishingType': 'EMAIL',
        'threatLevel': 'HIGH',
        'indicators': ['Fake sender', 'Urgency'],
        'brandDetected': 'PayPal',
        'scannedAt': '2024-01-15T10:30:00Z',
      };

      final history = PhishingScanHistory.fromJson(json);

      expect(history.id, 'history-1');
      expect(history.inputText, 'Suspicious email content');
      expect(history.inputUrl, 'http://phishing-site.com');
      expect(history.isPhishing, true);
      expect(history.confidence, 0.88);
      expect(history.brandDetected, 'PayPal');
    });

    test('toJson creates correct map', () {
      final history = PhishingScanHistory(
        id: 'test-1',
        inputText: 'Test content',
        isPhishing: false,
        confidence: 0.2,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        scannedAt: DateTime(2024, 1, 15),
      );

      final json = history.toJson();

      expect(json['id'], 'test-1');
      expect(json['inputText'], 'Test content');
      expect(json['isPhishing'], false);
    });

    test('displayText truncates long text', () {
      final longText = 'A' * 150;
      final history = PhishingScanHistory(
        id: 'test-1',
        inputText: longText,
        isPhishing: false,
        confidence: 0.1,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        scannedAt: DateTime.now(),
      );

      expect(history.displayText.length, 103); // 100 + '...'
      expect(history.displayText.endsWith('...'), true);
    });

    test('displayText preserves short text', () {
      final history = PhishingScanHistory(
        id: 'test-1',
        inputText: 'Short text',
        isPhishing: false,
        confidence: 0.1,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        scannedAt: DateTime.now(),
      );

      expect(history.displayText, 'Short text');
    });
  });

  group('PhishingStatistics', () {
    test('fromJson creates correct instance', () {
      final json = {
        'totalScans': 100,
        'phishingDetected': 25,
        'safeScans': 75,
        'phishingPercentage': 25.0,
        'threatLevels': {
          'CRITICAL': 5,
          'HIGH': 10,
          'MEDIUM': 10,
          'LOW': 0,
        },
      };

      final stats = PhishingStatistics.fromJson(json);

      expect(stats.totalScans, 100);
      expect(stats.phishingDetected, 25);
      expect(stats.safeScans, 75);
      expect(stats.phishingPercentage, 25.0);
      expect(stats.threatLevels['CRITICAL'], 5);
    });

    test('fromJson handles string percentage', () {
      final json = {
        'totalScans': 50,
        'phishingDetected': 10,
        'safeScans': 40,
        'phishingPercentage': '20.0',
        'threatLevels': {},
      };

      final stats = PhishingStatistics.fromJson(json);

      expect(stats.phishingPercentage, 20.0);
    });

    test('toJson creates correct map', () {
      final stats = PhishingStatistics(
        totalScans: 200,
        phishingDetected: 50,
        safeScans: 150,
        phishingPercentage: 25.0,
        threatLevels: {'HIGH': 20},
      );

      final json = stats.toJson();

      expect(json['totalScans'], 200);
      expect(json['phishingDetected'], 50);
    });
  });

  group('BatchPhishingResult', () {
    test('fromJson creates correct instance', () {
      final json = {
        'results': [
          {
            'isPhishing': true,
            'confidence': 0.8,
            'phishingType': 'EMAIL',
            'threatLevel': 'HIGH',
            'indicators': [],
            'urlsAnalyzed': [],
            'recommendation': '',
            'details': {},
          },
          {
            'isPhishing': false,
            'confidence': 0.9,
            'phishingType': 'NONE',
            'threatLevel': 'NONE',
            'indicators': [],
            'urlsAnalyzed': [],
            'recommendation': '',
            'details': {},
          },
        ],
        'summary': {
          'total': 2,
          'phishing_detected': 1,
          'safe': 1,
          'threat_levels': {'HIGH': 1},
        },
        'timestamp': '2024-01-15T10:30:00Z',
      };

      final batch = BatchPhishingResult.fromJson(json);

      expect(batch.results.length, 2);
      expect(batch.total, 2);
      expect(batch.phishingDetected, 1);
      expect(batch.safe, 1);
      expect(batch.threatLevels['HIGH'], 1);
    });
  });
}
