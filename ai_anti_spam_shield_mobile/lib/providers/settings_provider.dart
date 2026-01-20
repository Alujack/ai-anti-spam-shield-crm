import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class AppSettingsState {
  final ThemeMode themeMode;
  final bool notificationsEnabled;
  final bool elderModeEnabled; // Phase 2: Elder-friendly warnings
  final bool isLoading;

  const AppSettingsState({
    this.themeMode = ThemeMode.system,
    this.notificationsEnabled = true,
    this.elderModeEnabled = false,
    this.isLoading = false,
  });

  AppSettingsState copyWith({
    ThemeMode? themeMode,
    bool? notificationsEnabled,
    bool? elderModeEnabled,
    bool? isLoading,
  }) {
    return AppSettingsState(
      themeMode: themeMode ?? this.themeMode,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      elderModeEnabled: elderModeEnabled ?? this.elderModeEnabled,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  bool get isDarkMode => themeMode == ThemeMode.dark;
}

class AppSettingsNotifier extends Notifier<AppSettingsState> {
  @override
  AppSettingsState build() {
    // Load settings after initialization
    Future.microtask(() => _loadSettings());
    return const AppSettingsState(isLoading: true);
  }

  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Load theme mode
      final themeModeString = prefs.getString(AppConstants.themeModeKey);
      ThemeMode themeMode = ThemeMode.system;
      if (themeModeString == 'dark') {
        themeMode = ThemeMode.dark;
      } else if (themeModeString == 'light') {
        themeMode = ThemeMode.light;
      }

      // Load notifications preference
      final notificationsEnabled =
          prefs.getBool(AppConstants.notificationsEnabledKey) ?? true;

      // Load elder mode preference
      final elderModeEnabled =
          prefs.getBool('elder_mode_enabled') ?? false;

      state = state.copyWith(
        themeMode: themeMode,
        notificationsEnabled: notificationsEnabled,
        elderModeEnabled: elderModeEnabled,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false);
    }
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      String themeModeString;
      switch (mode) {
        case ThemeMode.dark:
          themeModeString = 'dark';
          break;
        case ThemeMode.light:
          themeModeString = 'light';
          break;
        default:
          themeModeString = 'system';
      }
      await prefs.setString(AppConstants.themeModeKey, themeModeString);
      state = state.copyWith(themeMode: mode);
    } catch (e) {
      // Handle error silently
    }
  }

  Future<void> toggleDarkMode(bool enabled) async {
    await setThemeMode(enabled ? ThemeMode.dark : ThemeMode.light);
  }

  Future<void> setNotificationsEnabled(bool enabled) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(AppConstants.notificationsEnabledKey, enabled);
      state = state.copyWith(notificationsEnabled: enabled);
    } catch (e) {
      // Handle error silently
    }
  }

  /// Toggle elder mode for simplified warnings
  Future<void> setElderModeEnabled(bool enabled) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('elder_mode_enabled', enabled);
      state = state.copyWith(elderModeEnabled: enabled);
    } catch (e) {
      // Handle error silently
    }
  }
}

final appSettingsProvider =
    NotifierProvider<AppSettingsNotifier, AppSettingsState>(
  () => AppSettingsNotifier(),
);
