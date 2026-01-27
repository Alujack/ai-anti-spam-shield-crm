import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/phishing_result.dart';
import 'package:ai_anti_spam_shield_mobile/providers/phishing_provider.dart';

/// Integration tests for the phishing detection flow
/// These tests verify the complete user flow from input to result display
void main() {
  group('Phishing Detection Flow Integration', () {
    testWidgets('Complete phishing text scan flow displays result', (tester) async {
      final mockResult = PhishingResult(
        isPhishing: true,
        confidence: 0.92,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.critical,
        indicators: ['Suspicious sender', 'Fake urgency'],
        urlsAnalyzed: [
          URLAnalysis(
            url: 'http://fake-bank.com',
            isSuspicious: true,
            score: 0.95,
            reasons: ['Domain mismatch'],
          ),
        ],
        brandImpersonation: BrandImpersonation(
          detected: true,
          brand: 'PayPal',
          similarityScore: 0.88,
        ),
        recommendation: 'Do not click any links',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        dangerCauses: [
          PhishingDangerCause(
            type: 'phishing',
            title: 'Phishing Attack',
            description: 'This email attempts to steal credentials',
            severity: 'critical',
          ),
        ],
        riskLevel: 'CRITICAL',
        confidenceLabel: 'Phishing Confidence',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingScanScreen(mockResult: mockResult),
          ),
        ),
      );

      // Find and fill the text input
      final textField = find.byType(TextField);
      expect(textField, findsOneWidget);

      await tester.enterText(
        textField,
        'Your PayPal account has been suspended. Click here to verify: http://fake-bank.com',
      );
      await tester.pump();

      // Tap the scan button
      final scanButton = find.text('Scan for Phishing');
      expect(scanButton, findsOneWidget);

      await tester.tap(scanButton);
      await tester.pumpAndSettle();

      // Verify result is displayed
      expect(find.text('Phishing Detected'), findsOneWidget);
      expect(find.text('CRITICAL'), findsOneWidget);
      expect(find.text('92.0%'), findsOneWidget);
    });

    testWidgets('Safe content scan shows no phishing detected', (tester) async {
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
            home: _MockPhishingScanScreen(mockResult: safeResult),
          ),
        ),
      );

      final textField = find.byType(TextField);
      await tester.enterText(textField, 'Hello, meeting tomorrow at 3pm.');
      await tester.pump();

      await tester.tap(find.text('Scan for Phishing'));
      await tester.pumpAndSettle();

      expect(find.text('Safe Content'), findsOneWidget);
      expect(find.text('NONE'), findsOneWidget);
    });

    testWidgets('URL scan detects phishing website', (tester) async {
      final phishingUrlResult = PhishingResult(
        isPhishing: true,
        confidence: 0.88,
        phishingType: PhishingType.url,
        threatLevel: ThreatLevel.high,
        indicators: ['Suspicious URL pattern'],
        urlsAnalyzed: [
          URLAnalysis(
            url: 'http://paypa1-secure.com/login',
            isSuspicious: true,
            score: 0.92,
            reasons: ['Typosquatting', 'Known phishing pattern'],
          ),
        ],
        recommendation: 'Do not visit this website',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'HIGH',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingUrlScanScreen(mockResult: phishingUrlResult),
          ),
        ),
      );

      final urlField = find.byType(TextField);
      await tester.enterText(urlField, 'http://paypa1-secure.com/login');
      await tester.pump();

      await tester.tap(find.text('Scan URL'));
      await tester.pumpAndSettle();

      expect(find.text('Phishing Detected'), findsOneWidget);
      expect(find.text('URL'), findsOneWidget);
    });

    testWidgets('Loading state shows progress indicator', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockPhishingLoadingScreen(),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Analyzing content...'), findsOneWidget);
    });

    testWidgets('Error state shows error message with retry', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockPhishingErrorScreen(error: 'AI service unavailable'),
          ),
        ),
      );

      expect(find.text('AI service unavailable'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('Retry button triggers new scan', (tester) async {
      bool retried = false;

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingErrorScreen(
              error: 'Network error',
              onRetry: () => retried = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();

      expect(retried, true);
    });

    testWidgets('Navigation from result to report screen', (tester) async {
      final result = PhishingResult(
        isPhishing: true,
        confidence: 0.9,
        phishingType: PhishingType.email,
        threatLevel: ThreatLevel.high,
        indicators: ['Suspicious content'],
        urlsAnalyzed: [],
        recommendation: 'Report this email',
        details: {},
        timestamp: '',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            routes: {
              '/': (_) => _MockPhishingResultScreen(result: result),
              '/report': (_) => const _MockReportScreen(),
            },
          ),
        ),
      );

      expect(find.text('Phishing Detected'), findsOneWidget);

      await tester.tap(find.text('Report'));
      await tester.pumpAndSettle();

      expect(find.text('Report Screen'), findsOneWidget);
    });

    testWidgets('Navigation back to scan screen', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            routes: {
              '/': (_) => const _MockPhishingScanHomeScreen(),
              '/result': (_) => _MockPhishingResultScreen(
                    result: PhishingResult(
                      isPhishing: false,
                      confidence: 0.95,
                      phishingType: PhishingType.none,
                      threatLevel: ThreatLevel.none,
                      indicators: [],
                      urlsAnalyzed: [],
                      recommendation: 'Safe',
                      details: {},
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

      expect(find.text('Safe Content'), findsOneWidget);

      // Navigate back
      await tester.tap(find.text('Scan Another'));
      await tester.pumpAndSettle();

      expect(find.text('Phishing Scanner'), findsOneWidget);
    });
  });

  group('Phishing State Management Integration', () {
    testWidgets('PhishingProvider state changes reflect in UI', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final phishingState = ref.watch(phishingProvider);

                if (phishingState.isLoading) {
                  return const CircularProgressIndicator();
                }

                if (phishingState.error != null) {
                  return Text('Error: ${phishingState.error}');
                }

                if (phishingState.result != null) {
                  return Text(
                    phishingState.result!.isPhishing
                        ? 'Phishing Detected'
                        : 'Safe Content',
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

    testWidgets('Clear result resets phishing state', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final phishingState = ref.watch(phishingProvider);
                final notifier = ref.read(phishingProvider.notifier);

                return Column(
                  children: [
                    Text(
                      phishingState.result?.recommendation ?? 'No result',
                    ),
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

    testWidgets('Reset phishing state clears all data', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final phishingState = ref.watch(phishingProvider);
                final notifier = ref.read(phishingProvider.notifier);

                return Column(
                  children: [
                    Text('History: ${phishingState.history.length}'),
                    ElevatedButton(
                      onPressed: () => notifier.reset(),
                      child: const Text('Reset'),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      );

      await tester.tap(find.text('Reset'));
      await tester.pump();

      expect(find.text('History: 0'), findsOneWidget);
    });
  });

  group('Phishing Scan History Flow', () {
    testWidgets('History list displays scan items', (tester) async {
      final histories = [
        PhishingScanHistory(
          id: 'h1',
          inputText: 'Phishing email content',
          isPhishing: true,
          confidence: 0.92,
          phishingType: PhishingType.email,
          threatLevel: ThreatLevel.critical,
          indicators: ['Fake sender'],
          brandDetected: 'PayPal',
          scannedAt: DateTime.now().subtract(const Duration(hours: 1)),
        ),
        PhishingScanHistory(
          id: 'h2',
          inputText: 'Safe message',
          isPhishing: false,
          confidence: 0.95,
          phishingType: PhishingType.none,
          threatLevel: ThreatLevel.none,
          indicators: [],
          scannedAt: DateTime.now(),
        ),
      ];

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingHistoryScreen(histories: histories),
          ),
        ),
      );

      expect(find.text('Phishing email content'), findsOneWidget);
      expect(find.text('Safe message'), findsOneWidget);
      expect(find.text('PayPal'), findsOneWidget);
    });

    testWidgets('Delete history item removes it from list', (tester) async {
      final histories = [
        PhishingScanHistory(
          id: 'h1',
          inputText: 'Item to delete',
          isPhishing: false,
          confidence: 0.9,
          phishingType: PhishingType.none,
          threatLevel: ThreatLevel.none,
          indicators: [],
          scannedAt: DateTime.now(),
        ),
      ];

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingHistoryScreen(
              histories: histories,
              allowDelete: true,
            ),
          ),
        ),
      );

      expect(find.text('Item to delete'), findsOneWidget);

      await tester.tap(find.byIcon(Icons.delete));
      await tester.pumpAndSettle();

      // After deletion, the item should not be visible
      expect(find.text('No history items'), findsOneWidget);
    });
  });

  group('SMS Phishing (Smishing) Flow', () {
    testWidgets('SMS scan detects smishing attack', (tester) async {
      final smishingResult = PhishingResult(
        isPhishing: true,
        confidence: 0.87,
        phishingType: PhishingType.sms,
        threatLevel: ThreatLevel.high,
        indicators: ['Unknown sender', 'Urgency', 'Suspicious link'],
        urlsAnalyzed: [],
        recommendation: 'Do not respond to this SMS',
        details: {},
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'HIGH',
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPhishingScanScreen(mockResult: smishingResult),
          ),
        ),
      );

      final textField = find.byType(TextField);
      await tester.enterText(
        textField,
        'URGENT: Your bank account is locked. Reply with your PIN to unlock.',
      );
      await tester.pump();

      await tester.tap(find.text('Scan for Phishing'));
      await tester.pumpAndSettle();

      expect(find.text('Phishing Detected'), findsOneWidget);
      expect(find.text('SMS'), findsOneWidget);
      expect(find.text('HIGH'), findsOneWidget);
    });
  });
}

