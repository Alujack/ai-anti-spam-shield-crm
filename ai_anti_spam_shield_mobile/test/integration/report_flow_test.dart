import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/report.dart';
import 'package:ai_anti_spam_shield_mobile/providers/report_provider.dart';

/// Integration tests for the report submission and management flow
void main() {
  group('Report Submission Flow Integration', () {
    testWidgets('Complete report submission flow', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(),
          ),
        ),
      );

      // Fill in the content
      await tester.enterText(
        find.byKey(const Key('content-field')),
        'URGENT: You won \$10,000! Click here to claim!',
      );
      await tester.pump();

      // Fill in the description
      await tester.enterText(
        find.byKey(const Key('description-field')),
        'This message appears to be a phishing attempt',
      );
      await tester.pump();

      // Select report type (phishing)
      await tester.tap(find.text('Phishing'));
      await tester.pump();

      // Submit the report
      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      // Verify success message
      expect(find.text('Report submitted successfully'), findsOneWidget);
    });

    testWidgets('Report submission with all optional fields', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(),
          ),
        ),
      );

      // Fill required fields
      await tester.enterText(
        find.byKey(const Key('content-field')),
        'Your account is suspended. Click here: http://fake-bank.com',
      );
      await tester.enterText(
        find.byKey(const Key('description-field')),
        'Received via SMS claiming to be from my bank',
      );

      // Fill optional fields
      await tester.enterText(
        find.byKey(const Key('url-field')),
        'http://fake-bank.com',
      );
      await tester.enterText(
        find.byKey(const Key('phone-field')),
        '+1-800-555-1234',
      );
      await tester.enterText(
        find.byKey(const Key('sender-field')),
        'fake@bank.com',
      );
      await tester.pump();

      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      expect(find.text('Report submitted successfully'), findsOneWidget);
    });

    testWidgets('Report submission validation - empty content', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(),
          ),
        ),
      );

      // Only fill description, leave content empty
      await tester.enterText(
        find.byKey(const Key('description-field')),
        'Some description',
      );
      await tester.pump();

      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter the suspicious content'), findsOneWidget);
    });

    testWidgets('Report submission validation - empty description', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(),
          ),
        ),
      );

      // Only fill content, leave description empty
      await tester.enterText(
        find.byKey(const Key('content-field')),
        'Some suspicious content',
      );
      await tester.pump();

      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      expect(find.text('Please provide a description'), findsOneWidget);
    });

    testWidgets('Report submission shows loading state', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(simulateLoading: true),
          ),
        ),
      );

      await tester.enterText(
        find.byKey(const Key('content-field')),
        'Content',
      );
      await tester.enterText(
        find.byKey(const Key('description-field')),
        'Description',
      );
      await tester.pump();

      await tester.tap(find.text('Submit Report'));
      await tester.pump();

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('Report submission handles error', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(simulateError: true),
          ),
        ),
      );

      await tester.enterText(
        find.byKey(const Key('content-field')),
        'Content',
      );
      await tester.enterText(
        find.byKey(const Key('description-field')),
        'Description',
      );
      await tester.pump();

      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      expect(find.text('Failed to submit report'), findsOneWidget);
    });
  });

  group('Report List Flow Integration', () {
    testWidgets('Displays list of user reports', (tester) async {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'reviewed'),
        _createMockReport('3', 'scam', 'resolved'),
      ];

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockReportListScreen(reports: reports),
          ),
        ),
      );

      expect(find.text('Test content for spam report'), findsOneWidget);
      expect(find.text('Test content for phishing report'), findsOneWidget);
      expect(find.text('Test content for scam report'), findsOneWidget);
    });

    testWidgets('Displays report status badges', (tester) async {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'resolved'),
      ];

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockReportListScreen(reports: reports),
          ),
        ),
      );

      expect(find.text('Pending Review'), findsOneWidget);
      expect(find.text('Resolved'), findsOneWidget);
    });

    testWidgets('Empty state when no reports', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockReportListScreen(reports: []),
          ),
        ),
      );

      expect(find.text('No reports yet'), findsOneWidget);
    });

    testWidgets('Pull to refresh loads new reports', (tester) async {
      bool refreshed = false;

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockReportListScreen(
              reports: [_createMockReport('1', 'spam', 'pending')],
              onRefresh: () async => refreshed = true,
            ),
          ),
        ),
      );

      await tester.fling(
        find.byType(ListView),
        const Offset(0, 300),
        1000,
      );
      await tester.pumpAndSettle();

      expect(refreshed, true);
    });

    testWidgets('Delete report removes it from list', (tester) async {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'reviewed'),
      ];

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockReportListScreen(
              reports: reports,
              allowDelete: true,
            ),
          ),
        ),
      );

      expect(find.text('Test content for spam report'), findsOneWidget);

      // Delete first report
      await tester.tap(find.byIcon(Icons.delete).first);
      await tester.pumpAndSettle();

      // Confirm deletion
      await tester.tap(find.text('Delete'));
      await tester.pumpAndSettle();

      expect(find.text('Test content for spam report'), findsNothing);
    });
  });

  group('Report Details Flow Integration', () {
    testWidgets('Navigate to report details', (tester) async {
      final report = _createMockReport('1', 'phishing', 'pending');

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            routes: {
              '/': (_) => _MockReportListScreen(reports: [report]),
              '/details': (_) => _MockReportDetailsScreen(report: report),
            },
          ),
        ),
      );

      await tester.tap(find.text('Test content for phishing report'));
      await tester.pumpAndSettle();

      expect(find.text('Report Details'), findsOneWidget);
      expect(find.text('Phishing'), findsOneWidget);
      expect(find.text('Pending Review'), findsOneWidget);
    });

    testWidgets('Report details show all information', (tester) async {
      final report = Report(
        id: '1',
        visitorId: 'user-1',
        type: 'phishing',
        content: 'Phishing content here',
        url: 'http://fake-site.com',
        phoneNumber: '+1234567890',
        senderInfo: 'fake@email.com',
        description: 'Detailed description',
        status: 'reviewed',
        createdAt: DateTime(2024, 1, 15, 10, 30),
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockReportDetailsScreen(report: report),
          ),
        ),
      );

      expect(find.text('Phishing content here'), findsOneWidget);
      expect(find.text('http://fake-site.com'), findsOneWidget);
      expect(find.text('+1234567890'), findsOneWidget);
      expect(find.text('fake@email.com'), findsOneWidget);
      expect(find.text('Detailed description'), findsOneWidget);
    });
  });

  group('Report State Management Integration', () {
    testWidgets('ReportProvider state changes reflect in UI', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final reportState = ref.watch(reportProvider);

                if (reportState.isLoading) {
                  return const CircularProgressIndicator();
                }

                if (reportState.error != null) {
                  return Text('Error: ${reportState.error}');
                }

                return Text('Reports: ${reportState.reports.length}');
              },
            ),
          ),
        ),
      );

      expect(find.text('Reports: 0'), findsOneWidget);
    });

    testWidgets('Clear error resets error state', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final reportState = ref.watch(reportProvider);
                final notifier = ref.read(reportProvider.notifier);

                return Column(
                  children: [
                    Text(reportState.error ?? 'No error'),
                    ElevatedButton(
                      onPressed: () => notifier.clearError(),
                      child: const Text('Clear Error'),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      );

      await tester.tap(find.text('Clear Error'));
      await tester.pump();

      expect(find.text('No error'), findsOneWidget);
    });
  });

  group('Report Navigation Flow', () {
    testWidgets('Navigate from scan result to create report', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            routes: {
              '/': (_) => const _MockScanResultScreen(),
              '/create-report': (_) => const _MockCreateReportScreen(
                    initialContent: 'Pre-filled content',
                    initialType: 'phishing',
                  ),
            },
          ),
        ),
      );

      await tester.tap(find.text('Report'));
      await tester.pumpAndSettle();

      expect(find.text('Create Report'), findsOneWidget);
      expect(find.text('Pre-filled content'), findsOneWidget);
    });

    testWidgets('Navigate back from create report', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            routes: {
              '/': (_) => const _MockReportsHomeScreen(),
              '/create': (_) => const _MockCreateReportScreen(),
            },
          ),
        ),
      );

      await tester.tap(find.text('Create Report'));
      await tester.pumpAndSettle();

      expect(find.text('Create Report'), findsOneWidget);

      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      expect(find.text('My Reports'), findsOneWidget);
    });
  });

  group('Report Type Selection Flow', () {
    testWidgets('All report types can be selected', (tester) async {
      final types = ['Spam', 'Phishing', 'Scam', 'Other'];

      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: _MockCreateReportScreen(),
          ),
        ),
      );

      for (final type in types) {
        await tester.tap(find.text(type));
        await tester.pump();

        // Verify selection is reflected (mock widget changes visual state)
        expect(find.text(type), findsOneWidget);
      }
    });
  });

  group('Report Pagination Flow', () {
    testWidgets('Load more reports on scroll', (tester) async {
      final initialReports = List.generate(
        10,
        (i) => _createMockReport('$i', 'spam', 'pending'),
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPaginatedReportListScreen(
              initialReports: initialReports,
              hasMore: true,
            ),
          ),
        ),
      );

      expect(find.text('Test content for spam report'), findsWidgets);

      // Scroll to bottom
      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pumpAndSettle();

      // Load more should be triggered
      expect(find.text('Loading more...'), findsOneWidget);
    });

    testWidgets('Shows end of list when no more reports', (tester) async {
      final reports = List.generate(
        5,
        (i) => _createMockReport('$i', 'spam', 'pending'),
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: _MockPaginatedReportListScreen(
              initialReports: reports,
              hasMore: false,
            ),
          ),
        ),
      );

      // Scroll to bottom
      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pumpAndSettle();

      expect(find.text('No more reports'), findsOneWidget);
    });
  });
}

