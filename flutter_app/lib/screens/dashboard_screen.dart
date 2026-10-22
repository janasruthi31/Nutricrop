import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'farm_details_screen.dart';
import 'final_recommendation_screen.dart';
import 'language_selection_screen.dart';
import 'notifications_screen.dart';
import 'recommendation_details_screen.dart';
import 'recommendation_history_screen.dart';
import 'upload_screen.dart';
import 'weather_screen.dart';
import 'yield_prediction_input_screen.dart';

class DashboardScreen extends StatefulWidget {
  final Function(int)? onSwitchTab;
  const DashboardScreen({super.key, this.onSwitchTab});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _profile;
  Map<String, dynamic>? _latestRecommendation;
  Map<String, dynamic>? _weather;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    try {
      final p = await ApiClient.instance.getProfile();
      final recs = await ApiClient.instance.listRecommendations();
      final w = await ApiClient.instance.getWeatherGuidance(p['district'] ?? 'Thanjavur');

      setState(() {
        _profile = p;
        if (recs.isNotEmpty) {
          _latestRecommendation = recs.first as Map<String, dynamic>;
        }
        _weather = w;
      });
    } catch (_) {}
    finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _actionCard({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.14),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: color, size: 34),
              ),
              const SizedBox(height: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textDark),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _openShortFlowModal(BuildContext context, String district) {
    String selectedCrop = 'Rice';
    double selectedArea = 1.0;
    bool isSubmitting = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (modalCtx, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(modalCtx).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade100,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.flash_on_rounded, color: Colors.amber, size: 28),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Short Flow / விரைவு முறை (3 Steps)',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textDark),
                            ),
                            Text(
                              'Instant TNAU fertilizer plan without soil card upload',
                              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.pop(modalCtx),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  // Step 1: Crop Selection
                  const Text('Step 1: Target Crop (பயிர்)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<String>(
                    value: selectedCrop,
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.grey.shade50,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'Rice', child: Text('Rice (நெல்)')),
                      DropdownMenuItem(value: 'Cotton (lint)', child: Text('Cotton (பருத்தி)')),
                      DropdownMenuItem(value: 'Sugarcane', child: Text('Sugarcane (கரும்பு)')),
                      DropdownMenuItem(value: 'Groundnut', child: Text('Groundnut (நிலக்கடலை)')),
                      DropdownMenuItem(value: 'Blackgram', child: Text('Blackgram (உளுந்து)')),
                    ],
                    onChanged: (val) {
                      if (val != null) setModalState(() => selectedCrop = val);
                    },
                  ),
                  const SizedBox(height: 14),
                  // Step 2: Farm Area
                  const Text('Step 2: Farm Area (நிலப் பரப்பு)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      for (final a in [0.5, 1.0, 2.0, 5.0])
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text('$a acre'),
                            selected: selectedArea == a,
                            onSelected: (sel) {
                              if (sel) setModalState(() => selectedArea = a);
                            },
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Step 3: Action
                  const Text('Step 3: Recommendation (பரிந்துரை)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 4),
                  const Text('Uses official TNAU blanket guidelines with soil test advisory.', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF2E7D32),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: isSubmitting
                        ? null
                        : () async {
                            setModalState(() => isSubmitting = true);
                            try {
                              final payload = {
                                'crop': selectedCrop,
                                'district': district,
                                'farm_area': selectedArea,
                                'farm_area_unit': 'acre',
                                'recommendation_type': 'NO_SOIL_TEST',
                                'no_soil_test': true,
                              };
                              final rec = await ApiClient.instance.getFullRecommendation(payload);
                              if (!context.mounted) return;
                              Navigator.pop(modalCtx);
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => FinalRecommendationScreen(recommendationData: rec),
                                ),
                              );
                            } catch (e) {
                              setModalState(() => isSubmitting = false);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Failed to compute recommendation: $e')),
                                );
                              }
                            }
                          },
                    icon: isSubmitting
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.flash_on_rounded),
                    label: Text(
                      isSubmitting ? 'Computing...' : 'Get Instant Recommendation (உடனடி உரம்)',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final farmerName = _profile?['full_name'] ?? 'Farmer';
    final district = _profile?['district'] ?? 'Thanjavur';

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen),
            const SizedBox(width: 8),
            Text(l10n.text('app_title'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.language_rounded),
            tooltip: 'Language',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const LanguageSelectionScreen(isFromSettings: true)),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            tooltip: 'Notifications',
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen()));
            },
          ),
        ],
      ),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _loadDashboardData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(18.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Greeting & Profile Header
                Card(
                  color: AppTheme.darkGreen,
                  child: Padding(
                    padding: const EdgeInsets.all(18.0),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 28,
                          backgroundColor: Colors.white.withOpacity(0.2),
                          child: const Icon(Icons.person_rounded, color: Colors.white, size: 36),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                l10n.text('greeting'),
                                style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 13),
                              ),
                              Text(
                                farmerName,
                                style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                              Text(
                                '$district District, Tamil Nadu',
                                style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 12),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Based on TNAU guidelines • Not an official government tool',
                                style: TextStyle(color: Color(0xFFC8E6C9), fontSize: 10.5, fontStyle: FontStyle.italic),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Weather Summary Card
                if (_weather != null) ...[
                  Card(
                    color: const Color(0xFFF1F8E9),
                    child: ListTile(
                      leading: const Icon(Icons.cloud_queue_rounded, color: AppTheme.primaryGreen, size: 32),
                      title: Text(
                        'Weather: ${_weather!['current_condition'] ?? 'Clear'} (${_weather!['temperature_c'] ?? 31}°C)',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      subtitle: Text(
                        _weather!['actionable_advice'] ?? 'Clear conditions for fieldwork.',
                        style: const TextStyle(fontSize: 12, color: AppTheme.darkGreen),
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => WeatherScreen(initialDistrict: district)));
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Short Flow Option (விரைவு முறை) - 3 Step Quick Flow (Task 4b)
                Card(
                  elevation: 2.0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: Colors.amber.shade700, width: 1.5),
                  ),
                  color: const Color(0xFFFFF8E1),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(16),
                    onTap: () => _openShortFlowModal(context, district),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.amber.shade800,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: const Icon(Icons.flash_on_rounded, color: Colors.white, size: 32),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      'Short Flow / விரைவு முறை',
                                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.brown.shade900),
                                    ),
                                    const SizedBox(width: 6),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: Colors.amber.shade900,
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: const Text('3 STEPS', style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Instant fertilizer dose & cheapest bags in 30 seconds. No card upload needed.',
                                  style: TextStyle(fontSize: 11, color: Colors.brown.shade800, height: 1.2),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.brown),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Grid of 6 Core Actions
                Text(
                  l10n.text('dashboard_quick_actions'),
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textDark),
                ),
                const SizedBox(height: 12),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.15,
                  children: [
                    _actionCard(
                      context: context,
                      title: l10n.text('upload_card'),
                      subtitle: 'PDF / Camera OCR',
                      icon: Icons.document_scanner_rounded,
                      color: const Color(0xFF2E7D32),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => UploadScreen(
                              onValidatedProfile: (profile) {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => FarmDetailsScreen(initialSoilProfile: profile),
                                  ),
                                );
                              },
                            ),
                          ),
                        );
                      },
                    ),
                    _actionCard(
                      context: context,
                      title: l10n.text('get_recommendation'),
                      subtitle: 'TNAU STCR + LP Cost',
                      icon: Icons.calculate_rounded,
                      color: const Color(0xFF00796B),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const FarmDetailsScreen()));
                      },
                    ),
                    _actionCard(
                      context: context,
                      title: l10n.text('predict_yield'),
                      subtitle: 'XGBoost ML Benchmark',
                      icon: Icons.online_prediction_rounded,
                      color: const Color(0xFF1565C0),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const YieldPredictionInputScreen()));
                      },
                    ),
                    _actionCard(
                      context: context,
                      title: l10n.text('weather_advisory'),
                      subtitle: 'Fertilizer Timing',
                      icon: Icons.wb_sunny_rounded,
                      color: const Color(0xFFF57F17),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => WeatherScreen(initialDistrict: district)));
                      },
                    ),
                    _actionCard(
                      context: context,
                      title: l10n.text('history'),
                      subtitle: 'Past Recommendations',
                      icon: Icons.history_rounded,
                      color: const Color(0xFF6A1B9A),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const RecommendationHistoryScreen()));
                      },
                    ),
                    _actionCard(
                      context: context,
                      title: 'Download Reports',
                      subtitle: 'Official PDF Copies',
                      icon: Icons.picture_as_pdf_rounded,
                      color: const Color(0xFFC2185B),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const RecommendationHistoryScreen()));
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 22),

                // Latest Recommendation Card
                Text(
                  l10n.text('recent_recommendations'),
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textDark),
                ),
                const SizedBox(height: 10),
                if (_latestRecommendation != null) ...[
                  Card(
                    child: ListTile(
                      contentPadding: const EdgeInsets.all(14),
                      leading: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(color: AppTheme.lightGreen, borderRadius: BorderRadius.circular(10)),
                        child: const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen),
                      ),
                      title: Text(
                        '${_latestRecommendation!['crop']} (${_latestRecommendation!['district']})',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text(
                        'Total Cost: ₹${((_latestRecommendation!['total_cost_inr'] as num?)?.toDouble() ?? 0).toStringAsFixed(0)} • ${_latestRecommendation!['created_at']?.toString().split('T').first}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => RecommendationDetailsScreen(
                              recommendationId: _latestRecommendation!['recommendation_id'],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ] else ...[
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: Column(
                        children: [
                          const Icon(Icons.compost_rounded, size: 38, color: Colors.grey),
                          const SizedBox(height: 10),
                          Text(
                            l10n.text('no_recent_rec'),
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
                          ),
                          const SizedBox(height: 14),
                          FilledButton(
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => UploadScreen(
                                    onValidatedProfile: (profile) {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (_) => FarmDetailsScreen(initialSoilProfile: profile),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              );
                            },
                            child: Text(l10n.text('upload_card')),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
