import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/providers/phishing_provider.dart';
import 'package:ai_anti_spam_shield_mobile/models/phishing_result.dart';

void main() {
  group('PhishingState', () {
    test('initial state has no result and is not loading', () {
      final state = PhishingState();

      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
      expect(state.history, isEmpty);
      expect(state.statistics, isNull);
    });

    test('copyWith creates new state with updated values', () {
      final initialState = PhishingState();
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.isLoading, true);
      expect(newState.result, isNull);
      expect(newState.error, isNull);
    });

    test('copyWith preserves unmodified values', () {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.9,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: ['Suspicious sender'],
        urlsAnalyzed: [],
        recommendation: 'Be careful',
        details: {},
        timestamp: '',
      );
      final initialState = PhishingState(result: result);
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.result, equals(result));
      expect(newState.isLoading, true);
    });

    test('copyWith can update result', () {
      final result = PhishingResult(
        isPhishing: false,
        confidence: 0.85,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );
      final initialState = PhishingState();
      final newState = initialState.copyWith(result: result);

      expect(newState.result, equals(result));
      expect(newState.result!.isPhishing, false);
    });

    test('copyWith can update error', () {
      final initialState = PhishingState();
      final newState = initialState.copyWith(error: 'Network error');

      expect(newState.error, 'Network error');
    });

    test('copyWith can update history', () {
      final history = [
        PhishingScanHistory(
          id: 'h1',
          inputText: 'Test',
          isPhishing: false,
          confidence: 0.9,
          phishingType: PhishingType.none,
          threatLevel: ThreatLevel.none,
          indicators: [],
          scannedAt: DateTime.now(),
        ),
      ];
      final initialState = PhishingState();
      final newState = initialState.copyWith(history: history);

      expect(newState.history, equals(history));
      expect(newState.history.length, 1);
    });

    test('copyWith can update statistics', () {
      final stats = PhishingStatistics(
        totalScans: 100,
        phishingDetected: 20,
        safeScans: 80,
        phishingPercentage: 20.0,
        threatLevels: {'HIGH': 10, 'CRITICAL': 5},
      );
      final initialState = PhishingState();
      final newState = initialState.copyWith(statistics: stats);

      expect(newState.statistics, equals(stats));
      expect(newState.statistics!.totalScans, 100);
    });

    test('copyWith clears error when null is passed', () {
      final stateWithError = PhishingState(error: 'Some error');
      final clearedState = stateWithError.copyWith(error: null);

      // Note: When passing null explicitly, copyWith keeps the existing value
      // To clear the error, you need to set error explicitly
      expect(clearedState.error, isNull);
    });
  });

  group('PhishingNotifier', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('initial state is empty', () {
      final state = container.read(phishingProvider);

      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
      expect(state.history, isEmpty);
      expect(state.statistics, isNull);
    });

    test('clearResult resets result and error', () {
      final notifier = container.read(phishingProvider.notifier);

      notifier.clearResult();

      final state = container.read(phishingProvider);
      expect(state.result, isNull);
      expect(state.error, isNull);
    });

    test('clearError clears only error', () {
      final notifier = container.read(phishingProvider.notifier);

      notifier.clearError();

      final state = container.read(phishingProvider);
      expect(state.error, isNull);
    });

    test('reset returns state to initial values', () {
      final notifier = container.read(phishingProvider.notifier);

      notifier.reset();

      final state = container.read(phishingProvider);
      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
      expect(state.history, isEmpty);
      expect(state.statistics, isNull);
    });
  });

  group('PhishingResult integration with PhishingState', () {
    test('state correctly holds phishing result', () {
      final phishingResult = PhishingResult(
        isPhishing: true,
        confidence: 0.92,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: ['Suspicious sender', 'Fake urgency', 'Malicious link'],
        urlsAnalyzed: [
          URLAnalysis(
            url: 'http://fake-bank.com/login',
            isSuspicious: true,
            score: 0.95,
            reasons: ['Domain mismatch', 'Unusual path'],
          ),
        ],
        brandImpersonation: BrandImpersonation(
          detected: true,
          brand: 'Bank of America',
          similarityScore: 0.88,
        ),
        recommendation: 'Do not click any links. Delete this email.',
        details: {'source': 'ml_model', 'version': '2.0'},
        timestamp: DateTime.now().toIso8601String(),
        dangerCauses: [
          PhishingDangerCause(
            type: 'phishing',
            title: 'Phishing Attack',
            description: 'This email is attempting to steal your credentials',
            severity: 'critical',
          ),
        ],
        riskLevel: 'CRITICAL',
        confidenceLabel: 'Phishing Confidence',
      );

      final state = PhishingState(result: phishingResult);

      expect(state.result!.isPhishing, true);
      expect(state.result!.isHighRisk, true);
      expect(state.result!.hasSuspiciousUrls, true);
      expect(state.result!.suspiciousUrlCount, 1);
      expect(state.result!.brandImpersonation!.detected, true);
      expect(state.result!.hasCriticalDanger, true);
      expect(state.result!.dangerCount, 1);
    });

    test('state correctly holds safe phishing result', () {
      final safeResult = PhishingResult(
        isPhishing: false,
        confidence: 0.95,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [
          URLAnalysis(
            url: 'http://google.com',
            isSuspicious: false,
            score: 0.05,
            reasons: [],
          ),
        ],
        recommendation: 'This content appears to be safe.',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
        confidenceLabel: 'Safety Confidence',
      );

      final state = PhishingState(result: safeResult);

      expect(state.result!.isPhishing, false);
      expect(state.result!.isSafe, true);
      expect(state.result!.isHighRisk, false);
      expect(state.result!.hasSuspiciousUrls, false);
      expect(state.result!.hasCriticalDanger, false);
    });

    test('state correctly holds SMS phishing (smishing) result', () {
      final smishingResult = PhishingResult(
        isPhishing: true,
        confidence: 0.87,
        phishingType: PhishingType.sms,
        threatLevel: ThreatLevel.high,
        indicators: ['Unknown sender', 'Urgency', 'Link to unknown domain'],
        urlsAnalyzed: [],
        recommendation: 'Do not respond to this SMS.',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'HIGH',
      );

      final state = PhishingState(result: smishingResult);

      expect(state.result!.phishingType, PhishingType.sms);
      expect(state.result!.phishingType.displayName, 'SMS');
      expect(state.result!.threatLevel, ThreatLevel.high);
    });

    test('state handles history correctly', () {
      final histories = [
        PhishingScanHistory(
          id: 'h1',
          inputText: 'Your account has been compromised',
          inputUrl: 'http://fake.com',
          isPhishing: true,
          confidence: 0.92,
          phishingType: PhishingType.email,
          threatLevel: ThreatLevel.critical,
          indicators: ['Fake urgency'],
          brandDetected: 'PayPal',
          scannedAt: DateTime.now().subtract(const Duration(hours: 1)),
        ),
        PhishingScanHistory(
          id: 'h2',
          inputText: 'Hello, how are you?',
          isPhishing: false,
          confidence: 0.95,
          phishingType: PhishingType.none,
          threatLevel: ThreatLevel.none,
          indicators: [],
          scannedAt: DateTime.now(),
        ),
      ];

      final state = PhishingState(history: histories);

      expect(state.history.length, 2);
      expect(state.history.first.isPhishing, true);
      expect(state.history.first.brandDetected, 'PayPal');
      expect(state.history.last.isPhishing, false);
    });
  });

  group('PhishingState with loading states', () {
    test('loading state during scan', () {
      final loadingState = PhishingState(isLoading: true);

      expect(loadingState.isLoading, true);
      expect(loadingState.result, isNull);
      expect(loadingState.error, isNull);
    });

    test('error state after failed scan', () {
      final errorState = PhishingState(
        isLoading: false,
        error: 'AI service unavailable',
      );

      expect(errorState.isLoading, false);
      expect(errorState.error, 'AI service unavailable');
      expect(errorState.result, isNull);
    });

    test('transition from loading to result', () {
      final loadingState = PhishingState(isLoading: true);

      final result = PhishingResult(
        isPhishing: false,
        confidence: 0.9,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      final resultState = loadingState.copyWith(
        isLoading: false,
        result: result,
      );

      expect(resultState.isLoading, false);
      expect(resultState.result, isNotNull);
    });

    test('transition from loading to error', () {
      final loadingState = PhishingState(isLoading: true);

      final errorState = loadingState.copyWith(
        isLoading: false,
        error: 'Connection refused',
      );

      expect(errorState.isLoading, false);
      expect(errorState.error, 'Connection refused');
    });
  });

  group('Edge Cases', () {
    test('handles empty indicators list', () {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.75,
        phishingType: PhishingType.url,
        threatLevel: ThreatLevel.medium,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: 'Exercise caution',
        details: {},
        timestamp: '',
      );

      final state = PhishingState(result: result);

      expect(state.result!.indicators, isEmpty);
      expect(state.result!.isPhishing, true);
    });

    test('handles multiple URLs analyzed', () {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.85,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: ['Multiple suspicious URLs'],
        urlsAnalyzed: [
          URLAnalysis(url: 'http://safe.com', isSuspicious: false, score: 0.1, reasons: []),
          URLAnalysis(url: 'http://bad1.com', isSuspicious: true, score: 0.85, reasons: ['Phishing domain']),
          URLAnalysis(url: 'http://bad2.com', isSuspicious: true, score: 0.9, reasons: ['Known malware']),
        ],
        recommendation: 'Do not click any links',
        details: {},
        timestamp: '',
      );

      final state = PhishingState(result: result);

      expect(state.result!.urlsAnalyzed.length, 3);
      expect(state.result!.suspiciousUrlCount, 2);
      expect(state.result!.hasSuspiciousUrls, true);
    });

    test('handles different threat levels correctly', () {
      final threatLevels = [
        (ThreatLevel.critical, true),
        (ThreatLevel.high, true),
        (ThreatLevel.medium, false),
        (ThreatLevel.low, false),
        (ThreatLevel.none, false),
      ];

      for (final (level, expectedHighRisk) in threatLevels) {
        final result = PhishingResult(
          isPhishing: level != ThreatLevel.none,
          confidence: 0.8,
          phishingType: PhishingType.email,
          threatLevel: level,
          indicators: [],
          urlsAnalyzed: [],
          recommendation: '',
          details: {},
          timestamp: '',
        );

        expect(result.isHighRisk, expectedHighRisk, reason: 'ThreatLevel ${level.displayName}');
      }
    });
  });
}