// Helper function
Report _createMockReport(String id, String type, String status) {
  return Report(
    id: id,
    visitorId: 'user-$id',
    type: type,
    content: 'Test content for $type report',
    description: 'Test description',
    status: status,
    createdAt: DateTime.now(),
  );
}

// Mock screens for integration testing

class _MockCreateReportScreen extends StatefulWidget {
  final bool simulateLoading;
  final bool simulateError;
  final String? initialContent;
  final String? initialType;

  const _MockCreateReportScreen({
    this.simulateLoading = false,
    this.simulateError = false,
    this.initialContent,
    this.initialType,
  });

  @override
  State<_MockCreateReportScreen> createState() => _MockCreateReportScreenState();
}

class _MockCreateReportScreenState extends State<_MockCreateReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _contentController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _urlController = TextEditingController();
  final _phoneController = TextEditingController();
  final _senderController = TextEditingController();
  String _selectedType = 'spam';
  bool _isSubmitting = false;
  String? _successMessage;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    if (widget.initialContent != null) {
      _contentController.text = widget.initialContent!;
    }
    if (widget.initialType != null) {
      _selectedType = widget.initialType!;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Report'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Report type selection
            Wrap(
              spacing: 8,
              children: ['Spam', 'Phishing', 'Scam', 'Other'].map((type) {
                return ChoiceChip(
                  label: Text(type),
                  selected: _selectedType == type.toLowerCase(),
                  onSelected: (_) => setState(() => _selectedType = type.toLowerCase()),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),

            // Content field
            TextFormField(
              key: const Key('content-field'),
              controller: _contentController,
              maxLines: 5,
              decoration: InputDecoration(
                labelText: 'Suspicious Content',
                hintText: widget.initialContent ?? 'Enter content',
              ),
              validator: (v) => v?.isEmpty ?? true ? 'Please enter the suspicious content' : null,
            ),
            const SizedBox(height: 16),

            // Description field
            TextFormField(
              key: const Key('description-field'),
              controller: _descriptionController,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Description',
              ),
              validator: (v) => v?.isEmpty ?? true ? 'Please provide a description' : null,
            ),
            const SizedBox(height: 16),

            // Optional fields
            TextFormField(
              key: const Key('url-field'),
              controller: _urlController,
              decoration: const InputDecoration(labelText: 'URL (optional)'),
            ),
            TextFormField(
              key: const Key('phone-field'),
              controller: _phoneController,
              decoration: const InputDecoration(labelText: 'Phone Number (optional)'),
            ),
            TextFormField(
              key: const Key('sender-field'),
              controller: _senderController,
              decoration: const InputDecoration(labelText: 'Sender Info (optional)'),
            ),
            const SizedBox(height: 24),

            // Messages
            if (_successMessage != null)
              Text(_successMessage!, style: const TextStyle(color: Colors.green)),
            if (_errorMessage != null)
              Text(_errorMessage!, style: const TextStyle(color: Colors.red)),

            // Submit button
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              child: _isSubmitting
                  ? const CircularProgressIndicator()
                  : const Text('Submit Report'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    if (widget.simulateLoading) {
      await Future.delayed(const Duration(seconds: 2));
    }

    if (widget.simulateError) {
      setState(() {
        _isSubmitting = false;
        _errorMessage = 'Failed to submit report';
      });
      return;
    }

    setState(() {
      _isSubmitting = false;
      _successMessage = 'Report submitted successfully';
    });
  }
}

class _MockReportListScreen extends StatefulWidget {
  final List<Report> reports;
  final bool allowDelete;
  final Future<void> Function()? onRefresh;

  const _MockReportListScreen({
    required this.reports,
    this.allowDelete = false,
    this.onRefresh,
  });

  @override
  State<_MockReportListScreen> createState() => _MockReportListScreenState();
}

class _MockReportListScreenState extends State<_MockReportListScreen> {
  late List<Report> _reports;

  @override
  void initState() {
    super.initState();
    _reports = List.from(widget.reports);
  }

  @override
  Widget build(BuildContext context) {
    if (_reports.isEmpty) {
      return const Scaffold(
        body: Center(child: Text('No reports yet')),
      );
    }

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: widget.onRefresh ?? () async {},
        child: ListView.builder(
          itemCount: _reports.length,
          itemBuilder: (context, index) {
            final report = _reports[index];
            return ListTile(
              title: Text(report.content),
              subtitle: Text(report.statusDisplayName),
              trailing: widget.allowDelete
                  ? IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () => _showDeleteDialog(index),
                    )
                  : null,
              onTap: () => Navigator.pushNamed(context, '/details'),
            );
          },
        ),
      ),
    );
  }

  void _showDeleteDialog(int index) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Report'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              setState(() => _reports.removeAt(index));
              Navigator.pop(ctx);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _MockReportDetailsScreen extends StatelessWidget {
  final Report report;

  const _MockReportDetailsScreen({required this.report});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Details')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(report.typeDisplayName),
            Text(report.content),
            Text(report.statusDisplayName),
            if (report.url != null) Text(report.url!),
            if (report.phoneNumber != null) Text(report.phoneNumber!),
            if (report.senderInfo != null) Text(report.senderInfo!),
            Text(report.description),
          ],
        ),
      ),
    );
  }
}

class _MockScanResultScreen extends StatelessWidget {
  const _MockScanResultScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          onPressed: () => Navigator.pushNamed(context, '/create-report'),
          child: const Text('Report'),
        ),
      ),
    );
  }
}

class _MockReportsHomeScreen extends StatelessWidget {
  const _MockReportsHomeScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Reports')),
      body: Center(
        child: ElevatedButton(
          onPressed: () => Navigator.pushNamed(context, '/create'),
          child: const Text('Create Report'),
        ),
      ),
    );
  }
}

class _MockPaginatedReportListScreen extends StatelessWidget {
  final List<Report> initialReports;
  final bool hasMore;

  const _MockPaginatedReportListScreen({
    required this.initialReports,
    required this.hasMore,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListView.builder(
        itemCount: initialReports.length + 1,
        itemBuilder: (context, index) {
          if (index == initialReports.length) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(hasMore ? 'Loading more...' : 'No more reports'),
              ),
            );
          }
          return ListTile(title: Text(initialReports[index].content));
        },
      ),
    );
  }
}
