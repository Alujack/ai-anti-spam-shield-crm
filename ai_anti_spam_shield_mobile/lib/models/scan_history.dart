class ScanHistory {
  final String id;
  final String message;
  final bool isSpam;
  final double confidence;
  final String prediction;
  final DateTime scannedAt;
  final Map<String, dynamic>? details;

  ScanHistory({
    required this.id,
    required this.message,
    required this.isSpam,
    required this.confidence,
    required this.prediction,
    required this.scannedAt,
    this.details,
  });

  factory ScanHistory.fromJson(Map<String, dynamic> json) {
    // Handle details field - it might be a JSON string from the backend
    Map<String, dynamic>? detailsMap;
    if (json['details'] != null) {
      if (json['details'] is Map) {
        detailsMap = Map<String, dynamic>.from(json['details']);
      } else if (json['details'] is String && json['details'].isNotEmpty) {
        try {
          final parsed = json['details'];
          if (parsed is Map) {
            detailsMap = Map<String, dynamic>.from(parsed);
          }
        } catch (_) {
          detailsMap = null;
        }
      }
    }

    return ScanHistory(
      id: json['id']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      isSpam: json['isSpam'] == true,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      prediction: json['prediction']?.toString() ?? '',
      scannedAt: json['scannedAt'] != null
          ? DateTime.tryParse(json['scannedAt'].toString()) ?? DateTime.now()
          : DateTime.now(),
      details: detailsMap,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'message': message,
      'isSpam': isSpam,
      'confidence': confidence,
      'prediction': prediction,
      'scannedAt': scannedAt.toIso8601String(),
      'details': details,
    };
  }
}

