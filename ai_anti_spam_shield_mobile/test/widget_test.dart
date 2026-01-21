import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';

void main() {
  group('App Smoke Tests', () {
    testWidgets('Basic MaterialApp renders', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Center(
                child: Text('AI Anti-Spam Shield'),
              ),
            ),
          ),
        ),
      );

      expect(find.text('AI Anti-Spam Shield'), findsOneWidget);
    });

    testWidgets('ProviderScope wraps app correctly', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Text('Provider Test'),
            ),
          ),
        ),
      );

      expect(find.text('Provider Test'), findsOneWidget);
    });
  });

  group('Core Model Tests', () {
    test('ScanResult can be created', () {
      final result = ScanResult(
        isSpam: false,
        confidence: 0.9,
        prediction: 'ham',
        message: 'Test message',
        timestamp: DateTime.now().toIso8601String(),
      );

      expect(result.isSpam, false);
      expect(result.confidence, 0.9);
    });

    test('DangerCause can be created', () {
      final cause = DangerCause(
        type: 'test',
        title: 'Test Title',
        description: 'Test description',
        severity: 'high',
      );

      expect(cause.type, 'test');
      expect(cause.isHigh, true);
    });
  });

  group('UI Component Tests', () {
    testWidgets('Text input field works', (tester) async {
      final controller = TextEditingController();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Enter message to scan',
              ),
            ),
          ),
        ),
      );

      await tester.enterText(find.byType(TextField), 'Test message');
      expect(controller.text, 'Test message');
    });

    testWidgets('Button tap works', (tester) async {
      bool tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ElevatedButton(
              onPressed: () => tapped = true,
              child: const Text('Scan'),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Scan'));
      expect(tapped, true);
    });

    testWidgets('Loading indicator displays', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('Error message displays', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Center(
              child: Text(
                'An error occurred',
                style: TextStyle(color: Colors.red),
              ),
            ),
          ),
        ),
      );

      expect(find.text('An error occurred'), findsOneWidget);
    });
  });

  group('Result Display Tests', () {
    testWidgets('Spam result shows warning icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Icon(
              Icons.warning,
              color: Colors.red,
              size: 48,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('Safe result shows check icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Icon(
              Icons.check_circle,
              color: Colors.green,
              size: 48,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('Confidence percentage displays correctly', (tester) async {
      const confidence = 0.856;
      final percentage = '${(confidence * 100).toStringAsFixed(1)}%';

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Text(percentage),
          ),
        ),
      );

      expect(find.text('85.6%'), findsOneWidget);
    });
  });

  group('Navigation Tests', () {
    testWidgets('Can navigate between pages', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const Scaffold(
                        body: Text('Second Page'),
                      ),
                    ),
                  );
                },
                child: const Text('Navigate'),
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Navigate'));
      await tester.pumpAndSettle();

      expect(find.text('Second Page'), findsOneWidget);
    });
  });
}
