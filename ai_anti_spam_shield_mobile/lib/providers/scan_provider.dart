import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/scan_result.dart';
import '../services/api_service.dart';
import '../services/widget_service.dart';

// Scan State
class ScanState {
  final ScanResult? result;
  final bool isLoading;
  final String? error;

  ScanState({
    this.result,
    this.isLoading = false,
    this.error,
  });

  ScanState copyWith({
    ScanResult? result,
    bool? isLoading,
    String? error,
  }) {
    return ScanState(
      result: result ?? this.result,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

// Scan Provider - using Riverpod 3.x Notifier
class ScanNotifier extends Notifier<ScanState> {
  late final ApiService _apiService;

  @override
  ScanState build() {
    _apiService = ApiService();
    return ScanState();
  }

  Future<void> scanText(String message) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final result = await _apiService.scanText(message);
      state = state.copyWith(result: result, isLoading: false);

      // Update iOS Home Screen Widget with scan result
      await _updateWidget(result.isSpam);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _apiService.getErrorMessage(e),
      );
      rethrow;
    }
  }

  Future<void> scanVoice(String audioPath) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final result = await _apiService.scanVoice(audioPath);
      state = state.copyWith(result: result, isLoading: false);

      // Update iOS Home Screen Widget with scan result
      await _updateWidget(result.isSpam);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _apiService.getErrorMessage(e),
      );
      rethrow;
    }
  }

  /// Update iOS Home Screen Widget with latest scan data
  Future<void> _updateWidget(bool isSpam) async {
    try {
      final stats = await _apiService.getScanStatistics();
      await WidgetService.onScanComplete(
        isSpam: isSpam,
        totalScans: stats['totalScans'] ?? 0,
        spamDetected: stats['spamDetected'] ?? 0,
      );
    } catch (e) {
      // Widget update failure shouldn't affect the scan result
      // Just log the error silently
    }
  }

  void clearResult() {
    state = ScanState();
  }
}

final scanProvider = NotifierProvider<ScanNotifier, ScanState>(() {
  return ScanNotifier();
});

// Scan Statistics Provider
final scanStatisticsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final apiService = ApiService();
  return await apiService.getScanStatistics();
});

