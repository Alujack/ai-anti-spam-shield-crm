import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ai_anti_spam_shield_mobile/providers/scan_provider.dart';
import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';

void main() {
  group('ScanState', () {
    test('initial state has no result and is not loading', () {
      final state = ScanState();

      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
    });

    test('copyWith creates new state with updated values', () {
      final initialState = ScanState();
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.isLoading, true);
      expect(newState.result, isNull);
      expect(newState.error, isNull);
    });

    test('copyWith preserves unmodified values', () {
      final result = ScanResult(
        isSpam: false,
        confidence: 0.9,
        prediction: 'ham',
        message: 'test',
        timestamp: '',
      );
      final initialState = ScanState(result: result);
      final newState = initialState.copyWith(isLoading: true);

      expect(newState.result, equals(result));
      expect(newState.isLoading, true);
    });

    test('copyWith can update result', () {
      final result = ScanResult(
        isSpam: true,
        confidence: 0.85,
        prediction: 'spam',
        message: 'spam message',
        timestamp: '',
      );
      final initialState = ScanState();
      final newState = initialState.copyWith(result: result);

      expect(newState.result, equals(result));
      expect(newState.result!.isSpam, true);
    });

    test('copyWith can update error', () {
      final initialState = ScanState();
      final newState = initialState.copyWith(error: 'Network error');

      expect(newState.error, 'Network error');
    });
  });

  group('ScanNotifier', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('initial state is empty', () {
      final state = container.read(scanProvider);

      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
    });

    test('clearResult resets state to initial', () {
      // Get the notifier
      final notifier = container.read(scanProvider.notifier);

      // Clear the result
      notifier.clearResult();

      // Verify state is reset
      final state = container.read(scanProvider);
      expect(state.result, isNull);
      expect(state.isLoading, false);
      expect(state.error, isNull);
    });
  });

  group('ScanResult integration with ScanState', () {
    test('state correctly holds spam result', () {
      final spamResult = ScanResult(
        isSpam: true,
        confidence: 0.87,
        prediction: 'spam',
        message: 'URGENT: Click here!',
        timestamp: DateTime.now().toIso8601String(),
        riskLevel: 'HIGH',
        dangerCauses: [
          DangerCause(
            type: 'urgency',
            title: 'Urgency',
            description: 'Contains urgent language',
            severity: 'high',
          ),
        ],
      );

      final state = ScanState(result: spamResult);

      expect(state.result!.isSpam, true);
      expect(state.result!.isHighRisk, true);
      expect(state.result!.dangerCauses.length, 1);
    });

    test('state correctly holds safe result', () {
      final safeResult = ScanResult(
        isSpam: false,
        confidence: 0.92,
        prediction: 'ham',
        message: 'Hello, how are you?',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
      );

      final state = ScanState(result: safeResult);

      expect(state.result!.isSpam, false);
      expect(state.result!.isSafe, true);
      expect(state.result!.isHighRisk, false);
    });
  });
}
