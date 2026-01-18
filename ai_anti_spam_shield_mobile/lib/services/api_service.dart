import 'package:dio/dio.dart';
import '../models/user.dart';
import '../models/scan_result.dart';
import '../models/scan_history.dart';
import '../models/report.dart';
import '../models/statistics.dart';
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

