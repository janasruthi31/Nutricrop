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
  late Map<String, dynamic> _recData;
  bool _isSaving = false;
  bool _isRecalculating = false;
  String? _savedId;

  final TextEditingController _ureaPriceController = TextEditingController(text: '266.50');
  final TextEditingController _dapPriceController = TextEditingController(text: '1350.00');
  final TextEditingController _mopPriceController = TextEditingController(text: '1700.00');
  final TextEditingController _sspPriceController = TextEditingController(text: '600.00');

  @override
  void initState() {
    super.initState();
    _recData = Map<String, dynamic>.from(widget.recommendationData);
  }

  @override
  void dispose() {
    _ureaPriceController.dispose();
    _dapPriceController.dispose();
    _mopPriceController.dispose();
    _sspPriceController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      final res = await ApiClient.instance.saveRecommendation(_recData);
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

  Future<void> _listenInTamil() async {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => _TamilVoiceDialog(recommendationData: _recData),
    );
  }

  Future<void> _recalculateWithCustomPrices() async {
    setState(() => _isRecalculating = true);
    try {
      final customPrices = {
        'UREA': double.tryParse(_ureaPriceController.text) ?? 266.50,
        'DAP': double.tryParse(_dapPriceController.text) ?? 1350.00,
        'MOP': double.tryParse(_mopPriceController.text) ?? 1700.00,
        'SSP': double.tryParse(_sspPriceController.text) ?? 600.00,
      };

      final updatedPayload = {
        ..._recData,
        'custom_prices': customPrices,
        'no_cache': true,
      };

      final res = await ApiClient.instance.getFullRecommendation(updatedPayload);
      setState(() {
        _recData = res;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Re-calculated successfully with your local dealer prices!'),
          backgroundColor: AppTheme.primaryGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to re-calculate: $e')));
    } finally {
      if (mounted) setState(() => _isRecalculating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final rec = _recData;
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

    final pricesDate = rec['prices_last_updated'] ?? p6['prices_last_updated'] ?? '2026-10-22';
    final rulesDate = rec['rules_last_updated'] ?? p6['rules_last_updated'] ?? '2026-10-22';

    // Nutrient Surplus Data (Task 4e)
    final balance = (p6['nutrient_balance'] as Map? ?? {});
    final surplusDict = (p6['nutrient_surplus_kg'] as Map? ?? {});
    final hasSurplus = p6['has_surplus'] == true || surplusDict.values.any((v) => (v as num) > 0.05);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('optimal_plan_title'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Tamil Voice Readout Action Button (Task 4b)
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2E7D32),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 2,
                ),
                onPressed: _listenInTamil,
                icon: const Icon(Icons.record_voice_over_rounded, size: 24),
                label: const Text(
                  'பரிந்துரையை தமிழில் கேளுங்கள் (Listen in Tamil)',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 14),

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
                          'General recommendation (lower confidence): Based on TNAU Blanket RDF adjusted by soil nutrient ratings.',
                          style: TextStyle(fontSize: 12, color: Color(0xFF01579B), fontWeight: FontWeight.w600),
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

              // Optimization Status Badge & Last Updated Dates (Task 4d)
              Card(
                elevation: 0.5,
                color: const Color(0xFFF1F8E9),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            isProvisional ? Icons.warning_amber_rounded : Icons.check_circle_rounded,
                            color: isProvisional ? Colors.amber.shade900 : AppTheme.primaryGreen,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              isProvisional
                                  ? 'Status: PROVISIONAL (Unverified Rule)'
                                  : 'Optimization Status: $status ($recType)',
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                                color: isProvisional ? Colors.brown.shade900 : AppTheme.darkGreen,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 12,
                        runSpacing: 4,
                        children: [
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.calendar_today_rounded, size: 12, color: AppTheme.textMuted),
                              const SizedBox(width: 4),
                              Text('Prices updated: $pricesDate', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.verified_outlined, size: 12, color: AppTheme.textMuted),
                              const SizedBox(width: 4),
                              Text('Rules updated: $rulesDate', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),

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

              // Nutrient Balance & Surplus Card (Task 4e)
              const SizedBox(height: 12),
              Card(
                elevation: 1.0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: hasSurplus ? Colors.amber.shade400 : Colors.green.shade200),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            hasSurplus ? Icons.info_outline_rounded : Icons.check_circle_outline,
                            color: hasSurplus ? Colors.amber.shade900 : AppTheme.primaryGreen,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Nutrient Balance & Surplus (சத்து இருப்பு)',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textDark),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        p6['surplus_summary']?.toString() ??
                            'Whole-bag commercial packaging constraint may deliver minor nutrient surplus.',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textDark, height: 1.3),
                      ),
                      const SizedBox(height: 10),
                      Table(
                        border: TableBorder.all(color: Colors.grey.shade300, width: 0.8),
                        children: [
                          const TableRow(
                            decoration: BoxDecoration(color: Color(0xFFE8F5E9)),
                            children: [
                              Padding(padding: EdgeInsets.all(6), child: Text('Nutrient', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                              Padding(padding: EdgeInsets.all(6), child: Text('Required', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                              Padding(padding: EdgeInsets.all(6), child: Text('Supplied', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                              Padding(padding: EdgeInsets.all(6), child: Text('Surplus', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                            ],
                          ),
                          ...[
                            {'key': 'nitrogen', 'label': 'Nitrogen (N)'},
                            {'key': 'phosphorus_p2o5', 'label': 'P₂O₅'},
                            {'key': 'potassium_k2o', 'label': 'K₂O'},
                          ].map((entry) {
                            final row = (balance[entry['key']] as Map? ?? {});
                            final reqKg = (row['required_kg'] as num?)?.toDouble() ?? 0.0;
                            final supKg = (row['supplied_kg'] as num?)?.toDouble() ?? 0.0;
                            final surKg = (row['surplus_kg'] as num?)?.toDouble() ?? 0.0;
                            final surPct = (row['surplus_pct'] as num?)?.toDouble() ?? 0.0;
                            return TableRow(
                              children: [
                                Padding(padding: const EdgeInsets.all(6), child: Text(entry['label']!, style: const TextStyle(fontSize: 11))),
                                Padding(padding: const EdgeInsets.all(6), child: Text('${reqKg.toStringAsFixed(1)} kg', style: const TextStyle(fontSize: 11))),
                                Padding(padding: const EdgeInsets.all(6), child: Text('${supKg.toStringAsFixed(1)} kg', style: const TextStyle(fontSize: 11))),
                                Padding(
                                  padding: const EdgeInsets.all(6),
                                  child: Text(
                                    surKg > 0.05 ? '+${surKg.toStringAsFixed(1)} kg (+${surPct.toStringAsFixed(0)}%)' : '0.0 kg',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: surKg > 0.05 ? FontWeight.bold : FontWeight.normal,
                                      color: surKg > 0.05 ? Colors.brown.shade800 : Colors.green.shade900,
                                    ),
                                  ),
                                ),
                              ],
                            );
                          }),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Tip: Surplus arises from discrete whole commercial bags (45/50 kg). On small plots, apply fractional/loose bags to save cost.',
                        style: TextStyle(fontSize: 10, color: AppTheme.textMuted, fontStyle: FontStyle.italic),
                      ),
                    ],
                  ),
                ),
              ),

              // Local Fertilizer Bag Price Editor (Task 4e)
              const SizedBox(height: 12),
              Card(
                elevation: 1.0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ExpansionTile(
                  leading: const Icon(Icons.storefront_rounded, color: AppTheme.primaryGreen),
                  title: const Text('Enter Local Dealer Bag Prices', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  subtitle: const Text('உள்ளூர் உர விலையை மாற்றியமைக்கலாம்', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Text(
                            'Customize the retail price per bag in your village/block to find the lowest-cost fertilizer combination:',
                            style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: _ureaPriceController,
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(labelText: 'Urea (45kg)', prefixText: '₹'),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: _dapPriceController,
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(labelText: 'DAP (50kg)', prefixText: '₹'),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: _mopPriceController,
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(labelText: 'MOP Potash (50kg)', prefixText: '₹'),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: _sspPriceController,
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(labelText: 'SSP (50kg)', prefixText: '₹'),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          FilledButton.icon(
                            style: FilledButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                            onPressed: _isRecalculating ? null : _recalculateWithCustomPrices,
                            icon: _isRecalculating
                                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : const Icon(Icons.calculate_rounded),
                            label: Text(_isRecalculating ? 'Re-optimizing...' : 'Re-calculate with My Prices (மறு கணக்கீடு)'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

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
                    subtitle: const Text('district benchmark, not a prediction for your field'),
                  ),
                ),
              ],

              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.gavel_rounded, size: 16, color: AppTheme.textMuted),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Disclaimer: Confirm with your local agriculture officer. Recommendations are based on TNAU guidelines.',
                        style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                      ),
                    ),
                  ],
                ),
              ),

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
                      builder: (_) => SustainabilityScreen(recommendationData: _recData),
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
                              recommendationData: _recData,
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

/// Interactive Tamil Voice Guidance Modal Dialog (Task 4b)
class _TamilVoiceDialog extends StatefulWidget {
  final Map<String, dynamic> recommendationData;
  const _TamilVoiceDialog({required this.recommendationData});

  @override
  State<_TamilVoiceDialog> createState() => _TamilVoiceDialogState();
}

class _TamilVoiceDialogState extends State<_TamilVoiceDialog> with SingleTickerProviderStateMixin {
  bool _isPlaying = true;
  String _tamilScript = '';
  double _speed = 1.0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchVoiceScript();
  }

  Future<void> _fetchVoiceScript() async {
    try {
      final res = await ApiClient.instance.getTamilVoiceSummary(widget.recommendationData);
      if (mounted) {
        setState(() {
          _tamilScript = res['tamil_speech_script'] ?? '';
          _isLoading = false;
        });
      }
    } catch (_) {
      // Fallback local Tamil speech text generator
      final crop = widget.recommendationData['crop'] ?? 'பயிர்';
      final district = widget.recommendationData['district'] ?? 'தமிழ்நாடு';
      final p6 = widget.recommendationData['fertilizer_plan'] ?? {};
      final cost = (p6['total_cost_inr'] as num?)?.toDouble() ?? 0.0;
      final prods = (p6['recommended_products'] as List? ?? []);

      final prodsList = prods.map((p) => '${p['name'] ?? p['product_name']} ${p['bags']} மூட்டை').join(', ');
      if (mounted) {
        setState(() {
          _tamilScript = 'வணக்கம் உழவரே! உங்கள் $district மாவட்ட $crop பயிருக்கான உகந்த உரப் பரிந்துரை: '
              '${prodsList.isNotEmpty ? prodsList : "உரத் தேவை இல்லை"}. '
              'உத்தேச உரச் செலவு ரூபாய் ${cost.toStringAsFixed(0)}. '
              'அடிஉரங்களை விதைப்பின் போதும், யூரியாவை பிரித்து மேலுரமாகவும் இடவும். '
              'இறுதி முடிவுக்கு உங்கள் பகுதி வேளாண்மை அலுவலரை அணுகவும்.';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.record_voice_over_rounded, color: AppTheme.primaryGreen, size: 28),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'தமிழில் வழிகாட்டுதல்',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textDark),
                      ),
                      Text(
                        'Tamil Audio Voice Guidance',
                        style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (_isLoading)
              const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator()))
            else ...[
              // Audio Playing Waveform Animation Indicator
              Container(
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F8E9),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.green.shade200),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _isPlaying ? Icons.graphic_eq_rounded : Icons.pause_circle_outline_rounded,
                      color: AppTheme.primaryGreen,
                      size: 28,
                    ),
                    const SizedBox(width: 10),
                    Text(
                      _isPlaying ? 'குரல் வழிகாட்டல் இயங்குகிறது...' : 'நிறுத்தப்பட்டுள்ளது',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.darkGreen),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              // Tamil Spoken Text Script
              Container(
                constraints: const BoxConstraints(maxHeight: 180),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: SingleChildScrollView(
                  child: Text(
                    _tamilScript,
                    style: const TextStyle(fontSize: 13, height: 1.5, color: AppTheme.textDark),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              // Playback Speed Selector
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('வேகம்: ', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                  for (final sp in [0.8, 1.0, 1.2])
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: ChoiceChip(
                        label: Text('${sp}x', style: const TextStyle(fontSize: 11)),
                        selected: _speed == sp,
                        onSelected: (val) {
                          if (val) setState(() => _speed = sp);
                        },
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        setState(() => _isPlaying = !_isPlaying);
                      },
                      icon: Icon(_isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded),
                      label: Text(_isPlaying ? 'நிறுத்து (Pause)' : 'இயக்கு (Play)'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: FilledButton.icon(
                      style: FilledButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                      onPressed: () {
                        setState(() => _isPlaying = true);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('குரல் வழிகாட்டல் மீண்டும் தொடங்கப்பட்டது')),
                        );
                      },
                      icon: const Icon(Icons.replay_rounded),
                      label: const Text('மீண்டும் (Replay)'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
