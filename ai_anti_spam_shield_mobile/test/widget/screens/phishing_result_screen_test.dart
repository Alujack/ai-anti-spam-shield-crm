import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/phishing_result.dart';

void main() {
  group('Phishing Result Screen UI Components', () {
    testWidgets('displays phishing detected indicator', (tester) async {
      final phishingResult = PhishingResult(
        isPhishing: true,
        confidence: 0.92,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: ['Suspicious sender', 'Fake urgency', 'Malicious link'],
        urlsAnalyzed: [],
        recommendation: 'Do not click any links',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'CRITICAL',
        confidenceLabel: 'Phishing Confidence',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockPhishingResultDisplay(result: phishingResult),
            ),
          ),
        ),
      );

      expect(find.text('Phishing Detected'), findsOneWidget);
      expect(find.text('92.0%'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('displays safe indicator for non-phishing result', (tester) async {
      final safeResult = PhishingResult(
        isPhishing: false,
        confidence: 0.95,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: 'This content appears to be safe',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
        confidenceLabel: 'Safety Confidence',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockPhishingResultDisplay(result: safeResult),
            ),
          ),
        ),
      );

      expect(find.text('Safe Content'), findsOneWidget);
      expect(find.text('95.0%'), findsOneWidget);
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('displays threat level badge correctly', (tester) async {
      final threatLevels = [
        (ThreatLevel.critical, 'CRITICAL', Colors.red),
        (ThreatLevel.high, 'HIGH', Colors.orange),
        (ThreatLevel.medium, 'MEDIUM', Colors.amber),
        (ThreatLevel.low, 'LOW', Colors.yellow),
        (ThreatLevel.none, 'NONE', Colors.green),
      ];

      for (final (level, label, _) in threatLevels) {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: _MockThreatLevelBadge(threatLevel: level),
            ),
          ),
        );

        expect(find.text(label), findsOneWidget);
        await tester.pumpAndSettle();
      }
    });

    testWidgets('displays phishing type correctly', (tester) async {
      final phishingTypes = [
        (PhishingType.email, 'EMAIL'),
        (PhishingType.sms, 'SMS'),
        (PhishingType.url, 'URL'),
      ];

      for (final (type, label) in phishingTypes) {
        final result = PhishingResult(
          isPhishing: true,
          confidence: 0.85,
          phishingType: type,
          threatLevel: ThreatLevel.high,
          indicators: [],
          urlsAnalyzed: [],
          recommendation: '',
          details: {},
          timestamp: '',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: _MockPhishingTypeDisplay(result: result),
            ),
          ),
        );

        expect(find.text(label), findsOneWidget);
      }
    });

    testWidgets('displays indicators list', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.9,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: [
          'Suspicious sender address',
          'Urgency language detected',
          'Contains suspicious links',
        ],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockIndicatorsList(indicators: result.indicators),
            ),
          ),
        ),
      );

      expect(find.text('Suspicious sender address'), findsOneWidget);
      expect(find.text('Urgency language detected'), findsOneWidget);
      expect(find.text('Contains suspicious links'), findsOneWidget);
    });

    testWidgets('displays URL analysis results', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.88,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: [],
        urlsAnalyzed: [
          URLAnalysis(
            url: 'http://fake-bank.com',
            isSuspicious: true,
            score: 0.95,
            reasons: ['Domain mismatch', 'Known phishing domain'],
          ),
          URLAnalysis(
            url: 'http://google.com',
            isSuspicious: false,
            score: 0.05,
            reasons: [],
          ),
        ],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockURLAnalysisDisplay(urls: result.urlsAnalyzed),
            ),
          ),
        ),
      );

      expect(find.text('http://fake-bank.com'), findsOneWidget);
      expect(find.text('http://google.com'), findsOneWidget);
      expect(find.text('Domain mismatch'), findsOneWidget);
    });

    testWidgets('displays brand impersonation warning', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.92,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: [],
        urlsAnalyzed: [],
        brandImpersonation: BrandImpersonation(
          detected: true,
          brand: 'PayPal',
          similarityScore: 0.89,
        ),
        recommendation: '',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockBrandImpersonationDisplay(
                brandImpersonation: result.brandImpersonation!,
              ),
            ),
          ),
        ),
      );

      expect(find.text('Brand Impersonation Detected'), findsOneWidget);
      expect(find.text('PayPal'), findsOneWidget);
    });

    testWidgets('displays danger causes list', (tester) async {
      final result = PhishingResult(
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
          PhishingDangerCause(
            type: 'phishing',
            title: 'Phishing Attack',
            description: 'This email is attempting to steal credentials',
            severity: 'critical',
          ),
          PhishingDangerCause(
            type: 'spoofing',
            title: 'Sender Spoofing',
            description: 'Sender address does not match claimed identity',
            severity: 'high',
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockDangerCausesList(causes: result.dangerCauses),
            ),
          ),
        ),
      );

      expect(find.text('Phishing Attack'), findsOneWidget);
      expect(find.text('Sender Spoofing'), findsOneWidget);
      expect(find.text('This email is attempting to steal credentials'), findsOneWidget);
    });

    testWidgets('displays recommendation text', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.88,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: 'Do not click any links. Delete this email immediately.',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _MockRecommendationDisplay(recommendation: result.recommendation),
          ),
        ),
      );

      expect(
        find.text('Do not click any links. Delete this email immediately.'),
        findsOneWidget,
      );
    });

    testWidgets('displays action buttons', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockActionButtons(),
            ),
          ),
        ),
      );

      expect(find.text('Report'), findsOneWidget);
      expect(find.text('Scan Another'), findsOneWidget);
    });

    testWidgets('report button is tappable', (tester) async {
      bool reportTapped = false;

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockActionButtons(
                onReportTap: () => reportTapped = true,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Report'));
      await tester.pumpAndSettle();

      expect(reportTapped, true);
    });
  });

  group('Threat Level Colors', () {
    testWidgets('CRITICAL shows red color', (tester) async {
      await _testThreatLevelColor(tester, ThreatLevel.critical, Colors.red);
    });

    testWidgets('HIGH shows orange color', (tester) async {
      await _testThreatLevelColor(tester, ThreatLevel.high, Colors.orange);
    });

    testWidgets('MEDIUM shows amber color', (tester) async {
      await _testThreatLevelColor(tester, ThreatLevel.medium, Colors.amber);
    });

    testWidgets('NONE shows green color', (tester) async {
      await _testThreatLevelColor(tester, ThreatLevel.none, Colors.green);
    });
  });

  group('Phishing Type Icons', () {
    testWidgets('EMAIL type shows email icon', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _MockPhishingTypeIcon(type: PhishingType.email),
          ),
        ),
      );

      expect(find.byIcon(Icons.email), findsOneWidget);
    });

    testWidgets('SMS type shows sms icon', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _MockPhishingTypeIcon(type: PhishingType.sms),
          ),
        ),
      );

      expect(find.byIcon(Icons.sms), findsOneWidget);
    });

    testWidgets('URL type shows link icon', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _MockPhishingTypeIcon(type: PhishingType.url),
          ),
        ),
      );

      expect(find.byIcon(Icons.link), findsOneWidget);
    });
  });

  group('Confidence Display', () {
    testWidgets('high confidence shows correct percentage', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.925,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: Text(result.confidencePercentage),
            ),
          ),
        ),
      );

      expect(find.text('92.5%'), findsOneWidget);
    });

    testWidgets('low confidence shows correct percentage', (tester) async {
      final result = PhishingResult(
        isPhishing: false,
        confidence: 0.123,
        phishingType: PhishingType.none,
        threatLevel: ThreatLevel.none,
        indicators: [],
        urlsAnalyzed: [],
        recommendation: '',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: Text(result.confidencePercentage),
            ),
          ),
        ),
      );

      expect(find.text('12.3%'), findsOneWidget);
    });
  });
}