// Mock screens for integration testing

class _MockPhishingScanScreen extends StatefulWidget {
  final PhishingResult mockResult;

  const _MockPhishingScanScreen({required this.mockResult});

  @override
  State<_MockPhishingScanScreen> createState() => _MockPhishingScanScreenState();
}

class _MockPhishingScanScreenState extends State<_MockPhishingScanScreen> {
  bool _showResult = false;
  final _controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    if (_showResult) {
      return Scaffold(
        body: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(widget.mockResult.isPhishing ? 'Phishing Detected' : 'Safe Content'),
            Text(widget.mockResult.threatLevel.displayName),
            Text(widget.mockResult.phishingType.displayName),
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
            child: const Text('Scan for Phishing'),
          ),
        ],
      ),
    );
  }
}

class _MockPhishingUrlScanScreen extends StatefulWidget {
  final PhishingResult mockResult;

  const _MockPhishingUrlScanScreen({required this.mockResult});

  @override
  State<_MockPhishingUrlScanScreen> createState() => _MockPhishingUrlScanScreenState();
}

class _MockPhishingUrlScanScreenState extends State<_MockPhishingUrlScanScreen> {
  bool _showResult = false;
  final _controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    if (_showResult) {
      return Scaffold(
        body: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(widget.mockResult.isPhishing ? 'Phishing Detected' : 'Safe URL'),
            Text(widget.mockResult.phishingType.displayName),
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
            child: const Text('Scan URL'),
          ),
        ],
      ),
    );
  }
}

