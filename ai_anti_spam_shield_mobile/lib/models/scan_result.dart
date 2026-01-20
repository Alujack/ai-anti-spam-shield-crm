/// Represents a single danger cause/indicator
class DangerCause {
  final String type;
  final String title;
  final String description;
  final String severity; // 'critical', 'high', 'medium', 'low'

  DangerCause({
    required this.type,
    required this.title,
    required this.description,
    required this.severity,
  });

  factory DangerCause.fromJson(Map<String, dynamic> json) {
    return DangerCause(
      type: json['type'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      severity: json['severity'] ?? 'medium',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'title': title,
      'description': description,
      'severity': severity,
    };
  }

  /// Check if this is a critical severity issue
  bool get isCritical => severity == 'critical';

  /// Check if this is a high severity issue
  bool get isHigh => severity == 'high';
}

class ScanResult {
  final bool isSpam;
  final double confidence;
  final String prediction;
  final String message;
  final String timestamp;
  final Map<String, dynamic>? details;
  final String? transcribedText; // For voice scans
  final bool isVoiceScan; // Indicates if this was a voice scan
  final bool isSafe; // Whether the message is considered safe
  final double detectionThreshold; // The threshold used (0.65)
  final List<DangerCause> dangerCauses; // Detailed list of why it's dangerous
  final String riskLevel; // 'NONE', 'MEDIUM', 'HIGH', 'CRITICAL'
  final String confidenceLabel; // 'Spam Confidence' or 'Safety Confidence'

  ScanResult({
    required this.isSpam,
    required this.confidence,
    required this.prediction,
    required this.message,
    required this.timestamp,
    this.details,
    this.transcribedText,
    this.isVoiceScan = false,
    this.isSafe = true,
    this.detectionThreshold = 0.65,
    this.dangerCauses = const [],
    this.riskLevel = 'NONE',
    this.confidenceLabel = 'Safety Confidence',
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    final transcribed = json['transcribed_text'];
    final dangerCausesJson = json['danger_causes'] as List<dynamic>? ?? [];
    final isSpam = json['is_spam'] ?? false;

    return ScanResult(
      isSpam: isSpam,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      prediction: json['prediction'] ?? '',
      message: json['message'] ?? transcribed ?? '',
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
      details: json['details'],
      transcribedText: transcribed,
      isVoiceScan: transcribed != null,
      isSafe: json['is_safe'] ?? !isSpam,
      detectionThreshold: (json['detection_threshold'] as num?)?.toDouble() ?? 0.65,
      dangerCauses: dangerCausesJson
          .map((cause) => DangerCause.fromJson(cause as Map<String, dynamic>))
          .toList(),
      riskLevel: json['risk_level'] ?? 'NONE',
      confidenceLabel: json['confidence_label'] ?? (isSpam ? 'Spam Confidence' : 'Safety Confidence'),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'is_spam': isSpam,
      'confidence': confidence,
      'prediction': prediction,
      'message': message,
      'timestamp': timestamp,
      'details': details,
      if (transcribedText != null) 'transcribed_text': transcribedText,
      'is_voice_scan': isVoiceScan,
      'is_safe': isSafe,
      'detection_threshold': detectionThreshold,
      'danger_causes': dangerCauses.map((c) => c.toJson()).toList(),
      'risk_level': riskLevel,
      'confidence_label': confidenceLabel,
    };
  }

  /// Get the confidence as a percentage string
  String get confidencePercentage => '${(confidence * 100).toStringAsFixed(1)}%';

  /// Check if there are any critical danger causes
  bool get hasCriticalDanger => dangerCauses.any((c) => c.isCritical);

  /// Check if there are any high severity danger causes
  bool get hasHighDanger => dangerCauses.any((c) => c.isHigh);

  /// Get the count of danger causes
  int get dangerCount => dangerCauses.length;

  /// Check if this is a high-risk result (CRITICAL or HIGH)
  bool get isHighRisk => riskLevel == 'CRITICAL' || riskLevel == 'HIGH';
}

