import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';
import 'package:ai_anti_spam_shield_mobile/providers/scan_provider.dart';

/// Integration tests for the scan flow
/// These tests verify the complete user flow from input to result display
void main() {
  group('Scan Flow Integration', () {
    testWidgets('Complete text scan flow displays result', (tester) async {
      // Create a mock scan result
      final mockResult = ScanResult(
        isSpam: false,
        confidence: 0.92,
        prediction: 'ham',
        message: 'Hello, how are you?',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockScanScreen(mockResult: mockResult),
          ),
        ),
      );

      // Find and fill the text input
      final textField = find.byType(TextField);
      expect(textField, findsOneWidget);

      await tester.enterText(textField, 'Hello, how are you?');
      await tester.pump();

      // Tap the scan button
      final scanButton = find.text('Scan');
      expect(scanButton, findsOneWidget);

      await tester.tap(scanButton);
      await tester.pumpAndSettle();

      // Verify result is displayed
      expect(find.text('Safe'), findsOneWidget);
      expect(find.text('92.0%'), findsOneWidget);
    });

    testWidgets('Spam detection shows warning', (tester) async {
      final spamResult = ScanResult(
        isSpam: true,
        confidence: 0.87,
        prediction: 'spam',
        message: 'URGENT: Click here!',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: false,
        riskLevel: 'HIGH',
        dangerCauses: [
          DangerCause(
            type: 'urgency',
            title: 'Urgency Detected',
            description: 'Contains urgent language',
            severity: 'high',
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockResultScreen(result: spamResult),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify spam warning is displayed
      expect(find.text('Spam'), findsOneWidget);
      expect(find.text('HIGH'), findsOneWidget);
      expect(find.text('Urgency Detected'), findsOneWidget);
    });

    testWidgets('Loading state shows progress indicator', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockLoadingScreen(),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Scanning...'), findsOneWidget);
    });

    testWidgets('Error state shows error message', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockErrorScreen(error: 'Network error occurred'),
          ),
        ),
      );

      expect(find.text('Network error occurred'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('Can navigate from result back to scan', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            initialRoute: '/',
            routes: {
              '/': (_) => const _MockHomeScreen(),
              '/result': (_) => _MockResultScreen(
                    result: ScanResult(
                      isSpam: false,
                      confidence: 0.9,
                      prediction: 'ham',
                      message: 'test',
                      timestamp: '',
                    ),
                  ),
            },
          ),
        ),
      );

      // Navigate to result
      await tester.tap(find.text('View Result'));
      await tester.pumpAndSettle();

      expect(find.text('Result'), findsOneWidget);

      // Navigate back
      await tester.tap(find.text('Scan Another'));
      await tester.pumpAndSettle();

      expect(find.text('Home'), findsOneWidget);
    });
  });

  group('State Management Integration', () {
    testWidgets('ScanProvider state changes reflect in UI', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final scanState = ref.watch(scanProvider);

                if (scanState.isLoading) {
                  return const CircularProgressIndicator();
                }

                if (scanState.error != null) {
                  return Text('Error: ${scanState.error}');
                }

                if (scanState.result != null) {
                  return Text(
                    scanState.result!.isSpam ? 'Spam' : 'Safe',
                  );
                }

                return const Text('Ready to scan');
              },
            ),
          ),
        ),
      );

      // Initial state
      expect(find.text('Ready to scan'), findsOneWidget);
    });

    testWidgets('Clear result resets state', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final scanState = ref.watch(scanProvider);
                final notifier = ref.read(scanProvider.notifier);

                return Column(
                  children: [
                    Text(scanState.result?.message ?? 'No result'),
                    ElevatedButton(
                      onPressed: () => notifier.clearResult(),
                      child: const Text('Clear'),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      );

      expect(find.text('No result'), findsOneWidget);

      await tester.tap(find.text('Clear'));
      await tester.pump();

      expect(find.text('No result'), findsOneWidget);
    });
  });
}

// Mock screens for testing

class _MockScanScreen extends StatefulWidget {
  final ScanResult mockResult;

  const _MockScanScreen({required this.mockResult});

  @override
  State<_MockScanScreen> createState() => _MockScanScreenState();
}

class _MockScanScreenState extends State<_MockScanScreen> {
  bool _showResult = false;
  final _controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    if (_showResult) {
      return Scaffold(
        body: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(widget.mockResult.isSafe ? 'Safe' : 'Spam'),
            Text('${(widget.mockResult.confidence * 100).toStringAsFixed(1)}%'),
          ],
        ),
      );
    }

    return Scaffold(
      body: Column(
        children: [
          TextField(controller: _controller),
          ElevatedButton(
            onPressed: () => setState(() => _showResult = true),
            child: const Text('Scan'),
          ),
        ],
      ),
    );
  }
}

class _MockResultScreen extends StatelessWidget {
  final ScanResult result;

  const _MockResultScreen({required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Result')),
      body: Column(
        children: [
          Text(result.isSpam ? 'Spam' : 'Safe'),
          Text(result.riskLevel),
          ...result.dangerCauses.map((c) => Text(c.title)),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Scan Another'),
          ),
        ],
      ),
    );
  }
}

class _MockLoadingScreen extends StatelessWidget {
  const _MockLoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Scanning...'),
          ],
        ),
      ),
    );
  }
}

class _MockErrorScreen extends StatelessWidget {
  final String error;

  const _MockErrorScreen({required this.error});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(error),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MockHomeScreen extends StatelessWidget {
  const _MockHomeScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: Center(
        child: ElevatedButton(
          onPressed: () => Navigator.pushNamed(context, '/result'),
          child: const Text('View Result'),
        ),
      ),
    );
  }
}