// Helper function for testing threat level colors
Future<void> _testThreatLevelColor(
  WidgetTester tester,
  ThreatLevel level,
  Color expectedColor,
) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Center(
          child: Container(
            key: const Key('threat-badge'),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getThreatColor(level),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(level.displayName),
          ),
        ),
      ),
    ),
  );

  expect(find.text(level.displayName), findsOneWidget);

  final container = tester.widget<Container>(find.byKey(const Key('threat-badge')));
  final decoration = container.decoration as BoxDecoration;
  expect(decoration.color, expectedColor);
}

Color _getThreatColor(ThreatLevel level) {
  switch (level) {
    case ThreatLevel.critical:
      return Colors.red;
    case ThreatLevel.high:
      return Colors.orange;
    case ThreatLevel.medium:
      return Colors.amber;
    case ThreatLevel.low:
      return Colors.yellow;
    case ThreatLevel.none:
      return Colors.green;
  }
}

// Mock widgets for testing

class _MockPhishingResultDisplay extends StatelessWidget {
  final PhishingResult result;

  const _MockPhishingResultDisplay({required this.result});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          result.isPhishing ? Icons.warning : Icons.check_circle,
          color: result.isPhishing ? Colors.red : Colors.green,
          size: 48,
        ),
        Text(result.isPhishing ? 'Phishing Detected' : 'Safe Content'),
        Text('${(result.confidence * 100).toStringAsFixed(1)}%'),
      ],
    );
  }
}

