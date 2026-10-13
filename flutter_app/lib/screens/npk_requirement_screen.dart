import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'final_recommendation_screen.dart';

class NpkRequirementScreen extends StatefulWidget {
  final Map<String, dynamic> flowData;
  final Map<String, dynamic>? soilProfile;

  const NpkRequirementScreen({
    super.key,
    required this.flowData,
    this.soilProfile,
  });

  @override
  State<NpkRequirementScreen> createState() => _NpkRequirementScreenState();
}

class _NpkRequirementScreenState extends State<NpkRequirementScreen> {
  Map<String, dynamic>? _recommendationResponse;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _calculateNpk();
  }

  Future<void> _calculateNpk() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Extract soil test values from soilProfile or use standard defaults
      double soilN = 220.0;
      double soilP = 16.0;
      double soilK = 190.0;
      String pMethod = 'Olsen';

      if (widget.soilProfile != null) {
        final fields = widget.soilProfile!['fields'] as List? ?? [];
        for (final f in fields) {
          final k = f['field']?.toString() ?? '';
          final val = (f['confirmed_value'] ?? f['ocr_value']);
          final numVal = double.tryParse(val?.toString() ?? '');
          if (numVal != null) {
            if (k == 'nitrogen') soilN = numVal;
            if (k == 'phosphorus') {
              soilP = numVal;
              if (f['test_method'] != null) pMethod = f['test_method'];
            }
            if (k == 'potassium') soilK = numVal;
          }
        }
      }

      final payload = {
        'crop': widget.flowData['crop'] ?? 'Rice',
        'district': widget.flowData['district'] ?? 'Thanjavur',
        'soil_series': widget.flowData['soil_series'] ?? 'Palavidhi',
        'season': widget.flowData['season'] ?? 'Kharif',
        'irrigation_method': widget.flowData['irrigation'] ?? 'Irrigated',
        'target_yield': widget.flowData['target_yield'] ?? 6.0,
        'soil_nitrogen': soilN,
        'soil_phosphorus': soilP,
        'soil_potassium': soilK,
        'soil_phosphorus_method': pMethod,
        'farm_area': widget.flowData['area'] ?? 1.0,
        'farm_area_unit': widget.flowData['area_unit'] ?? 'hectare',
      };

      final res = await ApiClient.instance.getFullRecommendation(payload);
      setState(() {
        _recommendationResponse = res;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Calculation failed: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _nutrientCard(String name, String symbol, double perHa, double total, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Text(
                symbol,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textDark)),
                  const SizedBox(height: 4),
                  Text('Per Hectare: ${perHa.toStringAsFixed(1)} kg/ha', style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('${total.toStringAsFixed(1)} kg', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
                const Text('Farm Total', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
              ],
            )
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final p5 = _recommendationResponse?['nutrient_requirements'] ?? {};
    final netN = (p5['n_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_n_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final netP = (p5['p2o5_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_p2o5_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final netK = (p5['k2o_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_k2o_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final totN = (p5['total_n_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_n_kg'] as num?)?.toDouble() ?? 0.0;
    final totP = (p5['total_p2o5_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_p2o5_kg'] as num?)?.toDouble() ?? 0.0;
    final totK = (p5['total_k2o_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_k2o_kg'] as num?)?.toDouble() ?? 0.0;
    final ruleId = p5['selected_rule_id']?.toString() ?? 'TNAU STCR-IPNS';
    final method = p5['calculation_method']?.toString() ?? p5['selected_method']?.toString() ?? 'Deterministic STCR Linear Equation';

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('npk_title'))),
      body: SafeArea(
        child: _isLoading
            ? const LoadingView(message: 'Evaluating verified TNAU STCR equations...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _calculateNpk)
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Card(
                          color: AppTheme.lightGreen,
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.verified_rounded, color: AppTheme.primaryGreen, size: 22),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        'Verified Rule: $ruleId',
                                        style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.darkGreen),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text('Method: $method', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                                Text('Crop: ${widget.flowData['crop']} | Target: ${widget.flowData['target_yield']} t/ha',
                                    style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        _nutrientCard('Nitrogen Requirement', 'N', netN, totN, const Color(0xFF1976D2)),
                        const SizedBox(height: 8),
                        _nutrientCard('Phosphorus Requirement', 'P₂O₅', netP, totP, const Color(0xFFE65100)),
                        const SizedBox(height: 8),
                        _nutrientCard('Potassium Requirement', 'K₂O', netK, totK, const Color(0xFF6A1B9A)),
                        const SizedBox(height: 20),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(14.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Agronomic Rule Details', style: TextStyle(fontWeight: FontWeight.bold)),
                                const SizedBox(height: 6),
                                const Text(
                                  '• Nitrogen, Phosphorus & Potash doses are calculated purely deterministically from your soil test and target yield.\n• Elemental P and K are properly normalized to oxide equivalents (P₂O₅ & K₂O).\n• No ML approximations are applied to nutrient calculations.',
                                  style: TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.4),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        FilledButton.icon(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => FinalRecommendationScreen(
                                  recommendationData: _recommendationResponse!,
                                ),
                              ),
                            );
                          },
                          icon: const Icon(Icons.calculate_rounded),
                          label: Text(l10n.text('optimal_plan_title')),
                        ),
                      ],
                    ),
                  ),
      ),
    );
  }
}