class _MockPhishingLoadingScreen extends StatelessWidget {
  const _MockPhishingLoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Analyzing content...'),
          ],
        ),
      ),
    );
  }
}

class _MockPhishingErrorScreen extends StatelessWidget {
  final String error;
  final VoidCallback? onRetry;

  const _MockPhishingErrorScreen({required this.error, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(error),
            ElevatedButton(
              onPressed: onRetry ?? () {},
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MockPhishingResultScreen extends StatelessWidget {
  final PhishingResult result;

  const _MockPhishingResultScreen({required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(result.isPhishing ? 'Phishing Detected' : 'Safe Content'),
          Text(result.threatLevel.displayName),
          ElevatedButton(
            onPressed: () => Navigator.pushNamed(context, '/report'),
            child: const Text('Report'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Scan Another'),
          ),
        ],
      ),
    );
  }
}

class _MockPhishingScanHomeScreen extends StatelessWidget {
  const _MockPhishingScanHomeScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Phishing Scanner')),
      body: Center(
        child: ElevatedButton(
          onPressed: () => Navigator.pushNamed(context, '/result'),
          child: const Text('View Result'),
        ),
      ),
    );
  }
}

class _MockReportScreen extends StatelessWidget {
  const _MockReportScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Screen')),
      body: const Center(child: Text('Report Screen')),
    );
  }
}

class _MockPhishingHistoryScreen extends StatefulWidget {
  final List<PhishingScanHistory> histories;
  final bool allowDelete;

  const _MockPhishingHistoryScreen({
    required this.histories,
    this.allowDelete = false,
  });

  @override
  State<_MockPhishingHistoryScreen> createState() => _MockPhishingHistoryScreenState();
}

class _MockPhishingHistoryScreenState extends State<_MockPhishingHistoryScreen> {
  late List<PhishingScanHistory> _histories;

  @override
  void initState() {
    super.initState();
    _histories = List.from(widget.histories);
  }

  @override
  Widget build(BuildContext context) {
    if (_histories.isEmpty) {
      return const Scaffold(
        body: Center(child: Text('No history items')),
      );
    }

    return Scaffold(
      body: ListView.builder(
        itemCount: _histories.length,
        itemBuilder: (context, index) {
          final history = _histories[index];
          return ListTile(
            title: Text(history.inputText),
            subtitle: history.brandDetected != null
                ? Text(history.brandDetected!)
                : null,
            trailing: widget.allowDelete
                ? IconButton(
                    icon: const Icon(Icons.delete),
                    onPressed: () {
                      setState(() {
                        _histories.removeAt(index);
                      });
                    },
                  )
                : null,
          );
        },
      ),
    );
  }
}
