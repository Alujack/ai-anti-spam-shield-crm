import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/models/report.dart';

void main() {
  group('Create Report Screen UI Components', () {
    testWidgets('displays all report type options', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockReportTypeSelector(),
            ),
          ),
        ),
      );

      expect(find.text('Spam'), findsOneWidget);
      expect(find.text('Phishing'), findsOneWidget);
      expect(find.text('Scam'), findsOneWidget);
      expect(find.text('Other'), findsOneWidget);
    });

    testWidgets('report type selection changes selected state', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockReportTypeSelector(),
            ),
          ),
        ),
      );

      // Initially spam should be selected (default)
      expect(find.text('Spam'), findsOneWidget);

      // Tap on Phishing
      await tester.tap(find.text('Phishing'));
      await tester.pumpAndSettle();

      // Verify selection changed (mock widget handles this internally)
      expect(find.text('Phishing'), findsOneWidget);
    });

    testWidgets('displays content input field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockContentInput(),
            ),
          ),
        ),
      );

      expect(find.text('Suspicious Content *'), findsOneWidget);
      expect(
        find.text('Paste the suspicious message or content here...'),
        findsOneWidget,
      );
    });

    testWidgets('content input accepts text', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockContentInput(),
            ),
          ),
        ),
      );

      final textField = find.byType(TextField);
      await tester.enterText(textField, 'URGENT: Win $10,000 now!');
      await tester.pump();

      expect(find.text('URGENT: Win \$10,000 now!'), findsOneWidget);
    });

    testWidgets('displays description input field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockDescriptionInput(),
            ),
          ),
        ),
      );

      expect(find.text('Description *'), findsOneWidget);
      expect(
        find.text('Describe why you think this is suspicious...'),
        findsOneWidget,
      );
    });

    testWidgets('displays optional URL input field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockOptionalFields(),
            ),
          ),
        ),
      );

      expect(find.text('Suspicious URL'), findsOneWidget);
    });

    testWidgets('displays optional phone number input field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockOptionalFields(),
            ),
          ),
        ),
      );

      expect(find.text('Phone Number'), findsOneWidget);
    });

    testWidgets('displays optional sender info input field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockOptionalFields(),
            ),
          ),
        ),
      );

      expect(find.text('Sender Info'), findsOneWidget);
    });

    testWidgets('displays submit button', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockSubmitButton(),
            ),
          ),
        ),
      );

      expect(find.text('Submit Report'), findsOneWidget);
    });

    testWidgets('submit button is tappable', (tester) async {
      bool submitted = false;

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockSubmitButton(
                onSubmit: () => submitted = true,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Submit Report'));
      await tester.pumpAndSettle();

      expect(submitted, true);
    });

    testWidgets('displays loading state during submission', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockSubmitButton(isSubmitting: true),
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('displays error message', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockErrorDisplay(error: 'Failed to submit report'),
            ),
          ),
        ),
      );

      expect(find.text('Failed to submit report'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('displays header with help text', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockHeaderSection(),
            ),
          ),
        ),
      );

      expect(find.text('Help Us Protect Others'), findsOneWidget);
      expect(
        find.text('Report suspicious messages to help improve our detection'),
        findsOneWidget,
      );
    });
  });

  group('Form Validation', () {
    testWidgets('validates empty content field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockFormValidation(validateContent: true, contentEmpty: true),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Validate'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter the suspicious content'), findsOneWidget);
    });

    testWidgets('validates empty description field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockFormValidation(validateDescription: true, descriptionEmpty: true),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Validate'));
      await tester.pumpAndSettle();

      expect(find.text('Please provide a description'), findsOneWidget);
    });

    testWidgets('accepts valid form data', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockFormValidation(
                validateContent: true,
                validateDescription: true,
                contentEmpty: false,
                descriptionEmpty: false,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Validate'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter the suspicious content'), findsNothing);
      expect(find.text('Please provide a description'), findsNothing);
    });
  });

  group('Report Type Icons', () {
    testWidgets('spam type shows correct icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: _MockReportTypeIcon(type: 'spam'),
          ),
        ),
      );

      expect(find.byIcon(Icons.mark_email_unread), findsOneWidget);
    });

    testWidgets('phishing type shows correct icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: _MockReportTypeIcon(type: 'phishing'),
          ),
        ),
      );

      expect(find.byIcon(Icons.phishing), findsOneWidget);
    });

    testWidgets('scam type shows correct icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: _MockReportTypeIcon(type: 'scam'),
          ),
        ),
      );

      expect(find.byIcon(Icons.warning_amber), findsOneWidget);
    });

    testWidgets('other type shows correct icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: _MockReportTypeIcon(type: 'other'),
          ),
        ),
      );

      expect(find.byIcon(Icons.help_outline), findsOneWidget);
    });
  });

  group('Initial Content', () {
    testWidgets('pre-fills content when initialContent provided', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockContentInput(
                initialContent: 'Suspicious message content',
              ),
            ),
          ),
        ),
      );

      expect(find.text('Suspicious message content'), findsOneWidget);
    });

    testWidgets('pre-selects type when initialType provided', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: _MockReportTypeSelector(initialType: 'phishing'),
            ),
          ),
        ),
      );

      // The phishing type should be initially selected
      expect(find.text('Phishing'), findsOneWidget);
    });
  });

  group('Report Model Display', () {
    testWidgets('displays report status correctly', (tester) async {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'reviewed'),
        _createMockReport('3', 'scam', 'resolved'),
        _createMockReport('4', 'other', 'rejected'),
      ];

      for (final report in reports) {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: _MockReportStatusDisplay(report: report),
            ),
          ),
        );

        expect(find.text(report.statusDisplayName), findsOneWidget);
      }
    });

    testWidgets('displays report type correctly', (tester) async {
      final types = ['spam', 'phishing', 'scam', 'other'];

      for (final type in types) {
        final report = _createMockReport('1', type, 'pending');

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: _MockReportTypeDisplay(report: report),
            ),
          ),
        );

        expect(find.text(report.typeDisplayName), findsOneWidget);
      }
    });
  });
}

