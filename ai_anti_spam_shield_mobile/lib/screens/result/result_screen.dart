import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:animate_do/animate_do.dart';
import '../../providers/scan_provider.dart';
import '../../models/scan_result.dart';
import '../../utils/colors.dart';
import '../../widgets/animations/success_checkmark.dart';
import '../../widgets/animations/threat_alert_animation.dart';
import '../../widgets/animations/progress_ring.dart';
import '../../widgets/feedback_buttons.dart';

class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scanState = ref.watch(scanProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    if (scanState.result == null) {
      return Scaffold(
        backgroundColor: isDark ? AppColors.darkBackground : AppColors.background,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: Icon(
              Icons.arrow_back_ios_new,
              color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
            ),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.search_off,
                size: 64,
                color: AppColors.textTertiary,
              ),
              const SizedBox(height: 16),
              Text(
                'No scan result available',
                style: TextStyle(
                  fontSize: 16,
                  color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      );
    }

    final result = scanState.result!;
    final isSpam = result.isSpam;
    final statusColor = isSpam ? AppColors.danger : AppColors.success;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.background,
      body: CustomScrollView(
        slivers: [
          // Custom App Bar with result status
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            elevation: 0,
            backgroundColor: statusColor,
            leading: IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
              ),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: isSpam ? AppColors.dangerGradient : AppColors.successGradient,
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 40),
                      // Animated Icon
                      FadeInDown(
                        duration: const Duration(milliseconds: 600),
                        child: isSpam
                            ? ThreatAlertAnimation(
                                size: 100,
                                showShake: true,
                                showPulse: true,
                                enableHaptic: true,
                              )
                            : SuccessCheckmark(
                                size: 100,
                                showParticles: true,
                              ),
                      ),
                      const SizedBox(height: 20),
                      // Status Text
                      FadeInUp(
                        duration: const Duration(milliseconds: 500),
                        delay: const Duration(milliseconds: 200),
                        child: Text(
                          isSpam ? _getStatusText(result.riskLevel) : 'Message is Safe',
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Confidence Badge
                      FadeInUp(
                        duration: const Duration(milliseconds: 500),
                        delay: const Duration(milliseconds: 300),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                isSpam ? Icons.warning_amber : Icons.verified_user,
                                color: Colors.white,
                                size: 18,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '${result.confidenceLabel}: ${result.confidencePercentage}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Risk Level Card (for spam)
                  if (isSpam) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 500),
                      child: _buildRiskLevelCard(result, isDark),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Voice Scan Badge
                  if (result.isVoiceScan) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 550),
                      child: _buildVoiceScanBadge(isDark),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Transcribed Text
                  if (result.isVoiceScan && result.transcribedText != null) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 600),
                      child: _buildContentCard(
                        title: 'Transcribed Message',
                        icon: Icons.record_voice_over_outlined,
                        iconColor: AppColors.primary,
                        isDark: isDark,
                        child: Text(
                          result.transcribedText!,
                          style: TextStyle(
                            fontSize: 14,
                            fontStyle: FontStyle.italic,
                            color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Message Preview
                  if (!result.isVoiceScan || result.message.isNotEmpty)
                    FadeInUp(
                      duration: const Duration(milliseconds: 650),
                      child: _buildContentCard(
                        title: result.isVoiceScan ? 'Original Message' : 'Scanned Message',
                        icon: Icons.message_outlined,
                        iconColor: AppColors.info,
                        isDark: isDark,
                        child: Text(
                          result.message,
                          style: TextStyle(
                            fontSize: 14,
                            color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ),

                  const SizedBox(height: 16),

                  // Danger Causes Section
                  if (result.dangerCauses.isNotEmpty) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 700),
                      child: _buildDangerCausesSection(result, isDark),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Analysis Details
                  if (result.details != null)
                    FadeInUp(
                      duration: const Duration(milliseconds: 750),
                      child: _buildAnalysisDetails(result, isDark),
                    ),

                  const SizedBox(height: 16),

                  // Feedback Section
                  if (result.details?['historyId'] != null)
                    FadeInUp(
                      duration: const Duration(milliseconds: 800),
                      child: _buildFeedbackSection(result, isDark),
                    ),

                  const SizedBox(height: 24),

                  // Action Buttons
                  FadeInUp(
                    duration: const Duration(milliseconds: 850),
                    child: _buildActionButtons(context, result, isDark),
                  ),

                  // Safety Tips for spam
                  if (isSpam) ...[
                    const SizedBox(height: 24),
                    FadeInUp(
                      duration: const Duration(milliseconds: 900),
                      child: _buildSafetyTips(isDark),
                    ),
                  ],

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getStatusText(String riskLevel) {
    switch (riskLevel) {
      case 'CRITICAL':
        return 'Dangerous Message!';
      case 'HIGH':
        return 'High Risk Detected';
      case 'MEDIUM':
        return 'Suspicious Content';
      default:
        return 'Potential Threat';
    }
  }

  Widget _buildRiskLevelCard(ScanResult result, bool isDark) {
    final riskColor = AppColors.getRiskColor(result.riskLevel);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: riskColor.withValues(alpha: isDark ? 0.15 : 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: riskColor.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: riskColor.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.security, color: riskColor, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Threat Level',
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  result.riskLevel,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: riskColor,
                  ),
                ),
              ],
            ),
          ),
          ConfidenceIndicator(
            confidence: result.confidence,
            isSpam: result.isSpam,
            size: 60,
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceScanBadge(bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: isDark ? 0.15 : 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.mic, color: AppColors.primary, size: 20),
          ),
          const SizedBox(width: 12),
          Text(
            'Voice message analyzed',
            style: TextStyle(
              color: AppColors.primary,
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContentCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required bool isDark,
    required Widget child,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: isDark ? null : AppColors.softShadow(),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconColor, size: 18),
              ),
              const SizedBox(width: 12),
              Text(
                title,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildDangerCausesSection(ScanResult result, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.2)),
        boxShadow: isDark ? null : AppColors.softShadow(),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.danger.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(Icons.shield_outlined, color: AppColors.danger, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Why This Is Dangerous',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                      ),
                    ),
                    Text(
                      '${result.dangerCauses.length} issue${result.dangerCauses.length > 1 ? 's' : ''} detected',
                      style: TextStyle(
                        fontSize: 12,
                        color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Danger Causes List
          ...result.dangerCauses.map((cause) => _buildDangerCauseItem(cause, isDark)),

          // Detection Info
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isDark ? AppColors.darkBackground : AppColors.surfaceVariant,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  size: 16,
                  color: isDark ? AppColors.darkTextTertiary : AppColors.textTertiary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '${result.confidenceLabel}: ${result.confidencePercentage} • Threshold: ${(result.detectionThreshold * 100).toInt()}%',
                    style: TextStyle(
                      fontSize: 12,
                      color: isDark ? AppColors.darkTextTertiary : AppColors.textTertiary,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDangerCauseItem(DangerCause cause, bool isDark) {
    final color = _getSeverityColor(cause.severity);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDark ? 0.12 : 0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(_getSeverityIcon(cause.severity), color: color, size: 18),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  cause.title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  cause.severity.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            cause.description,
            style: TextStyle(
              fontSize: 13,
              color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'critical':
        return AppColors.riskCritical;
      case 'high':
        return AppColors.riskHigh;
      case 'medium':
        return AppColors.riskMedium;
      case 'low':
        return AppColors.riskLow;
      default:
        return AppColors.warning;
    }
  }

  IconData _getSeverityIcon(String severity) {
    switch (severity) {
      case 'critical':
        return Icons.dangerous;
      case 'high':
        return Icons.warning_amber;
      case 'medium':
        return Icons.error_outline;
      case 'low':
        return Icons.info_outline;
      default:
        return Icons.flag;
    }
  }

  Widget _buildAnalysisDetails(ScanResult result, bool isDark) {
    return _buildContentCard(
      title: 'Analysis Details',
      icon: Icons.analytics_outlined,
      iconColor: AppColors.secondary,
      isDark: isDark,
      child: Column(
        children: [
          _buildDetailRow('Prediction', result.prediction.toUpperCase(), isDark),
          _buildDetailRow('Confidence', result.confidencePercentage, isDark),
          if (result.details!['features'] != null) ...[
            const Divider(height: 24),
            _buildFeaturesSection(result.details!['features'], isDark),
          ],
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 14,
              color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturesSection(Map<String, dynamic> features, bool isDark) {
    final List<Widget> chips = [];

    if (features['has_url'] == true) {
      chips.add(_buildFeatureChip('Contains URL', Icons.link, AppColors.info));
    }
    if (features['has_email'] == true) {
      chips.add(_buildFeatureChip('Contains Email', Icons.email_outlined, AppColors.info));
    }
    if (features['has_phone'] == true) {
      chips.add(_buildFeatureChip('Contains Phone', Icons.phone_outlined, AppColors.info));
    }
    if (features['urgency_words'] == true) {
      chips.add(_buildFeatureChip('Urgency Tactics', Icons.timer_outlined, AppColors.warning));
    }
    if (features['spam_keywords'] == true) {
      chips.add(_buildFeatureChip('Spam Keywords', Icons.block, AppColors.danger));
    }
    if (features['currency_symbols'] == true) {
      chips.add(_buildFeatureChip('Money Reference', Icons.attach_money, AppColors.warning));
    }

    if (chips.isEmpty) {
      return Text(
        'No specific patterns detected',
        style: TextStyle(
          fontSize: 13,
          color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
        ),
      );
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: chips,
    );
  }

  Widget _buildFeatureChip(String label, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackSection(ScanResult result, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: isDark ? null : AppColors.softShadow(),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(Icons.thumb_up_outlined, color: AppColors.success, size: 18),
              ),
              const SizedBox(width: 12),
              Text(
                'Was this helpful?',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          FeedbackButtons(
            scanId: result.details!['historyId'].toString(),
            scanType: result.isVoiceScan ? 'voice' : 'text',
            isSpam: result.isSpam,
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, ScanResult result, bool isDark) {
    return Column(
      children: [
        if (result.isSpam)
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            child: ElevatedButton.icon(
              onPressed: () => _showReportDialog(context, result.message),
              icon: const Icon(Icons.flag_outlined, size: 20),
              label: const Text('Report This Message'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.danger,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            gradient: AppColors.primaryGradient,
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.3),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: ElevatedButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.search, size: 20),
            label: const Text('Scan Another Message'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSafetyTips(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: isDark ? 0.12 : 0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.warning.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(Icons.tips_and_updates, color: AppColors.warning, size: 20),
              ),
              const SizedBox(width: 12),
              Text(
                'What You Should Do',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildTipItem(Icons.block, 'Do not respond to this message', isDark),
          _buildTipItem(Icons.link_off, 'Never click on any links', isDark),
          _buildTipItem(Icons.person_off, 'Don\'t share personal information', isDark),
          _buildTipItem(Icons.delete_outline, 'Delete and block the sender', isDark),
        ],
      ),
    );
  }

  Widget _buildTipItem(IconData icon, String text, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.warning),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 13,
                color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showReportDialog(BuildContext context, String message) {
    HapticFeedback.lightImpact();
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) {
        final isDark = Theme.of(context).brightness == Brightness.dark;
        return Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkSurface : Colors.white,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.textLight,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.danger.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.flag, color: AppColors.danger, size: 32),
              ),
              const SizedBox(height: 20),
              Text(
                'Report This Message',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: isDark ? AppColors.darkTextPrimary : AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Help improve our detection by reporting this spam message. Your report is anonymous.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: isDark ? AppColors.darkTextSecondary : AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: BorderSide(color: AppColors.border),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: Text(
                        'Cancel',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Row(
                              children: [
                                Icon(Icons.check_circle, color: Colors.white, size: 20),
                                const SizedBox(width: 12),
                                const Text('Report submitted successfully'),
                              ],
                            ),
                            backgroundColor: AppColors.success,
                            behavior: SnackBarBehavior.floating,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            margin: const EdgeInsets.all(16),
                          ),
                        );
                      },
                      icon: const Icon(Icons.send, size: 18),
                      label: const Text('Submit Report'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.danger,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: MediaQuery.of(context).padding.bottom + 8),
            ],
          ),
        );
      },
    );
  }
}
