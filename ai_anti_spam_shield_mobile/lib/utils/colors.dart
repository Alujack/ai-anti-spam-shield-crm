import 'package:flutter/material.dart';

/// App Color Palette
/// A premium, professional color scheme designed for App Store quality
class AppColors {
  // Brand Colors - Modern Gradient-friendly palette
  static const Color primary = Color(0xFF4F46E5); // Deep Indigo
  static const Color primaryLight = Color(0xFF818CF8); // Light Indigo
  static const Color primaryDark = Color(0xFF3730A3);
  static const Color secondary = Color(0xFF7C3AED); // Vibrant Purple
  static const Color secondaryLight = Color(0xFFA78BFA);

  // Semantic Colors
  static const Color success = Color(0xFF059669); // Emerald
  static const Color successLight = Color(0xFF10B981);
  static const Color successBg = Color(0xFFECFDF5);

  static const Color danger = Color(0xFFDC2626); // Red
  static const Color dangerLight = Color(0xFFEF4444);
  static const Color dangerBg = Color(0xFFFEF2F2);

  static const Color warning = Color(0xFFD97706); // Amber
  static const Color warningLight = Color(0xFFF59E0B);
  static const Color warningBg = Color(0xFFFFFBEB);

  static const Color info = Color(0xFF0284C7); // Sky Blue
  static const Color infoLight = Color(0xFF0EA5E9);
  static const Color infoBg = Color(0xFFF0F9FF);

  // Legacy aliases
  static const Color accent = success;
  static const Color error = danger;

  // Neutral Colors - Light Theme
  static const Color textPrimary = Color(0xFF111827); // Gray 900
  static const Color textSecondary = Color(0xFF4B5563); // Gray 600
  static const Color textTertiary = Color(0xFF9CA3AF); // Gray 400
  static const Color textLight = Color(0xFFD1D5DB); // Gray 300

  static const Color background = Color(0xFFF8FAFC); // Slate 50
  static const Color surface = Colors.white;
  static const Color surfaceVariant = Color(0xFFF1F5F9); // Slate 100
  static const Color border = Color(0xFFE2E8F0); // Slate 200
  static const Color borderLight = Color(0xFFF1F5F9);
  static const Color divider = Color(0xFFE5E7EB);

  // Result Colors
  static const Color spamRed = Color(0xFFFEE2E2);
  static const Color spamRedText = Color(0xFFDC2626);
  static const Color hamGreen = Color(0xFFD1FAE5);
  static const Color hamGreenText = Color(0xFF059669);

  // Risk Level Colors
  static const Color riskCritical = Color(0xFFDC2626);
  static const Color riskHigh = Color(0xFFEA580C);
  static const Color riskMedium = Color(0xFFD97706);
  static const Color riskLow = Color(0xFF2563EB);
  static const Color riskNone = Color(0xFF059669);

  // Dark Theme Colors
  static const Color darkBackground = Color(0xFF0F172A); // Slate 900
  static const Color darkSurface = Color(0xFF1E293B); // Slate 800
  static const Color darkCard = Color(0xFF334155); // Slate 700
  static const Color darkCardVariant = Color(0xFF475569); // Slate 600
  static const Color darkTextPrimary = Color(0xFFF8FAFC); // Slate 50
  static const Color darkTextSecondary = Color(0xFFCBD5E1); // Slate 300
  static const Color darkTextTertiary = Color(0xFF94A3B8); // Slate 400
  static const Color darkBorder = Color(0xFF475569); // Slate 600
  static const Color darkDivider = Color(0xFF334155);
  static const Color darkSpamRed = Color(0xFF450A0A);
  static const Color darkHamGreen = Color(0xFF052E16);

  // Gradient Presets
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary, secondary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient successGradient = LinearGradient(
    colors: [Color(0xFF059669), Color(0xFF10B981)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient dangerGradient = LinearGradient(
    colors: [Color(0xFFDC2626), Color(0xFFEF4444)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient warningGradient = LinearGradient(
    colors: [Color(0xFFD97706), Color(0xFFF59E0B)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Card shadow for depth
  static List<BoxShadow> cardShadow({double opacity = 0.08}) => [
        BoxShadow(
          color: Colors.black.withValues(alpha: opacity),
          blurRadius: 16,
          offset: const Offset(0, 4),
          spreadRadius: 0,
        ),
      ];

  static List<BoxShadow> softShadow({double opacity = 0.04}) => [
        BoxShadow(
          color: Colors.black.withValues(alpha: opacity),
          blurRadius: 8,
          offset: const Offset(0, 2),
          spreadRadius: 0,
        ),
      ];

  // Get risk color based on level
  static Color getRiskColor(String riskLevel) {
    switch (riskLevel.toUpperCase()) {
      case 'CRITICAL':
        return riskCritical;
      case 'HIGH':
        return riskHigh;
      case 'MEDIUM':
        return riskMedium;
      case 'LOW':
        return riskLow;
      default:
        return riskNone;
    }
  }
}
