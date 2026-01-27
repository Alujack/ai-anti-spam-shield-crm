import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/providers/report_provider.dart';
import 'package:ai_anti_spam_shield_mobile/models/report.dart';

void main() {
  group('ReportState', () {
    test('initial state has empty reports and is not loading', () {
      const state = ReportState();

      expect(state.reports, isEmpty);
      expect(state.isLoading, false);
      expect(state.isSubmitting, false);
      expect(state.error, isNull);
      expect(state.currentPage, 1);
      expect(state.hasMore, true);
    });

    test('copyWith creates new state with updated values', () {
      const initialState = ReportState();
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.isLoading, true);
      expect(newState.reports, isEmpty);
      expect(newState.error, isNull);
    });

    test('copyWith preserves unmodified values', () {
      final reports = [
        _createMockReport('1', 'spam'),
        _createMockReport('2', 'phishing'),
      ];
      final initialState = ReportState(reports: reports);
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.reports, equals(reports));
      expect(newState.reports.length, 2);
      expect(newState.isLoading, true);
    });

    test('copyWith can update reports', () {
      const initialState = ReportState();
      final reports = [_createMockReport('1', 'spam')];
      final newState = initialState.copyWith(reports: reports);

      expect(newState.reports, equals(reports));
      expect(newState.reports.length, 1);
    });

    test('copyWith can update error', () {
      const initialState = ReportState();
      final newState = initialState.copyWith(error: 'Network error');

      expect(newState.error, 'Network error');
    });

    test('copyWith can update isSubmitting', () {
      const initialState = ReportState();
      final newState = initialState.copyWith(isSubmitting: true);

      expect(newState.isSubmitting, true);
      expect(newState.isLoading, false);
    });

    test('copyWith can update pagination', () {
      const initialState = ReportState();
      final newState = initialState.copyWith(
        currentPage: 3,
        hasMore: false,
      );

      expect(newState.currentPage, 3);
      expect(newState.hasMore, false);
    });

    test('copyWith clears error when null is passed', () {
      final stateWithError = const ReportState().copyWith(error: 'Some error');
      final clearedState = stateWithError.copyWith(error: null);

      expect(clearedState.error, isNull);
    });
  });

  group('ReportNotifier', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('initial state is empty', () {
      final state = container.read(reportProvider);

      expect(state.reports, isEmpty);
      expect(state.isLoading, false);
      expect(state.isSubmitting, false);
      expect(state.error, isNull);
      expect(state.currentPage, 1);
      expect(state.hasMore, true);
    });

    test('clearError clears only error', () {
      final notifier = container.read(reportProvider.notifier);

      notifier.clearError();

      final state = container.read(reportProvider);
      expect(state.error, isNull);
    });
  });

  group('ReportState with reports', () {
    test('state correctly holds spam report', () {
      final spamReport = Report(
        id: 'report-1',
        visitorId: 'user-1',
        type: 'spam',
        content: 'URGENT: You won $10,000!',
        description: 'Received this suspicious message',
        status: 'pending',
        createdAt: DateTime.now(),
      );

      final state = ReportState(reports: [spamReport]);

      expect(state.reports.length, 1);
      expect(state.reports.first.type, 'spam');
      expect(state.reports.first.typeDisplayName, 'Spam');
      expect(state.reports.first.status, 'pending');
      expect(state.reports.first.statusDisplayName, 'Pending Review');
    });

    test('state correctly holds phishing report', () {
      final phishingReport = Report(
        id: 'report-2',
        visitorId: 'user-1',
        type: 'phishing',
        content: 'Your account has been compromised',
        url: 'http://fake-bank.com',
        senderInfo: 'support@fake-bank.com',
        description: 'Email claiming to be from my bank',
        status: 'reviewed',
        createdAt: DateTime.now(),
      );

      final state = ReportState(reports: [phishingReport]);

      expect(state.reports.first.type, 'phishing');
      expect(state.reports.first.typeDisplayName, 'Phishing');
      expect(state.reports.first.url, 'http://fake-bank.com');
      expect(state.reports.first.senderInfo, 'support@fake-bank.com');
      expect(state.reports.first.statusDisplayName, 'Under Review');
    });

    test('state correctly holds scam report with phone number', () {
      final scamReport = Report(
        id: 'report-3',
        visitorId: 'user-1',
        type: 'scam',
        content: 'You need to pay taxes immediately',
        phoneNumber: '+1-800-FAKE-IRS',
        description: 'Phone call claiming to be from IRS',
        status: 'resolved',
        createdAt: DateTime.now(),
      );

      final state = ReportState(reports: [scamReport]);

      expect(state.reports.first.type, 'scam');
      expect(state.reports.first.typeDisplayName, 'Scam');
      expect(state.reports.first.phoneNumber, '+1-800-FAKE-IRS');
      expect(state.reports.first.statusDisplayName, 'Resolved');
    });

    test('state handles multiple reports', () {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'reviewed'),
        _createMockReport('3', 'scam', 'resolved'),
        _createMockReport('4', 'other', 'rejected'),
      ];

      final state = ReportState(reports: reports);

      expect(state.reports.length, 4);
      expect(state.reports[0].status, 'pending');
      expect(state.reports[1].status, 'reviewed');
      expect(state.reports[2].status, 'resolved');
      expect(state.reports[3].status, 'rejected');
    });
  });

  group('ReportState loading states', () {
    test('loading state during fetch', () {
      const loadingState = ReportState(isLoading: true);

      expect(loadingState.isLoading, true);
      expect(loadingState.isSubmitting, false);
      expect(loadingState.reports, isEmpty);
    });

    test('submitting state during report creation', () {
      const submittingState = ReportState(isSubmitting: true);

      expect(submittingState.isSubmitting, true);
      expect(submittingState.isLoading, false);
    });

    test('error state after failed operation', () {
      const errorState = ReportState(
        isLoading: false,
        error: 'Failed to load reports',
      );

      expect(errorState.isLoading, false);
      expect(errorState.error, 'Failed to load reports');
    });

    test('transition from loading to success', () {
      const loadingState = ReportState(isLoading: true);

      final reports = [_createMockReport('1', 'spam')];
      final successState = loadingState.copyWith(
        isLoading: false,
        reports: reports,
      );

      expect(successState.isLoading, false);
      expect(successState.reports.length, 1);
    });

    test('transition from submitting to success with new report', () {
      final existingReports = [_createMockReport('1', 'spam')];
      final submittingState = ReportState(
        reports: existingReports,
        isSubmitting: true,
      );

      final newReport = _createMockReport('2', 'phishing');
      final successState = submittingState.copyWith(
        isSubmitting: false,
        reports: [newReport, ...existingReports],
      );

      expect(successState.isSubmitting, false);
      expect(successState.reports.length, 2);
      expect(successState.reports.first.id, '2');
    });
  });

  group('ReportState pagination', () {
    test('initial pagination state', () {
      const state = ReportState();

      expect(state.currentPage, 1);
      expect(state.hasMore, true);
    });

    test('pagination after loading first page', () {
      final state = const ReportState().copyWith(
        reports: List.generate(20, (i) => _createMockReport('$i', 'spam')),
        currentPage: 1,
        hasMore: true,
      );

      expect(state.reports.length, 20);
      expect(state.currentPage, 1);
      expect(state.hasMore, true);
    });

    test('pagination after loading more pages', () {
      final existingReports = List.generate(20, (i) => _createMockReport('$i', 'spam'));
      final state = ReportState(
        reports: existingReports,
        currentPage: 1,
        hasMore: true,
      );

      final newReports = List.generate(20, (i) => _createMockReport('${20 + i}', 'phishing'));
      final updatedState = state.copyWith(
        reports: [...existingReports, ...newReports],
        currentPage: 2,
        hasMore: true,
      );

      expect(updatedState.reports.length, 40);
      expect(updatedState.currentPage, 2);
    });

    test('pagination reaches end', () {
      final reports = List.generate(15, (i) => _createMockReport('$i', 'spam'));
      final state = ReportState(
        reports: reports,
        currentPage: 3,
        hasMore: false,
      );

      expect(state.reports.length, 15);
      expect(state.currentPage, 3);
      expect(state.hasMore, false);
    });

    test('refresh resets pagination', () {
      final state = const ReportState(
        currentPage: 5,
        hasMore: false,
      ).copyWith(currentPage: 1, hasMore: true);

      expect(state.currentPage, 1);
      expect(state.hasMore, true);
    });
  });

  group('Report filtering by status', () {
    test('filter pending reports', () {
      final reports = [
        _createMockReport('1', 'spam', 'pending'),
        _createMockReport('2', 'phishing', 'reviewed'),
        _createMockReport('3', 'scam', 'pending'),
        _createMockReport('4', 'other', 'resolved'),
      ];

      final state = ReportState(reports: reports);
      final pendingReports = state.reports.where((r) => r.status == 'pending').toList();

      expect(pendingReports.length, 2);
    });

    test('filter resolved reports', () {
      final reports = [
        _createMockReport('1', 'spam', 'resolved'),
        _createMockReport('2', 'phishing', 'resolved'),
        _createMockReport('3', 'scam', 'pending'),
      ];

      final state = ReportState(reports: reports);
      final resolvedReports = state.reports.where((r) => r.status == 'resolved').toList();

      expect(resolvedReports.length, 2);
    });
  });

  group('Report filtering by type', () {
    test('filter spam reports', () {
      final reports = [
        _createMockReport('1', 'spam'),
        _createMockReport('2', 'phishing'),
        _createMockReport('3', 'spam'),
        _createMockReport('4', 'scam'),
      ];

      final state = ReportState(reports: reports);
      final spamReports = state.reports.where((r) => r.type == 'spam').toList();

      expect(spamReports.length, 2);
    });

    test('filter phishing reports', () {
      final reports = [
        _createMockReport('1', 'spam'),
        _createMockReport('2', 'phishing'),
        _createMockReport('3', 'phishing'),
        _createMockReport('4', 'scam'),
      ];

      final state = ReportState(reports: reports);
      final phishingReports = state.reports.where((r) => r.type == 'phishing').toList();

      expect(phishingReports.length, 2);
    });
  });

  group('Edge Cases', () {
    test('handles empty reports list', () {
      const state = ReportState(reports: []);

      expect(state.reports, isEmpty);
      expect(state.hasMore, true);
    });

    test('handles deleting a report from list', () {
      final reports = [
        _createMockReport('1', 'spam'),
        _createMockReport('2', 'phishing'),
        _createMockReport('3', 'scam'),
      ];

      final state = ReportState(reports: reports);
      final updatedState = state.copyWith(
        reports: state.reports.where((r) => r.id != '2').toList(),
      );

      expect(updatedState.reports.length, 2);
      expect(updatedState.reports.any((r) => r.id == '2'), false);
    });

    test('handles adding report to beginning', () {
      final existingReports = [
        _createMockReport('1', 'spam'),
        _createMockReport('2', 'phishing'),
      ];

      final state = ReportState(reports: existingReports);
      final newReport = _createMockReport('new', 'scam');
      final updatedState = state.copyWith(
        reports: [newReport, ...state.reports],
      );

      expect(updatedState.reports.length, 3);
      expect(updatedState.reports.first.id, 'new');
    });

    test('handles simultaneous loading and submitting states', () {
      // This shouldn't happen in practice, but state should handle it
      const state = ReportState(
        isLoading: true,
        isSubmitting: true,
      );

      expect(state.isLoading, true);
      expect(state.isSubmitting, true);
    });

    test('handles reports with all optional fields', () {
      final fullReport = Report(
        id: 'full-report',
        visitorId: 'user-full',
        type: 'phishing',
        content: 'Full phishing content',
        url: 'http://malicious.com',
        phoneNumber: '+1234567890',
        senderInfo: 'attacker@evil.com',
        description: 'Full description',
        status: 'pending',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      final state = ReportState(reports: [fullReport]);

      expect(state.reports.first.url, isNotNull);
      expect(state.reports.first.phoneNumber, isNotNull);
      expect(state.reports.first.senderInfo, isNotNull);
      expect(state.reports.first.updatedAt, isNotNull);
    });
  });
}

// Helper function to create mock reports
Report _createMockReport(String id, String type, [String status = 'pending']) {
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
