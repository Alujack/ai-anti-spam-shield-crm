import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

// Auth State
class AuthState {
  final User? user;
  final bool isLoading;
  final bool isInitialized;
  final String? error;

  AuthState({
    this.user,
    this.isLoading = false,
    this.isInitialized = false,
    this.error,
  });

  AuthState copyWith({
    User? user,
    bool? isLoading,
    bool? isInitialized,
    String? error,
    bool clearUser = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      isInitialized: isInitialized ?? this.isInitialized,
      error: error ?? this.error,
    );
  }
}

// Auth Notifier - using Riverpod 3.x Notifier
class AuthNotifier extends Notifier<AuthState> {
  late final ApiService _apiService;

  @override
  AuthState build() {
    _apiService = ApiService();
    _checkAuth();
    return AuthState();
  }

  Future<void> _checkAuth() async {
    try {
      // Check if we have a valid token and user stored
      final token = await StorageService.getToken();
      final user = await StorageService.getUser();

      if (token != null && token.isNotEmpty && user != null) {
        state = AuthState(user: user, isInitialized: true);
      } else {
        // Clear any partial data
        state = AuthState(isInitialized: true);
      }
    } catch (e) {
      state = AuthState(error: e.toString(), isInitialized: true);
    }
  }

  /// Check if user is authenticated (can be called from splash screen)
  Future<bool> checkAuthentication() async {
    if (!state.isInitialized) {
      await _checkAuth();
    }
    return state.user != null;
  }

  Future<void> login({required String email, required String password}) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final authResponse = await _apiService.login(
        email: email,
        password: password,
      );
      state = AuthState(user: authResponse.user, isLoading: false, isInitialized: true);
    } catch (e) {
      state = AuthState(isLoading: false, isInitialized: true, error: _apiService.getErrorMessage(e));
      rethrow;
    }
  }

  Future<void> register({
    required String email,
    required String password,
    String? name,
    String? phone,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final authResponse = await _apiService.register(
        email: email,
        password: password,
        name: name,
        phone: phone,
      );
      state = AuthState(user: authResponse.user, isLoading: false, isInitialized: true);
    } catch (e) {
      state = AuthState(isLoading: false, isInitialized: true, error: _apiService.getErrorMessage(e));
      rethrow;
    }
  }

  Future<void> updateProfile({String? name, String? phone}) async {
    try {
      final user = await _apiService.updateProfile(name: name, phone: phone);
      state = state.copyWith(user: user);
    } catch (e) {
      state = state.copyWith(error: _apiService.getErrorMessage(e));
      rethrow;
    }
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    await _apiService.changePassword(
      oldPassword: oldPassword,
      newPassword: newPassword,
    );
  }

  Future<void> logout() async {
    await _apiService.logout();
    state = AuthState(isInitialized: true);
  }
}

// Auth Provider - named authProvider for use in screens
final authProvider = NotifierProvider<AuthNotifier, AuthState>(() {
  return AuthNotifier();
});
