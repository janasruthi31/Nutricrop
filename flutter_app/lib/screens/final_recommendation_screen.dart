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

    final recType = rec['recommendation_type'] ?? p6['recommendation_type'] ?? p5['recommendation_type'] ?? 'SOIL_SPECIFIC_STCR';
    final isVerified = rec['is_verified'] == true && p6['is_verified'] != false;
    final isProvisional = rec['is_provisional'] == true || p6['is_provisional'] == true || !isVerified || recType == 'PROVISIONAL_UNVERIFIED';

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('optimal_plan_title'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Provisional Disclaimer or General Blanket Banner
              if (isProvisional) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF3E0),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.orange.shade800, width: 1.5),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.warning_amber_rounded, color: Colors.orange.shade900, size: 24),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable.',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.brown.shade900),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'PROVISIONAL ONLY: The quantities and costs shown below are provisional estimates awaiting official TNAU STCR calibration. Do not present or apply as a confirmed soil-specific recommendation.',
                              style: TextStyle(fontSize: 11, color: Colors.brown.shade800, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ] else if (recType == 'GENERAL_BLANKET') ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE1F5FE),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF0288D1), width: 1.2),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.assignment_turned_in_rounded, color: Color(0xFF0277BD), size: 22),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'GENERAL / BLANKET RECOMMENDATION: Verified official TNAU Crop Production Guide recommendation with soil rating adjustments. This is not an STCR target-yield equation.',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF01579B), height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // Summary Banner
              Card(
                color: isProvisional ? Colors.brown.shade800 : AppTheme.darkGreen,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text(
                        isProvisional ? 'Provisional Estimated Cost (Unverified)' : l10n.text('estimated_cost'),
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
                  Icon(
                    isProvisional ? Icons.warning_amber_rounded : Icons.check_circle_rounded,
                    color: isProvisional ? Colors.amber.shade900 : AppTheme.primaryGreen,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      isProvisional
                          ? 'Status: PROVISIONAL (Unverified Agronomic Rule)'
                          : 'Optimization Status: $status ($recType)',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: isProvisional ? Colors.brown.shade900 : AppTheme.darkGreen,
                      ),
                    ),
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
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(
                      status == 'MISSING_INPUTS' || status == 'VALIDATION_ERROR'
                          ? 'Fertilizer dose could not be calculated reliably due to missing soil test inputs or unavailable validated rules. AgroWise AI never fabricates doses.'
                          : 'No external chemical fertilizer products required. Natural soil fertility is sufficient to meet the crop nutrient uptake target.',
                    ),
                  ),
                )
              else
                for (final prod in products) ...[
                  FertilizerProductCard(
                    name: prod['product_name'] ?? prod['name'] ?? 'Fertilizer',
                    quantityKg: (prod['quantity_kg'] as num?)?.toDouble() ?? 0.0,
                    quantityPerHaKg: (prod['quantity_per_ha_kg'] as num?)?.toDouble(),
                    totalFarmQuantityKg: (prod['total_farm_quantity_kg'] as num?)?.toDouble(),
                    applicationTiming: prod['application_timing']?.toString(),
                    bags: (prod['bags'] as num?)?.toInt() ?? 0,
                    bagSizeKg: (prod['bag_size_kg'] as num?)?.toDouble() ?? 50.0,
                    totalCostInr: (prod['total_cost_inr'] as num?)?.toDouble() ?? 0.0,
                    pricePerBagInr: (prod['price_per_bag_inr'] as num?)?.toDouble(),
                    priceSource: prod['price_source']?.toString(),
                    priceEffectiveDate: prod['price_effective_date']?.toString(),
                    description: prod['description'],
                  ),
                  const SizedBox(height: 8),
                ],

              // Derivation Explanation Card
              if (rec['derivation_explanation'] != null || p5['derivation_explanation'] != null) ...[
                const SizedBox(height: 12),
                Card(
                  elevation: 1.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10), side: BorderSide(color: Colors.green.shade200)),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.psychology_alt_outlined, color: AppTheme.primaryGreen, size: 20),
                            SizedBox(width: 8),
                            Text('How This Recommendation Was Derived', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textDark)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          (rec['derivation_explanation'] ?? p5['derivation_explanation']).toString(),
                          style: const TextStyle(fontSize: 12, color: AppTheme.textDark, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              // Authoritative Reference Card
              if (rec['authoritative_reference'] is Map || p5['authoritative_reference'] is Map) ...[
                const SizedBox(height: 10),
                Builder(
                  builder: (_) {
                    final auth = (rec['authoritative_reference'] ?? p5['authoritative_reference']) as Map;
                    return Card(
                      elevation: 1.0,
                      color: const Color(0xFFF9FBF9),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10), side: BorderSide(color: Colors.grey.shade300)),
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.menu_book_rounded, color: AppTheme.darkGreen, size: 18),
                                SizedBox(width: 8),
                                Text('Authoritative Reference', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.darkGreen)),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text(
                              auth['title']?.toString() ?? 'TNAU Agronomic Recommendation',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textDark),
                            ),
                            if (auth['section_or_page'] != null)
                              Text('Section / Page: ${auth['section_or_page']}', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                            if (auth['url'] != null)
                              Text('Source URL: ${auth['url']}', style: const TextStyle(fontSize: 11, color: Color(0xFF1565C0))),
                          ],
                        ),
                      ),
                    );
                  },
                ),
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