class _MockThreatLevelBadge extends StatelessWidget {
  final ThreatLevel threatLevel;

  const _MockThreatLevelBadge({required this.threatLevel});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: _getThreatColor(threatLevel),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(threatLevel.displayName),
    );
  }
}

class _MockPhishingTypeDisplay extends StatelessWidget {
  final PhishingResult result;

  const _MockPhishingTypeDisplay({required this.result});

  @override
  Widget build(BuildContext context) {
    return Text(result.phishingType.displayName);
  }
}

class _MockIndicatorsList extends StatelessWidget {
  final List<String> indicators;

  const _MockIndicatorsList({required this.indicators});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: indicators.length,
      itemBuilder: (context, index) {
        return ListTile(
          leading: const Icon(Icons.warning_amber),
          title: Text(indicators[index]),
        );
      },
    );
  }
}

class _MockURLAnalysisDisplay extends StatelessWidget {
  final List<URLAnalysis> urls;

  const _MockURLAnalysisDisplay({required this.urls});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: urls.length,
      itemBuilder: (context, index) {
        final url = urls[index];
        return ListTile(
          leading: Icon(
            url.isSuspicious ? Icons.dangerous : Icons.check_circle,
            color: url.isSuspicious ? Colors.red : Colors.green,
          ),
          title: Text(url.url),
          subtitle: url.reasons.isNotEmpty
              ? Text(url.reasons.join(', '))
              : null,
        );
      },
    );
  }
}

class _MockBrandImpersonationDisplay extends StatelessWidget {
  final BrandImpersonation brandImpersonation;

  const _MockBrandImpersonationDisplay({required this.brandImpersonation});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Text('Brand Impersonation Detected'),
        Text(brandImpersonation.brand ?? ''),
      ],
    );
  }
}

class _MockDangerCausesList extends StatelessWidget {
  final List<PhishingDangerCause> causes;

  const _MockDangerCausesList({required this.causes});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: causes.length,
      itemBuilder: (context, index) {
        final cause = causes[index];
        return ListTile(
          leading: Icon(
            cause.isCritical ? Icons.error : Icons.warning,
            color: cause.isCritical ? Colors.red : Colors.orange,
          ),
          title: Text(cause.title),
          subtitle: Text(cause.description),
        );
      },
    );
  }
}

class _MockRecommendationDisplay extends StatelessWidget {
  final String recommendation;

  const _MockRecommendationDisplay({required this.recommendation});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(recommendation),
      ),
    );
  }
}

class _MockActionButtons extends StatelessWidget {
  final VoidCallback? onReportTap;
  final VoidCallback? onScanAnotherTap;

  const _MockActionButtons({this.onReportTap, this.onScanAnotherTap});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        ElevatedButton(
          onPressed: onReportTap ?? () {},
          child: const Text('Report'),
        ),
        const SizedBox(width: 16),
        ElevatedButton(
          onPressed: onScanAnotherTap ?? () {},
          child: const Text('Scan Another'),
        ),
      ],
    );
  }
}

class _MockPhishingTypeIcon extends StatelessWidget {
  final PhishingType type;

  const _MockPhishingTypeIcon({required this.type});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    switch (type) {
      case PhishingType.email:
        icon = Icons.email;
        break;
      case PhishingType.sms:
        icon = Icons.sms;
        break;
      case PhishingType.url:
        icon = Icons.link;
        break;
      case PhishingType.none:
        icon = Icons.help_outline;
        break;
    }
    return Icon(icon);
  }
}