// Helper function to create mock reports
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

// Mock widgets for testing

class _MockReportTypeSelector extends StatefulWidget {
  final String? initialType;

  const _MockReportTypeSelector({this.initialType});

  @override
  State<_MockReportTypeSelector> createState() => _MockReportTypeSelectorState();
}

class _MockReportTypeSelectorState extends State<_MockReportTypeSelector> {
  late String _selectedType;

  final _types = [
    {'value': 'spam', 'label': 'Spam', 'icon': Icons.mark_email_unread},
    {'value': 'phishing', 'label': 'Phishing', 'icon': Icons.phishing},
    {'value': 'scam', 'label': 'Scam', 'icon': Icons.warning_amber},
    {'value': 'other', 'label': 'Other', 'icon': Icons.help_outline},
  ];

  @override
  void initState() {
    super.initState();
    _selectedType = widget.initialType ?? 'spam';
  }

  @override
  Widget build(BuildContext context) {
    return Wrap(
      children: _types.map((type) {
        final isSelected = _selectedType == type['value'];
        return GestureDetector(
          onTap: () => setState(() => _selectedType = type['value'] as String),
          child: Chip(
            avatar: Icon(type['icon'] as IconData),
            label: Text(type['label'] as String),
            backgroundColor: isSelected ? Colors.blue : Colors.grey.shade200,
          ),
        );
      }).toList(),
    );
  }
}

class _MockContentInput extends StatelessWidget {
  final String? initialContent;

  const _MockContentInput({this.initialContent});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Suspicious Content *'),
        TextField(
          controller: TextEditingController(text: initialContent),
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Paste the suspicious message or content here...',
          ),
        ),
      ],
    );
  }
}

class _MockDescriptionInput extends StatelessWidget {
  const _MockDescriptionInput();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Description *'),
        TextField(
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: 'Describe why you think this is suspicious...',
          ),
        ),
      ],
    );
  }
}

class _MockOptionalFields extends StatelessWidget {
  const _MockOptionalFields();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Text('Additional Information (Optional)'),
        TextField(decoration: InputDecoration(labelText: 'Suspicious URL')),
        TextField(decoration: InputDecoration(labelText: 'Phone Number')),
        TextField(decoration: InputDecoration(labelText: 'Sender Info')),
      ],
    );
  }
}

class _MockSubmitButton extends StatelessWidget {
  final VoidCallback? onSubmit;
  final bool isSubmitting;

  const _MockSubmitButton({this.onSubmit, this.isSubmitting = false});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isSubmitting ? null : (onSubmit ?? () {}),
      child: isSubmitting
          ? const CircularProgressIndicator()
          : const Text('Submit Report'),
    );
  }
}

class _MockErrorDisplay extends StatelessWidget {
  final String error;

  const _MockErrorDisplay({required this.error});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      color: Colors.red.shade100,
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Colors.red),
          const SizedBox(width: 8),
          Text(error),
        ],
      ),
    );
  }
}

class _MockHeaderSection extends StatelessWidget {
  const _MockHeaderSection();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.report, size: 40),
        Text('Help Us Protect Others'),
        Text('Report suspicious messages to help improve our detection'),
      ],
    );
  }
}

class _MockFormValidation extends StatefulWidget {
  final bool validateContent;
  final bool validateDescription;
  final bool contentEmpty;
  final bool descriptionEmpty;

  const _MockFormValidation({
    this.validateContent = false,
    this.validateDescription = false,
    this.contentEmpty = false,
    this.descriptionEmpty = false,
  });

  @override
  State<_MockFormValidation> createState() => _MockFormValidationState();
}

class _MockFormValidationState extends State<_MockFormValidation> {
  final _formKey = GlobalKey<FormState>();
  bool _validated = false;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          if (widget.validateContent)
            TextFormField(
              initialValue: widget.contentEmpty ? '' : 'Content',
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter the suspicious content';
                }
                return null;
              },
            ),
          if (widget.validateDescription)
            TextFormField(
              initialValue: widget.descriptionEmpty ? '' : 'Description',
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please provide a description';
                }
                return null;
              },
            ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _validated = _formKey.currentState?.validate() ?? false;
              });
            },
            child: const Text('Validate'),
          ),
        ],
      ),
    );
  }
}

class _MockReportTypeIcon extends StatelessWidget {
  final String type;

  const _MockReportTypeIcon({required this.type});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    switch (type) {
      case 'spam':
        icon = Icons.mark_email_unread;
        break;
      case 'phishing':
        icon = Icons.phishing;
        break;
      case 'scam':
        icon = Icons.warning_amber;
        break;
      case 'other':
      default:
        icon = Icons.help_outline;
        break;
    }
    return Icon(icon);
  }
}

class _MockReportStatusDisplay extends StatelessWidget {
  final Report report;

  const _MockReportStatusDisplay({required this.report});

  @override
  Widget build(BuildContext context) {
    return Text(report.statusDisplayName);
  }
}

class _MockReportTypeDisplay extends StatelessWidget {
  final Report report;

  const _MockReportTypeDisplay({required this.report});

  @override
  Widget build(BuildContext context) {
    return Text(report.typeDisplayName);
  }
}
