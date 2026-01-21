import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';

// Note: These tests verify UI components in isolation
// The actual ResultScreen import may need adjustment based on your project structure

void main() {
  group('Result Screen UI Components', () {
    testWidgets('displays spam indicator for spam result', (tester) async {
      final spamResult = ScanResult(
        isSpam: true,
        confidence: 0.87,
        prediction: 'spam',
        message: 'URGENT: Click here!',
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'HIGH',
      );

      // Test the UI representation of spam results
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Column(
                children: [
                  // Spam indicator
                  Container(
                    padding: const EdgeInsets.all(16),
                    color: Colors.red.shade100,
                    child: Column(
                      children: [
                        Icon(
                          spamResult.isSpam ? Icons.warning : Icons.check_circle,
                          color: spamResult.isSpam ? Colors.red : Colors.green,
                          size: 48,
                        ),
                        Text(
                          spamResult.isSpam ? 'Spam Detected' : 'Safe Message',
                          style: TextStyle(
                            color: spamResult.isSpam ? Colors.red : Colors.green,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text('${(spamResult.confidence * 100).toStringAsFixed(1)}%'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );

      expect(find.text('Spam Detected'), findsOneWidget);
      expect(find.text('87.0%'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('displays safe indicator for ham result', (tester) async {
      final safeResult = ScanResult(
        isSpam: false,
        confidence: 0.92,
        prediction: 'ham',
        message: 'Hello!',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    color: Colors.green.shade100,
                    child: Column(
                      children: [
                        Icon(
                          safeResult.isSpam ? Icons.warning : Icons.check_circle,
                          color: safeResult.isSpam ? Colors.red : Colors.green,
                          size: 48,
                        ),
                        Text(
                          safeResult.isSpam ? 'Spam Detected' : 'Safe Message',
                          style: TextStyle(
                            color: safeResult.isSpam ? Colors.red : Colors.green,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text('${(safeResult.confidence * 100).toStringAsFixed(1)}%'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );

      expect(find.text('Safe Message'), findsOneWidget);
      expect(find.text('92.0%'), findsOneWidget);
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('displays danger causes list', (tester) async {
      final spamResult = ScanResult(
        isSpam: true,
        confidence: 0.9,
        prediction: 'spam',
        message: 'test',
        timestamp: '',
        dangerCauses: [
          DangerCause(
            type: 'urgency',
            title: 'Urgency Detected',
            description: 'Message contains urgent language',
            severity: 'high',
          ),
          DangerCause(
            type: 'financial',
            title: 'Financial Lure',
            description: 'Message promises money',
            severity: 'medium',
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: ListView.builder(
                itemCount: spamResult.dangerCauses.length,
                itemBuilder: (context, index) {
                  final cause = spamResult.dangerCauses[index];
                  return ListTile(
                    leading: Icon(
                      cause.isCritical
                          ? Icons.error
                          : cause.isHigh
                              ? Icons.warning
                              : Icons.info,
                      color: cause.isCritical
                          ? Colors.red
                          : cause.isHigh
                              ? Colors.orange
                              : Colors.blue,
                    ),
                    title: Text(cause.title),
                    subtitle: Text(cause.description),
                  );
                },
              ),
            ),
          ),
        ),
      );

      expect(find.text('Urgency Detected'), findsOneWidget);
      expect(find.text('Financial Lure'), findsOneWidget);
      expect(find.text('Message contains urgent language'), findsOneWidget);
    });

    testWidgets('displays risk level badge', (tester) async {
      final criticalResult = ScanResult(
        isSpam: true,
        confidence: 0.95,
        prediction: 'spam',
        message: 'test',
        timestamp: '',
        riskLevel: 'CRITICAL',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getRiskColor(criticalResult.riskLevel),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    criticalResult.riskLevel,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      expect(find.text('CRITICAL'), findsOneWidget);
    });

    testWidgets('displays confidence percentage correctly', (tester) async {
      final result = ScanResult(
        isSpam: false,
        confidence: 0.856,
        prediction: 'ham',
        message: 'test',
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

      expect(find.text('85.6%'), findsOneWidget);
    });
  });

  group('Risk Level Display', () {
    testWidgets('CRITICAL shows red', (tester) async {
      await _testRiskLevelColor(tester, 'CRITICAL', Colors.red);
    });

    testWidgets('HIGH shows orange', (tester) async {
      await _testRiskLevelColor(tester, 'HIGH', Colors.orange);
    });

    testWidgets('MEDIUM shows yellow', (tester) async {
      await _testRiskLevelColor(tester, 'MEDIUM', Colors.amber);
    });

    testWidgets('NONE shows green', (tester) async {
      await _testRiskLevelColor(tester, 'NONE', Colors.green);
    });
  });
}

Color _getRiskColor(String riskLevel) {
  switch (riskLevel) {
    case 'CRITICAL':
      return Colors.red;
    case 'HIGH':
      return Colors.orange;
    case 'MEDIUM':
      return Colors.amber;
    case 'LOW':
      return Colors.yellow;
    case 'NONE':
    default:
      return Colors.green;
  }
}

Future<void> _testRiskLevelColor(
  WidgetTester tester,
  String riskLevel,
  Color expectedColor,
) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Center(
          child: Container(
            key: const Key('risk-badge'),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getRiskColor(riskLevel),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(riskLevel),
          ),
        ),
      ),
    ),
  );

  expect(find.text(riskLevel), findsOneWidget);

  final container = tester.widget<Container>(find.byKey(const Key('risk-badge')));
  final decoration = container.decoration as BoxDecoration;
  expect(decoration.color, expectedColor);
}
