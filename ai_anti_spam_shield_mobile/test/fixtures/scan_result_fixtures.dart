import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';

/// Test fixtures for ScanResult
class ScanResultFixtures {
  /// A safe/ham scan result
  static ScanResult get safeResult => ScanResult(
        isSpam: false,
        confidence: 0.92,
        prediction: 'ham',
        message: 'Hello, how are you?',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: true,
        riskLevel: 'NONE',
        confidenceLabel: 'Safety Confidence',
        dangerCauses: [],
      );

  /// A spam scan result
  static ScanResult get spamResult => ScanResult(
        isSpam: true,
        confidence: 0.87,
        prediction: 'spam',
        message: 'URGENT: You won \$1000! Click here!',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: false,
        riskLevel: 'HIGH',
        confidenceLabel: 'Spam Confidence',
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
            description: 'Message promises money or prizes',
            severity: 'high',
          ),
        ],
      );

  /// A critical risk spam result
  static ScanResult get criticalSpamResult => ScanResult(
        isSpam: true,
        confidence: 0.95,
        prediction: 'spam',
        message: 'Your account is suspended! Verify now: http://fake.tk',
        timestamp: DateTime.now().toIso8601String(),
        isSafe: false,
        riskLevel: 'CRITICAL',
        confidenceLabel: 'Spam Confidence',
        dangerCauses: [
          DangerCause(
            type: 'phishing',
            title: 'Phishing Attempt',
            description: 'This appears to be a phishing message',
            severity: 'critical',
          ),
        ],
      );

  /// A voice scan result
  static ScanResult get voiceScanResult => ScanResult(
        isSpam: false,
        confidence: 0.88,
        prediction: 'ham',
        message: 'Transcribed voice message',
        timestamp: DateTime.now().toIso8601String(),
        transcribedText: 'Hello, this is a voice message test.',
        isVoiceScan: true,
        isSafe: true,
        riskLevel: 'NONE',
      );

  /// JSON representation of a safe result
  static Map<String, dynamic> get safeResultJson => {
        'is_spam': false,
        'confidence': 0.92,
        'prediction': 'ham',
        'message': 'Hello, how are you?',
        'timestamp': DateTime.now().toIso8601String(),
        'is_safe': true,
        'risk_level': 'NONE',
        'danger_causes': [],
        'detection_threshold': 0.65,
        'confidence_label': 'Safety Confidence',
      };

  /// JSON representation of a spam result
  static Map<String, dynamic> get spamResultJson => {
        'is_spam': true,
        'confidence': 0.87,
        'prediction': 'spam',
        'message': 'URGENT: You won \$1000! Click here!',
        'timestamp': DateTime.now().toIso8601String(),
        'is_safe': false,
        'risk_level': 'HIGH',
        'danger_causes': [
          {
            'type': 'urgency',
            'title': 'Urgency Detected',
            'description': 'Message contains urgent language',
            'severity': 'high',
          },
        ],
        'detection_threshold': 0.65,
        'confidence_label': 'Spam Confidence',
      };
}

/// Test fixtures for DangerCause
class DangerCauseFixtures {
  static DangerCause get criticalCause => DangerCause(
        type: 'phishing',
        title: 'Phishing Detected',
        description: 'This is a phishing attempt',
        severity: 'critical',
      );

  static DangerCause get highCause => DangerCause(
        type: 'urgency',
        title: 'Urgency Detected',
        description: 'Contains urgent language',
        severity: 'high',
      );

  static DangerCause get mediumCause => DangerCause(
        type: 'suspicious',
        title: 'Suspicious Content',
        description: 'Some suspicious patterns found',
        severity: 'medium',
      );

  static DangerCause get lowCause => DangerCause(
        type: 'minor',
        title: 'Minor Issue',
        description: 'A minor issue was detected',
        severity: 'low',
      );
}
