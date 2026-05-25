/// Phishing Detection Result Models
/// Contains data classes for phishing detection API responses
library;

/// Represents a single danger cause/indicator for phishing
class PhishingDangerCause {
  final String type;
  final String title;
  final String description;
  final String severity; // 'critical', 'high', 'medium', 'low'

  PhishingDangerCause({
    required this.type,
    required this.title,
    required this.description,
    required this.severity,
  });

  factory PhishingDangerCause.fromJson(Map<String, dynamic> json) {
    return PhishingDangerCause(
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

/// URL analysis result from phishing detection
class URLAnalysis {
  final String url;
  final bool isSuspicious;
  final double score;
  final List<String> reasons;

  URLAnalysis({
    required this.url,
    required this.isSuspicious,
    required this.score,
    required this.reasons,
  });

  factory URLAnalysis.fromJson(Map<String, dynamic> json) {
    return URLAnalysis(
      url: json['url'] ?? '',
      isSuspicious: json['isSuspicious'] ?? json['is_suspicious'] ?? false,
      score: (json['score'] ?? 0).toDouble(),
      reasons: List<String>.from(json['reasons'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'url': url,
      'is_suspicious': isSuspicious,
      'score': score,
      'reasons': reasons,
    };
  }
}

/// Brand impersonation detection result
class BrandImpersonation {
  final bool detected;
  final String? brand;
  final double similarityScore;

  BrandImpersonation({
    required this.detected,
    this.brand,
    required this.similarityScore,
  });

  factory BrandImpersonation.fromJson(Map<String, dynamic> json) {
    return BrandImpersonation(
      detected: json['detected'] ?? false,
      brand: json['brand'],
      similarityScore: (json['similarityScore'] ?? json['similarity_score'] ?? json['confidence'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'detected': detected,
      'brand': brand,
      'similarity_score': similarityScore,
    };
  }
}

/// Threat level enumeration
enum ThreatLevel {
  critical,
  high,
  medium,
  low,
  none,
}

extension ThreatLevelExtension on ThreatLevel {
  String get displayName {
    switch (this) {
      case ThreatLevel.critical:
        return 'CRITICAL';
      case ThreatLevel.high:
        return 'HIGH';
      case ThreatLevel.medium:
        return 'MEDIUM';
      case ThreatLevel.low:
        return 'LOW';
      case ThreatLevel.none:
        return 'NONE';
    }
  }

  static ThreatLevel fromString(String value) {
    switch (value.toUpperCase()) {
      case 'CRITICAL':
        return ThreatLevel.critical;
      case 'HIGH':
        return ThreatLevel.high;
      case 'MEDIUM':
        return ThreatLevel.medium;
      case 'LOW':
        return ThreatLevel.low;
      default:
        return ThreatLevel.none;
    }
  }
}

/// Phishing type enumeration
enum PhishingType {
  email,
  sms,
  url,
  none,
}

extension PhishingTypeExtension on PhishingType {
  String get displayName {
    switch (this) {
      case PhishingType.email:
        return 'EMAIL';
      case PhishingType.sms:
        return 'SMS';
      case PhishingType.url:
        return 'URL';
      case PhishingType.none:
        return 'NONE';
    }
  }

  static PhishingType fromString(String value) {
    switch (value.toUpperCase()) {
      case 'EMAIL':
        return PhishingType.email;
      case 'SMS':
      case 'SMISHING':
        return PhishingType.sms;
      case 'URL':
        return PhishingType.url;
      case 'CREDENTIAL_HARVEST':
      case 'CREDENTIAL-HARVEST':
        return PhishingType.email; // Credential harvesting is typically email-based
      default:
        return PhishingType.none;
    }
  }
}

/// Behavioral analysis from the safe-lab deep scan. Populated when the backend
/// runs the URL through a headless Chromium sandbox and Domain Intelligence
/// service. Fields default to null when the deep scan didn't run or failed.
/// A single observation the safe lab made while opening the URL. The backend
/// builds these on the Python side so the mobile just renders them.
class BehaviorFinding {
  final String severity; // 'critical' | 'high' | 'medium' | 'low'
  final String text;
  const BehaviorFinding({required this.severity, required this.text});
  factory BehaviorFinding.fromJson(Map<String, dynamic> json) => BehaviorFinding(
        severity: (json['severity'] ?? 'medium').toString(),
        text: (json['text'] ?? '').toString(),
      );
}

class DeepScan {
  final String? screenshotBase64;
  final String? pageTitle;
  final bool hasLoginForm;
  final bool hasPasswordField;
  final List<String> pageBrands;
  final num? visualRiskScore;
  final String? visualError;
  final Map<String, dynamic>? domainAge;
  final Map<String, dynamic>? sslInfo;
  final Map<String, dynamic>? asnInfo;
  final Map<String, dynamic>? dnsInfo;
  final List<String> domainRiskIndicators;
  final num? riskScore;

  // Runtime behavior observed by the safe lab
  final List<Map<String, dynamic>> permissionRequests;
  final List<Map<String, dynamic>> clipboardAttempts;
  final List<Map<String, dynamic>> forms;
  final List<Map<String, dynamic>> crossOriginFormPosts;
  final List<Map<String, dynamic>> iframes;
  final List<Map<String, dynamic>> hiddenIframes;
  final List<String> redirectChain;
  final String? finalUrl;
  final List<Map<String, dynamic>> downloads;
  final List<Map<String, dynamic>> dialogs;
  final List<String> thirdPartyScriptOrigins;
  final List<String> minerScripts;
  final List<BehaviorFinding> behaviorFindings;

  const DeepScan({
    this.screenshotBase64,
    this.pageTitle,
    this.hasLoginForm = false,
    this.hasPasswordField = false,
    this.pageBrands = const [],
    this.visualRiskScore,
    this.visualError,
    this.domainAge,
    this.sslInfo,
    this.asnInfo,
    this.dnsInfo,
    this.domainRiskIndicators = const [],
    this.riskScore,
    this.permissionRequests = const [],
    this.clipboardAttempts = const [],
    this.forms = const [],
    this.crossOriginFormPosts = const [],
    this.iframes = const [],
    this.hiddenIframes = const [],
    this.redirectChain = const [],
    this.finalUrl,
    this.downloads = const [],
    this.dialogs = const [],
    this.thirdPartyScriptOrigins = const [],
    this.minerScripts = const [],
    this.behaviorFindings = const [],
  });

  bool get hasAnySignal =>
      screenshotBase64 != null ||
      pageTitle != null ||
      hasLoginForm ||
      hasPasswordField ||
      pageBrands.isNotEmpty ||
      domainAge != null ||
      sslInfo != null ||
      domainRiskIndicators.isNotEmpty ||
      behaviorFindings.isNotEmpty ||
      permissionRequests.isNotEmpty ||
      clipboardAttempts.isNotEmpty ||
      redirectChain.length > 1 ||
      crossOriginFormPosts.isNotEmpty ||
      hiddenIframes.isNotEmpty ||
      downloads.isNotEmpty ||
      minerScripts.isNotEmpty;

  factory DeepScan.fromJson(Map<String, dynamic> json) {
    Map<String, dynamic>? asMap(dynamic v) =>
        v is Map ? Map<String, dynamic>.from(v) : null;
    List<Map<String, dynamic>> asMapList(dynamic v) => v is List
        ? v
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList()
        : <Map<String, dynamic>>[];
    List<String> asStringList(dynamic v) => v is List
        ? v.map((e) => e?.toString() ?? '').where((s) => s.isNotEmpty).toList()
        : <String>[];
    return DeepScan(
      screenshotBase64: json['screenshotBase64'] ?? json['screenshot_base64'],
      pageTitle: json['pageTitle'] ?? json['page_title'],
      hasLoginForm: json['hasLoginForm'] ?? json['has_login_form'] ?? false,
      hasPasswordField:
          json['hasPasswordField'] ?? json['has_password_field'] ?? false,
      pageBrands: asStringList(json['pageBrands'] ?? json['page_brands']),
      visualRiskScore: (json['visualRiskScore'] ?? json['visual_risk_score']) as num?,
      visualError: json['visualError'] ?? json['visual_error'],
      domainAge: asMap(json['domainAge'] ?? json['domain_age']),
      sslInfo: asMap(json['sslInfo'] ?? json['ssl_info']),
      asnInfo: asMap(json['asnInfo'] ?? json['asn_info']),
      dnsInfo: asMap(json['dnsInfo'] ?? json['dns_info']),
      domainRiskIndicators: asStringList(
          json['domainRiskIndicators'] ?? json['domain_risk_indicators']),
      riskScore: (json['riskScore'] ?? json['risk_score']) as num?,
      permissionRequests: asMapList(
          json['permissionRequests'] ?? json['permission_requests']),
      clipboardAttempts: asMapList(
          json['clipboardAttempts'] ?? json['clipboard_attempts']),
      forms: asMapList(json['forms']),
      crossOriginFormPosts: asMapList(
          json['crossOriginFormPosts'] ?? json['cross_origin_form_posts']),
      iframes: asMapList(json['iframes']),
      hiddenIframes:
          asMapList(json['hiddenIframes'] ?? json['hidden_iframes']),
      redirectChain:
          asStringList(json['redirectChain'] ?? json['redirect_chain']),
      finalUrl: json['finalUrl'] ?? json['final_url'],
      downloads: asMapList(json['downloads']),
      dialogs: asMapList(json['dialogs']),
      thirdPartyScriptOrigins: asStringList(
          json['thirdPartyScriptOrigins'] ??
              json['third_party_script_origins']),
      minerScripts:
          asStringList(json['minerScripts'] ?? json['miner_scripts']),
      behaviorFindings: (json['behaviorFindings'] ?? json['behavior_findings'] ?? [])
          is List
          ? ((json['behaviorFindings'] ?? json['behavior_findings'] ?? []) as List)
              .whereType<Map>()
              .map((e) => BehaviorFinding.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : <BehaviorFinding>[],
    );
  }
}

/// Complete phishing detection result
class PhishingResult {
  final bool isPhishing;
  final double confidence;
  final PhishingType phishingType;
  final ThreatLevel threatLevel;
  final List<String> indicators;
  final List<URLAnalysis> urlsAnalyzed;
  final BrandImpersonation? brandImpersonation;
  final String recommendation;
  final Map<String, dynamic> details;
  final String timestamp;
  final String? historyId; // For feedback submission
  final bool isSafe; // Whether the result is considered safe
  final double detectionThreshold; // The threshold used (0.65)
  final List<PhishingDangerCause> dangerCauses; // Detailed danger explanations
  final String riskLevel; // 'NONE', 'MEDIUM', 'HIGH', 'CRITICAL'
  final String confidenceLabel; // 'Phishing Confidence' or 'Safety Confidence'
  final DeepScan? deepScan; // Behavioral analysis from safe-lab Chromium sandbox

  PhishingResult({
    required this.isPhishing,
    required this.confidence,
    required this.phishingType,
    required this.threatLevel,
    required this.indicators,
    required this.urlsAnalyzed,
    this.brandImpersonation,
    required this.recommendation,
    required this.details,
    required this.timestamp,
    this.historyId,
    this.isSafe = true,
    this.detectionThreshold = 0.65,
    this.dangerCauses = const [],
    this.riskLevel = 'NONE',
    this.confidenceLabel = 'Safety Confidence',
    this.deepScan,
  });

  factory PhishingResult.fromJson(Map<String, dynamic> json) {
    final dangerCausesJson = json['danger_causes'] as List<dynamic>? ?? [];

    return PhishingResult(
      isPhishing: json['isPhishing'] ?? json['is_phishing'] ?? false,
      confidence: (json['confidence'] ?? 0).toDouble(),
      phishingType: PhishingTypeExtension.fromString(
          json['phishingType'] ?? json['phishing_type'] ?? 'NONE'),
      threatLevel: ThreatLevelExtension.fromString(
          json['threatLevel'] ?? json['threat_level'] ?? json['risk_level'] ?? 'NONE'),
      indicators: List<String>.from(json['indicators'] ?? []),
      urlsAnalyzed: (json['urlsAnalyzed'] ?? json['urls_analyzed'] ?? [])
          .map<URLAnalysis>((u) => URLAnalysis.fromJson(u))
          .toList(),
      brandImpersonation: json['brandImpersonation'] != null ||
              json['brand_impersonation'] != null
          ? BrandImpersonation.fromJson(
              json['brandImpersonation'] ?? json['brand_impersonation'])
          : null,
      recommendation: json['recommendation'] ?? '',
      details: Map<String, dynamic>.from(json['details'] ?? {}),
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
      historyId: json['historyId'] ?? json['history_id'] ?? json['id'],
      isSafe: json['is_safe'] ?? !(json['isPhishing'] ?? json['is_phishing'] ?? false),
      detectionThreshold: (json['detection_threshold'] as num?)?.toDouble() ?? 0.65,
      dangerCauses: dangerCausesJson
          .map((cause) => PhishingDangerCause.fromJson(cause as Map<String, dynamic>))
          .toList(),
      riskLevel: json['risk_level'] ?? json['threatLevel'] ?? json['threat_level'] ?? 'NONE',
      confidenceLabel: json['confidence_label'] ?? ((json['isPhishing'] ?? json['is_phishing'] ?? false) ? 'Phishing Confidence' : 'Safety Confidence'),
      deepScan: (json['deep_scan'] ?? json['deepScan']) is Map
          ? DeepScan.fromJson(Map<String, dynamic>.from(json['deep_scan'] ?? json['deepScan']))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'isPhishing': isPhishing,
      'confidence': confidence,
      'phishingType': phishingType.displayName,
      'threatLevel': threatLevel.displayName,
      'indicators': indicators,
      'urlsAnalyzed': urlsAnalyzed.map((u) => u.toJson()).toList(),
      'brandImpersonation': brandImpersonation?.toJson(),
      'recommendation': recommendation,
      'details': details,
      'timestamp': timestamp,
      'historyId': historyId,
      'is_safe': isSafe,
      'detection_threshold': detectionThreshold,
      'danger_causes': dangerCauses.map((c) => c.toJson()).toList(),
      'risk_level': riskLevel,
      'confidence_label': confidenceLabel,
    };
  }

  /// Get confidence as percentage string
  String get confidencePercentage => '${(confidence * 100).toStringAsFixed(1)}%';

  /// Check if there are any suspicious URLs
  bool get hasSuspiciousUrls => urlsAnalyzed.any((u) => u.isSuspicious);

  /// Get count of suspicious URLs
  int get suspiciousUrlCount =>
      urlsAnalyzed.where((u) => u.isSuspicious).length;

  /// Check if this is a high-risk result
  bool get isHighRisk =>
      threatLevel == ThreatLevel.critical || threatLevel == ThreatLevel.high;

  /// Check if there are any critical danger causes
  bool get hasCriticalDanger => dangerCauses.any((c) => c.isCritical);

  /// Get the count of danger causes
  int get dangerCount => dangerCauses.length;
}

/// Phishing scan history item
class PhishingScanHistory {
  final String id;
  final String inputText;
  final String? inputUrl;
  final bool isPhishing;
  final double confidence;
  final PhishingType phishingType;
  final ThreatLevel threatLevel;
  final List<String> indicators;
  final String? brandDetected;
  final DateTime scannedAt;

  PhishingScanHistory({
    required this.id,
    required this.inputText,
    this.inputUrl,
    required this.isPhishing,
    required this.confidence,
    required this.phishingType,
    required this.threatLevel,
    required this.indicators,
    this.brandDetected,
    required this.scannedAt,
  });

  factory PhishingScanHistory.fromJson(Map<String, dynamic> json) {
    return PhishingScanHistory(
      id: json['id'] ?? '',
      inputText: json['inputText'] ?? '',
      inputUrl: json['inputUrl'],
      isPhishing: json['isPhishing'] ?? false,
      confidence: (json['confidence'] ?? 0).toDouble(),
      phishingType: PhishingTypeExtension.fromString(
          json['phishingType'] ?? 'NONE'),
      threatLevel: ThreatLevelExtension.fromString(
          json['threatLevel'] ?? 'NONE'),
      indicators: List<String>.from(json['indicators'] ?? []),
      brandDetected: json['brandDetected'],
      scannedAt: json['scannedAt'] != null
          ? DateTime.parse(json['scannedAt'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'inputText': inputText,
      'inputUrl': inputUrl,
      'isPhishing': isPhishing,
      'confidence': confidence,
      'phishingType': phishingType.displayName,
      'threatLevel': threatLevel.displayName,
      'indicators': indicators,
      'brandDetected': brandDetected,
      'scannedAt': scannedAt.toIso8601String(),
    };
  }

  /// Get confidence as percentage string
  String get confidencePercentage => '${(confidence * 100).toStringAsFixed(1)}%';

  /// Get truncated input text for display
  String get displayText =>
      inputText.length > 100 ? '${inputText.substring(0, 100)}...' : inputText;
}

/// Phishing statistics
class PhishingStatistics {
  final int totalScans;
  final int phishingDetected;
  final int safeScans;
  final double phishingPercentage;
  final Map<String, int> threatLevels;

  PhishingStatistics({
    required this.totalScans,
    required this.phishingDetected,
    required this.safeScans,
    required this.phishingPercentage,
    required this.threatLevels,
  });

  factory PhishingStatistics.fromJson(Map<String, dynamic> json) {
    return PhishingStatistics(
      totalScans: json['totalScans'] ?? 0,
      phishingDetected: json['phishingDetected'] ?? 0,
      safeScans: json['safeScans'] ?? 0,
      phishingPercentage: (json['phishingPercentage'] is String)
          ? double.tryParse(json['phishingPercentage']) ?? 0
          : (json['phishingPercentage'] ?? 0).toDouble(),
      threatLevels: Map<String, int>.from(json['threatLevels'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'totalScans': totalScans,
      'phishingDetected': phishingDetected,
      'safeScans': safeScans,
      'phishingPercentage': phishingPercentage,
      'threatLevels': threatLevels,
    };
  }
}

/// Batch phishing scan result
class BatchPhishingResult {
  final List<PhishingResult> results;
  final int total;
  final int phishingDetected;
  final int safe;
  final Map<String, int> threatLevels;
  final String timestamp;

  BatchPhishingResult({
    required this.results,
    required this.total,
    required this.phishingDetected,
    required this.safe,
    required this.threatLevels,
    required this.timestamp,
  });

  factory BatchPhishingResult.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] ?? {};
    return BatchPhishingResult(
      results: (json['results'] ?? [])
          .map<PhishingResult>((r) => PhishingResult.fromJson(r))
          .toList(),
      total: summary['total'] ?? 0,
      phishingDetected: summary['phishing_detected'] ?? summary['phishingDetected'] ?? 0,
      safe: summary['safe'] ?? 0,
      threatLevels: Map<String, int>.from(summary['threat_levels'] ?? summary['threatLevels'] ?? {}),
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
    );
  }
}
