import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Creates a testable widget wrapped with necessary providers
Widget createTestWidget(
  Widget child, {
  List<ProviderOrFamily>? overrides,
  ThemeData? theme,
}) {
  return ProviderScope(
    overrides: overrides?.cast<Override>() ?? [],
    child: MaterialApp(
      theme: theme ?? ThemeData.light(),
      home: Scaffold(body: child),
    ),
  );
}

/// Creates a full app wrapper for testing screens
Widget createTestApp(
  Widget child, {
  List<ProviderOrFamily>? overrides,
  ThemeData? theme,
  String? initialRoute,
}) {
  return ProviderScope(
    overrides: overrides?.cast<Override>() ?? [],
    child: MaterialApp(
      theme: theme ?? ThemeData.light(),
      home: child,
      initialRoute: initialRoute,
    ),
  );
}

/// Extension on WidgetTester for common test operations
extension WidgetTesterExtension on WidgetTester {
  /// Pumps the widget with provider scope
  Future<void> pumpApp(
    Widget widget, {
    List<ProviderOrFamily>? overrides,
  }) async {
    await pumpWidget(createTestWidget(widget, overrides: overrides));
    await pump();
  }

  /// Pumps and settles with timeout
  Future<void> pumpAndSettleWithTimeout({
    Duration timeout = const Duration(seconds: 10),
  }) async {
    await pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      timeout,
    );
  }

  /// Enters text in a text field
  Future<void> enterTextInField(Finder finder, String text) async {
    await tap(finder);
    await pump();
    await enterText(finder, text);
    await pump();
  }
}

/// Test data factory for common test objects
class TestDataFactory {
  static Map<String, dynamic> createScanResultJson({
    bool isSpam = false,
    double confidence = 0.85,
    String prediction = 'ham',
    String message = 'Test message',
    String riskLevel = 'NONE',
    List<Map<String, dynamic>>? dangerCauses,
  }) {
    return {
      'is_spam': isSpam,
      'confidence': confidence,
      'prediction': prediction,
      'message': message,
      'timestamp': DateTime.now().toIso8601String(),
      'is_safe': !isSpam,
      'risk_level': riskLevel,
      'danger_causes': dangerCauses ?? [],
      'detection_threshold': 0.65,
      'confidence_label': isSpam ? 'Spam Confidence' : 'Safety Confidence',
    };
  }

  static Map<String, dynamic> createPhishingResultJson({
    bool isPhishing = false,
    double confidence = 0.85,
    String threatLevel = 'NONE',
    List<String>? indicators,
  }) {
    return {
      'is_phishing': isPhishing,
      'confidence': confidence,
      'threat_level': threatLevel,
      'phishing_type': isPhishing ? 'EMAIL' : 'NONE',
      'indicators': indicators ?? [],
      'urls_analyzed': [],
      'brand_impersonation': null,
      'recommendation': isPhishing ? 'Be cautious' : 'Safe',
      'is_safe': !isPhishing,
      'danger_causes': [],
    };
  }

  static Map<String, dynamic> createUserJson({
    String id = 'test-user-id',
    String email = 'test@example.com',
    String name = 'Test User',
    String role = 'USER',
  }) {
    return {
      'id': id,
      'email': email,
      'name': name,
      'role': role,
      'createdAt': DateTime.now().toIso8601String(),
    };
  }
}
