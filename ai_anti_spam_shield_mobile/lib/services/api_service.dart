import 'package:dio/dio.dart';
import '../models/user.dart';
import '../models/scan_result.dart';
import '../models/scan_result_v2.dart';
import '../models/scan_history.dart';
import '../models/report.dart';
import '../models/statistics.dart';
import '../models/feedback.dart';
import '../models/domain_intel.dart';
import '../utils/constants.dart';
import 'storage_service.dart';
import 'mock_api_service.dart';

/// API Service that supports both real server and demo mode
/// When AppConstants.demoMode is true, uses MockApiService
/// When false, uses real Dio HTTP client
class ApiService {
  late final Dio _dio;
  final MockApiService? _mockService;
  final bool _isDemoMode;

  ApiService() : _isDemoMode = AppConstants.demoMode,
                 _mockService = AppConstants.demoMode ? MockApiService() : null {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.baseUrl,
        connectTimeout: const Duration(milliseconds: AppConstants.timeout),
        receiveTimeout: const Duration(milliseconds: AppConstants.timeout),
        headers: {
          'Content-Type': 'application/json',
        },
      ),
    );

    // Add interceptor for auth token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await StorageService.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        // Handle errors
        return handler.next(error);
      },
    ));
  }

  // Authentication Endpoints
  Future<AuthResponse> register({
    required String email,
    required String password,
    String? name,
    String? phone,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.register(email: email, password: password, name: name, phone: phone);
    }
    try {
      final response = await _dio.post('/users/register', data: {
        'email': email,
        'password': password,
        if (name != null) 'name': name,
        if (phone != null) 'phone': phone,
      });

      final authResponse = AuthResponse.fromJson(response.data['data']);

      // Save tokens and user
      await StorageService.saveToken(authResponse.token);
      await StorageService.saveRefreshToken(authResponse.refreshToken);
      await StorageService.saveUser(authResponse.user);

      return authResponse;
    } catch (e) {
      rethrow;
    }
  }

  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.login(email: email, password: password);
    }
    try {
      final response = await _dio.post('/users/login', data: {
        'email': email,
        'password': password,
      });

      final authResponse = AuthResponse.fromJson(response.data['data']);

      // Save tokens and user
      await StorageService.saveToken(authResponse.token);
      await StorageService.saveRefreshToken(authResponse.refreshToken);
      await StorageService.saveUser(authResponse.user);

      return authResponse;
    } catch (e) {
      rethrow;
    }
  }

  Future<User> getProfile() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getProfile();
    }
    try {
      final response = await _dio.get('/users/profile');
      return User.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  Future<User> updateProfile({String? name, String? phone}) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.updateProfile(name: name, phone: phone);
    }
    try {
      final response = await _dio.put('/users/profile', data: {
        if (name != null) 'name': name,
        if (phone != null) 'phone': phone,
      });

      final user = User.fromJson(response.data['data']);
      await StorageService.saveUser(user);

      return user;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.changePassword(oldPassword: oldPassword, newPassword: newPassword);
    }
    try {
      await _dio.post('/users/change-password', data: {
        'oldPassword': oldPassword,
        'newPassword': newPassword,
      });
    } catch (e) {
      rethrow;
    }
  }

  // Message Scanning Endpoints
  Future<ScanResult> scanText(String message) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.scanText(message);
    }
    try {
      final response = await _dio.post('/messages/scan-text', data: {
        'message': message,
      });

      return ScanResult.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  Future<ScanResult> scanVoice(String audioPath) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.scanVoice(audioPath);
    }
    try {
      // Determine content type based on file extension
      final filename = audioPath.split('/').last;
      final extension = filename.split('.').last.toLowerCase();
      String contentType;
      switch (extension) {
        case 'm4a':
        case 'aac':
          contentType = 'audio/mp4';
          break;
        case 'mp3':
          contentType = 'audio/mpeg';
          break;
        case 'wav':
          contentType = 'audio/wav';
          break;
        case 'ogg':
          contentType = 'audio/ogg';
          break;
        case 'flac':
          contentType = 'audio/flac';
          break;
        case 'webm':
          contentType = 'audio/webm';
          break;
        default:
          contentType = 'audio/mpeg';
      }

      final formData = FormData.fromMap({
        'audio': await MultipartFile.fromFile(
          audioPath,
          filename: filename,
          contentType: DioMediaType.parse(contentType),
        ),
      });

      final response = await _dio.post('/messages/scan-voice', data: formData);

      return ScanResult.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getScanHistory({
    int page = 1,
    int limit = 20,
    bool? isSpam,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getScanHistory(page: page, limit: limit, isSpam: isSpam);
    }
    try {
      final response = await _dio.get(
        '/messages/history',
        queryParameters: {
          'page': page,
          'limit': limit,
          if (isSpam != null) 'isSpam': isSpam,
        },
      );

      final data = response.data['data'];
      return {
        'histories': (data['histories'] as List)
            .map((json) => ScanHistory.fromJson(json))
            .toList(),
        'pagination': data['pagination'],
      };
    } catch (e) {
      rethrow;
    }
  }

  Future<ScanHistory> getScanHistoryById(String id) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getScanHistoryById(id);
    }
    try {
      final response = await _dio.get('/messages/history/$id');
      return ScanHistory.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteScanHistory(String id) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.deleteScanHistory(id);
    }
    try {
      await _dio.delete('/messages/history/$id');
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getScanStatistics() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getScanStatistics();
    }
    try {
      final response = await _dio.get('/messages/statistics');
      return response.data['data'];
    } catch (e) {
      rethrow;
    }
  }

  // Logout
  Future<void> logout() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.logout();
    }
    await StorageService.clearAll();
  }

  // ============================================
  // PHISHING DETECTION ENDPOINTS
  // ============================================

  /// Scan text for phishing
  Future<Map<String, dynamic>> scanTextForPhishing(
    String text, {
    String scanType = 'auto',
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.scanTextForPhishing(text, scanType: scanType);
    }
    try {
      final response = await _dio.post('/phishing/scan-text', data: {
        'text': text,
        'scanType': scanType,
      });
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Scan URL for phishing
  Future<Map<String, dynamic>> scanUrlForPhishing(String url) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.scanUrlForPhishing(url);
    }
    try {
      final response = await _dio.post('/phishing/scan-url', data: {
        'url': url,
      });
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Batch scan for phishing
  Future<Map<String, dynamic>> batchScanForPhishing(
    List<String> items, {
    String scanType = 'auto',
  }) async {
    // Note: batch scan not implemented in mock, fallback to empty result
    if (_isDemoMode) {
      return {'success': true, 'data': {'results': []}};
    }
    try {
      final response = await _dio.post('/phishing/batch-scan', data: {
        'items': items,
        'scanType': scanType,
      });
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Get phishing scan history
  Future<Map<String, dynamic>> getPhishingHistory({
    int page = 1,
    int limit = 20,
    bool? phishingOnly,
    String? threatLevel,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getPhishingHistory(
        page: page,
        limit: limit,
        phishingOnly: phishingOnly,
        threatLevel: threatLevel,
      );
    }
    try {
      final response = await _dio.get(
        '/phishing/history',
        queryParameters: {
          'page': page,
          'limit': limit,
          if (phishingOnly != null) 'phishingOnly': phishingOnly,
          if (threatLevel != null) 'threatLevel': threatLevel,
        },
      );
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Get phishing scan by ID
  Future<Map<String, dynamic>> getPhishingHistoryById(String id) async {
    if (_isDemoMode) {
      return {'success': true, 'data': null};
    }
    try {
      final response = await _dio.get('/phishing/history/$id');
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Delete phishing scan from history
  Future<Map<String, dynamic>> deletePhishingHistory(String id) async {
    if (_isDemoMode) {
      return {'success': true, 'message': 'Deleted'};
    }
    try {
      final response = await _dio.delete('/phishing/history/$id');
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// Get phishing detection statistics
  Future<Map<String, dynamic>> getPhishingStatistics() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getPhishingStatistics();
    }
    try {
      final response = await _dio.get('/phishing/statistics');
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  // ============================================
  // REPORT ENDPOINTS
  // ============================================

  /// Create a new report
  Future<Report> createReport({
    required String type,
    required String content,
    required String description,
    String? url,
    String? phoneNumber,
    String? senderInfo,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.createReport(
        type: type,
        content: content,
        description: description,
        url: url,
        phoneNumber: phoneNumber,
        senderInfo: senderInfo,
      );
    }
    try {
      final response = await _dio.post('/reports', data: {
        'type': type,
        'content': content,
        'description': description,
        if (url != null) 'url': url,
        if (phoneNumber != null) 'phoneNumber': phoneNumber,
        if (senderInfo != null) 'senderInfo': senderInfo,
      });
      return Report.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  /// Get user's reports
  Future<Map<String, dynamic>> getMyReports({
    int page = 1,
    int limit = 20,
  }) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getMyReports(page: page, limit: limit);
    }
    try {
      final response = await _dio.get(
        '/reports/my-reports',
        queryParameters: {
          'page': page,
          'limit': limit,
        },
      );
      final data = response.data['data'];
      return {
        'reports': (data['reports'] as List)
            .map((json) => Report.fromJson(json))
            .toList(),
        'pagination': data['pagination'],
      };
    } catch (e) {
      rethrow;
    }
  }

  /// Get report by ID
  Future<Report> getReportById(String id) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getReportById(id);
    }
    try {
      final response = await _dio.get('/reports/$id');
      return Report.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  /// Delete report
  Future<void> deleteReport(String id) async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.deleteReport(id);
    }
    try {
      await _dio.delete('/reports/$id');
    } catch (e) {
      rethrow;
    }
  }

  /// Get report statistics
  Future<ReportSummary> getReportStatistics() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getReportStatistics();
    }
    try {
      final response = await _dio.get('/reports/statistics');
      return ReportSummary.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  // ============================================
  // DASHBOARD STATISTICS
  // ============================================

  /// Get combined dashboard statistics
  Future<DashboardStatistics> getDashboardStatistics() async {
    if (_isDemoMode && _mockService != null) {
      return _mockService.getDashboardStatistics();
    }
    try {
      // Fetch all statistics in parallel
      final results = await Future.wait([
        _dio.get('/messages/statistics'),
        _dio.get('/phishing/statistics'),
        _dio.get('/reports/statistics'),
      ]);

      return DashboardStatistics(
        scanStats: ScanStatistics.fromJson(results[0].data['data']),
        phishingStats: PhishingStatistics.fromJson(results[1].data['data']),
        reportSummary: ReportSummary.fromJson(results[2].data['data']),
      );
    } catch (e) {
      rethrow;
    }
  }

  // ============================================
  // FEEDBACK ENDPOINTS (Phase 5: Continuous Learning)
  // ============================================

  /// Submit feedback on a scan result
  Future<Feedback> submitFeedback({
    required String scanId,
    required String feedbackType, // false_positive, false_negative, confirmed
    String scanType = 'text', // text, phishing, voice
    String? actualLabel,
    String? comment,
  }) async {
    if (_isDemoMode) {
      // Return mock feedback in demo mode
      return Feedback(
        id: 'demo_${DateTime.now().millisecondsSinceEpoch}',
        scanHistoryId: scanType != 'phishing' ? scanId : null,
        phishingHistoryId: scanType == 'phishing' ? scanId : null,
        originalPrediction: 'spam',
        actualLabel: actualLabel ?? 'ham',
        feedbackType: feedbackType,
        userComment: comment,
        status: 'pending',
        createdAt: DateTime.now(),
      );
    }
    try {
      final response = await _dio.post('/feedback', data: {
        'scanId': scanId,
        'scanType': scanType,
        'feedbackType': feedbackType,
        if (actualLabel != null) 'actualLabel': actualLabel,
        if (comment != null) 'comment': comment,
      });
      return Feedback.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  /// Get user's feedback history
  Future<List<Feedback>> getMyFeedback({int page = 1, int limit = 20}) async {
    if (_isDemoMode) {
      return [];
    }
    try {
      final response = await _dio.get('/feedback/my', queryParameters: {
        'page': page,
        'limit': limit,
      });
      final data = response.data['data'];
      if (data is List) {
        return data.map((f) => Feedback.fromJson(f)).toList();
      }
      return (data['feedback'] as List?)?.map((f) => Feedback.fromJson(f)).toList() ?? [];
    } catch (e) {
      rethrow;
    }
  }

  /// Get feedback statistics
  Future<FeedbackStats> getFeedbackStats() async {
    if (_isDemoMode) {
      return FeedbackStats(
        byStatus: {'pending': 0, 'approved': 0, 'rejected': 0},
        byType: {'false_positive': 0, 'false_negative': 0, 'confirmed': 0},
        rates: FeedbackRates(falsePositiveRate: 0, falseNegativeRate: 0),
        pendingCount: 0,
      );
    }
    try {
      final response = await _dio.get('/feedback/stats');
      return FeedbackStats.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  // ============================================
  // V2 ENHANCED SCAN ENDPOINTS
  // ============================================

  /// Scan text with V2 model (enhanced with risk levels, categories)
  Future<ScanResultV2> scanTextV2(String message, {bool elderMode = false}) async {
    if (_isDemoMode) {
      // Return enhanced mock result
      final isSpam = message.toLowerCase().contains('win') ||
                     message.toLowerCase().contains('urgent') ||
                     message.toLowerCase().contains('click');
      return ScanResultV2(
        isSpam: isSpam,
        confidence: isSpam ? 0.87 : 0.12,
        prediction: isSpam ? 'spam' : 'ham',
        message: message,
        timestamp: DateTime.now().toIso8601String(),
        historyId: 'demo_${DateTime.now().millisecondsSinceEpoch}',
        riskLevel: isSpam ? RiskLevel.high : RiskLevel.none,
        scamCategory: isSpam ? ScamCategory.urgencyScam : null,
        indicators: isSpam ? [
          ThreatIndicator(
            type: 'urgency',
            source: 'text_analysis',
            description: 'Message contains urgency language',
            severity: 'medium',
          ),
        ] : [],
        elderWarnings: isSpam && elderMode ? [
          'Be cautious - this message shows signs of a scam.',
          'Never share personal information with unknown senders.',
        ] : [],
        modelVersion: 'v2.0.0-demo',
      );
    }
    try {
      final response = await _dio.post('/messages/scan-text', data: {
        'message': message,
        'elderMode': elderMode,
        'useV2': true,
      });
      return ScanResultV2.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// Scan voice with V2 model (enhanced with prosody analysis)
  Future<ScanResultV2> scanVoiceV2(String audioPath) async {
    if (_isDemoMode) {
      return ScanResultV2(
        isSpam: false,
        confidence: 0.15,
        prediction: 'ham',
        message: 'Demo voice message transcription',
        timestamp: DateTime.now().toIso8601String(),
        historyId: 'demo_voice_${DateTime.now().millisecondsSinceEpoch}',
        riskLevel: RiskLevel.none,
        transcribedText: 'This is a demo transcription of the voice message.',
        isVoiceScan: true,
        prosodyAnalysis: ProsodyAnalysis(
          durationSeconds: 5.2,
          estimatedWpm: 145,
          numPauses: 3,
          totalPauseDuration: 0.8,
          avgPauseDuration: 0.27,
          pauseRatio: 0.15,
          pitchMean: 180,
          pitchStd: 35,
          pitchRange: 120,
          energyMean: 0.05,
          energyStd: 0.02,
          indicators: ProsodyIndicators(
            speakingRate: 'normal',
            variability: 'normal',
            stress: 'normal',
          ),
        ),
        voiceScores: VoiceScores(text: 0.1, audio: 0.15, prosody: 0.12),
        modelVersion: 'voice-v2.0.0-demo',
      );
    }
    try {
      final filename = audioPath.split('/').last;
      final extension = filename.split('.').last.toLowerCase();
      String contentType;
      switch (extension) {
        case 'm4a':
        case 'aac':
          contentType = 'audio/mp4';
          break;
        case 'mp3':
          contentType = 'audio/mpeg';
          break;
        case 'wav':
          contentType = 'audio/wav';
          break;
        default:
          contentType = 'audio/mpeg';
      }

      final formData = FormData.fromMap({
        'audio': await MultipartFile.fromFile(
          audioPath,
          filename: filename,
          contentType: DioMediaType.parse(contentType),
        ),
        'useV2': true,
      });

      final response = await _dio.post('/messages/scan-voice', data: formData);
      return ScanResultV2.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  // ============================================
  // DEEP URL ANALYSIS (Phase 3: Phishing Intel)
  // ============================================

  /// Deep URL analysis with domain intelligence
  Future<DeepUrlAnalysis> analyzeUrlDeep(String url, {bool includeScreenshot = false}) async {
    if (_isDemoMode) {
      return DeepUrlAnalysis(
        url: url,
        isPhishing: url.contains('suspicious') || url.contains('login-verify'),
        confidence: 0.75,
        threatLevel: 'MEDIUM',
        domainIntel: DomainIntel(
          domain: Uri.tryParse(url)?.host ?? url,
          domainAge: DomainAge(
            creationDate: DateTime.now().subtract(const Duration(days: 45)),
            registrar: 'Demo Registrar Inc.',
            isNew: false,
            ageDays: 45,
          ),
          sslInfo: SslInfo(
            isValid: true,
            issuer: "Let's Encrypt",
            isFreeCertificate: true,
            daysUntilExpiry: 60,
          ),
          riskScore: 0.4,
          riskFactors: ['Recently registered domain', 'Free SSL certificate'],
        ),
        riskBreakdown: RiskBreakdown(
          textScore: 0.3,
          urlScore: 0.5,
          domainScore: 0.4,
          visualScore: 0.2,
          combined: 0.4,
        ),
        indicators: ['Domain registered recently', 'Uses free SSL certificate'],
        recommendations: ['Verify the sender before clicking links', 'Check the URL carefully'],
      );
    }
    try {
      final response = await _dio.post('/phishing/scan-url', data: {
        'url': url,
        'deepAnalysis': true,
        'includeScreenshot': includeScreenshot,
      });
      return DeepUrlAnalysis.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  /// Get domain intelligence for a specific domain
  Future<DomainIntel> getDomainIntel(String domain) async {
    if (_isDemoMode) {
      return DomainIntel(
        domain: domain,
        domainAge: DomainAge(
          creationDate: DateTime.now().subtract(const Duration(days: 365)),
          registrar: 'Demo Registrar',
          isNew: false,
          ageDays: 365,
        ),
        riskScore: 0.2,
      );
    }
    try {
      final response = await _dio.get('/intel/domain/$domain');
      return DomainIntel.fromJson(response.data['data']);
    } catch (e) {
      rethrow;
    }
  }

  // Error handling helper
  String getErrorMessage(dynamic error) {
    if (error is DioException) {
      if (error.response != null) {
        final message = error.response?.data['message'];
        return message ?? 'An error occurred';
      } else if (error.type == DioExceptionType.connectionTimeout) {
        return 'Connection timeout';
      } else if (error.type == DioExceptionType.receiveTimeout) {
        return 'Receive timeout';
      } else if (error.type == DioExceptionType.connectionError) {
        return 'Connection error. Please check your internet connection.';
      }
      return 'Network error occurred';
    }
    return 'An unexpected error occurred';
  }
}

