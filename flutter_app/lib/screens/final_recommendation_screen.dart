import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'application_schedule_screen.dart';
import 'report_generation_screen.dart';
import 'sustainability_screen.dart';

class FinalRecommendationScreen extends StatefulWidget {
  final Map<String, dynamic> recommendationData;

  const FinalRecommendationScreen({
    super.key,
    required this.recommendationData,
  });

  @override
  State<FinalRecommendationScreen> createState() => _FinalRecommendationScreenState();
}

class _FinalRecommendationScreenState extends State<FinalRecommendationScreen> {
  bool _isSaving = false;
  String? _savedId;

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      final res = await ApiClient.instance.saveRecommendation(widget.recommendationData);
      setState(() => _savedId = res['recommendation_id']);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Recommendation saved successfully! (ID: $_savedId)'),
          backgroundColor: AppTheme.primaryGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to save: $e')));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final rec = widget.recommendationData;
    final crop = rec['crop'] ?? 'Crop';
    final district = rec['district'] ?? 'District';
    final p6 = rec['fertilizer_plan'] ?? {};
    final products = (p6['recommended_products'] as List? ?? []);
    final totalCost = (p6['total_cost_inr'] as num?)?.toDouble() ?? 0.0;
    final status = p6['status'] ?? 'OPTIMIZATION_SUCCESS';
    final p5 = rec['nutrient_requirements'] ?? {};
    final yp = rec['district_yield_prediction'] ?? {};
    final estYield = yp['estimated_yield_kg_per_ha'];

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('optimal_plan_title'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Summary Banner
              Card(
                color: AppTheme.darkGreen,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text(
                        l10n.text('estimated_cost'),
                        style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 13),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '₹${totalCost.toStringAsFixed(0)}',
                        style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '$crop • $district • ${p5['farm_area_hectares'] ?? 1.0} ha',
                          style: const TextStyle(color: Colors.white, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),

              // Optimization Status Badge
              Row(
                children: [
                  const Icon(Icons.check_circle_rounded, color: AppTheme.primaryGreen, size: 20),
                  const SizedBox(width: 8),
                  Text(
                    'Optimization Status: $status',
                    style: const TextStyle(fontWeight: FontWeight.w600, color: AppTheme.darkGreen),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Recommended Fertilizer Cards
              const SectionHeader(
                title: 'Commercial Fertilizer Purchase List',
                subtitle: 'Commercial bag sizes (45kg Neem Coated Urea / 50kg DAP & MOP)',
              ),
              if (products.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text('No external fertilizer products required. Soil fertility is sufficient.'),
                  ),
                )
              else
                for (final prod in products) ...[
                  FertilizerProductCard(
                    name: prod['name'] ?? 'Fertilizer',
                    quantityKg: (prod['quantity_kg'] as num?)?.toDouble() ?? 0.0,
                    bags: (prod['bags'] as num?)?.toInt() ?? 0,
                    bagSizeKg: (prod['bag_size_kg'] as num?)?.toDouble() ?? 50.0,
                    totalCostInr: (prod['total_cost_inr'] as num?)?.toDouble() ?? 0.0,
                    description: prod['description'],
                  ),
                  const SizedBox(height: 8),
                ],

              if (estYield != null) ...[
                const SizedBox(height: 14),
                Card(
                  color: AppTheme.lightGreen,
                  child: ListTile(
                    leading: const Icon(Icons.analytics_rounded, color: AppTheme.primaryGreen),
                    title: Text('District Benchmark: ${estYield.toStringAsFixed(0)} kg/ha'),
                    subtitle: const Text('Statistical average from historical district data (Phase 2 model).'),
                  ),
                ),
              ],

              const SizedBox(height: 24),
              // Action Buttons
              FilledButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ApplicationScheduleScreen(
                        scheduleData: p6['application_schedule'] ?? {},
                        crop: crop,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.calendar_month_rounded),
                label: Text(l10n.text('application_schedule')),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SustainabilityScreen(recommendationData: widget.recommendationData),
                    ),
                  );
                },
                icon: const Icon(Icons.eco_rounded),
                label: Text(l10n.text('sustainability_title')),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isSaving ? null : _save,
                      icon: const Icon(Icons.bookmark_border_rounded),
                      label: Text(_isSaving ? 'Saving...' : l10n.text('save_recommendation')),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ReportGenerationScreen(
                              recommendationData: widget.recommendationData,
                              savedId: _savedId,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.picture_as_pdf_rounded),
                      label: const Text('Report PDF'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
