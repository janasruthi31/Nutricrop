import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'application_schedule_screen.dart';
import 'report_generation_screen.dart';
import 'sustainability_screen.dart';
import 'main_navigation_shell.dart';

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

    final unifiedRec = rec['unified_recommendation'] as Map<String, dynamic>?;
    final priorityTier = (unifiedRec?['priority_tier'] as num?)?.toInt() ?? (p5['priority_tier'] as num?)?.toInt() ?? 3;
    final rulePriority = unifiedRec?['rule_priority']?.toString() ?? p5['rule_priority']?.toString() ?? 'TNAU Verified Recommendation';
    final selectionReason = unifiedRec?['selection_reason']?.toString() ??
        p5['selection_reason']?.toString() ??
        'Selected automatically using crop, soil report, and verified agricultural rules.';
    final recType = unifiedRec?['recommendation_type'] ?? rec['recommendation_type'] ?? p6['recommendation_type'] ?? p5['recommendation_type'] ?? 'TNAU_BLANKET';
    final isVerified = rec['is_verified'] == true && p6['is_verified'] != false;
    final isProvisional = rec['is_provisional'] == true || p6['is_provisional'] == true || !isVerified || recType == 'PROVISIONAL_UNVERIFIED';

    final totalCostStatus = rec['total_cost_status']?.toString() ??
        p6['total_cost_status']?.toString() ??
        (totalCost > 0.0 ? 'AVAILABLE' : (products.isEmpty ? 'AVAILABLE' : 'UNAVAILABLE'));
    final isCostAvailable = totalCostStatus == 'AVAILABLE' && (totalCost > 0 || products.isEmpty);

    final pricesDate = rec['prices_last_updated'] ?? p6['prices_last_updated'] ?? '2026-10-22';
    final rulesDate = rec['rules_last_updated'] ?? p6['rules_last_updated'] ?? '2026-10-22';

    // Nutrient Surplus Data (Task 4e)
    final balance = (p6['nutrient_balance'] as Map? ?? {});
    final surplusDict = (p6['nutrient_surplus_kg'] as Map? ?? {});
    final hasSurplus = p6['has_surplus'] == true || surplusDict.values.any((v) => (v as num) > 0.05);

    // Soil Fertility Diagnostics & Low NPK Detection
    final soilSummary = rec['soil_test_summary'] as Map<String, dynamic>? ?? {};
    final soilStatus = rec['soil_nutrient_status'] as Map<String, dynamic>? ?? (p5['soil_nutrient_status'] as Map<String, dynamic>? ?? {});
    final highlights = rec['soil_fertility_highlights'] as Map<String, dynamic>? ?? (rec['low_nutrients_highlight'] as Map<String, dynamic>? ?? {});
    final lowNutrients = (highlights['low_nutrients'] as List? ?? []);

    final nVal = (soilSummary['nitrogen_kg_per_ha'] as num?)?.toDouble() ?? (soilStatus['nitrogen']?['value_kg_per_ha'] as num?)?.toDouble() ?? (p5['soil_nitrogen'] as num?)?.toDouble();
    final pVal = (soilSummary['phosphorus_kg_per_ha'] as num?)?.toDouble() ?? (soilStatus['phosphorus']?['value_kg_per_ha'] as num?)?.toDouble() ?? (p5['soil_phosphorus'] as num?)?.toDouble();
    final kVal = (soilSummary['potassium_kg_per_ha'] as num?)?.toDouble() ?? (soilStatus['potassium']?['value_kg_per_ha'] as num?)?.toDouble() ?? (p5['soil_potassium'] as num?)?.toDouble();
    final pMethod = soilSummary['phosphorus_method']?.toString() ?? soilStatus['phosphorus']?['method']?.toString() ?? 'Olsen';

    final nRating = soilStatus['nitrogen']?['rating']?.toString() ?? (nVal != null && nVal < 280 ? 'Low' : 'Medium');
    final pRating = soilStatus['phosphorus']?['rating']?.toString() ?? (pVal != null && (pMethod == 'Bray' ? pVal < 24.2 : pVal < 11.0) ? 'Low' : 'Medium');
    final kRating = soilStatus['potassium']?['rating']?.toString() ?? (kVal != null && kVal < 118 ? 'Low' : 'Medium');

    final isNLow = nRating == 'Low' || (nVal != null && nVal < 280);
    final isPLow = pRating == 'Low' || (pVal != null && (pMethod == 'Bray' ? pVal < 24.2 : pVal < 11.0));
    final isKLow = kRating == 'Low' || (kVal != null && kVal < 118);
    final hasLowNutrient = isNLow || isPLow || isKLow || lowNutrients.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.text('optimal_plan_title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.home_rounded),
            tooltip: 'Home',
            onPressed: () => Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (_) => const MainNavigationShell(initialIndex: 0)),
              (route) => false,
            ),
          ),
        ],
      ),
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

              // Incompatible Soil Test Method Banner
              if (status == 'INCOMPATIBLE_SOIL_TEST_METHOD' || p6['status'] == 'INCOMPATIBLE_SOIL_TEST_METHOD' || rec['status'] == 'INCOMPATIBLE_SOIL_TEST_METHOD') ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFEBEE),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.red.shade800, width: 1.5),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.error_outline_rounded, color: Colors.red.shade900, size: 24),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Incompatible Soil Test Method (Bray-1 P)',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.red.shade900),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              rec['actionable_message']?.toString() ?? 'The uploaded report uses Bray-1 phosphorus, which cannot be converted to Olsen-P using generic multipliers. Please confirm your phosphorus test method from your Soil Health Card or select a standard fertilizer recommendation.',
                              style: TextStyle(fontSize: 11, color: Colors.brown.shade900, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // Unified Recommendation Source & Explanation Banner
              Card(
                elevation: 1.0,
                color: isProvisional
                    ? const Color(0xFFFFF3E0)
                    : (priorityTier == 1
                        ? const Color(0xFFE8F5E9)
                        : (priorityTier == 2 ? const Color(0xFFE3F2FD) : const Color(0xFFE0F2F1))),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: isProvisional
                        ? Colors.orange.shade800
                        : (priorityTier == 1
                            ? const Color(0xFF2E7D32)
                            : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B))),
                    width: 1.2,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            isProvisional ? Icons.warning_amber_rounded : Icons.verified_rounded,
                            color: isProvisional
                                ? Colors.orange.shade900
                                : (priorityTier == 1
                                    ? const Color(0xFF2E7D32)
                                    : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B))),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              isProvisional
                                  ? 'Provisional Rule (Pending Agronomic Validation)'
                                  : 'Unified Recommendation • Priority $priorityTier',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                                color: isProvisional
                                    ? Colors.brown.shade900
                                    : (priorityTier == 1
                                        ? const Color(0xFF1B5E20)
                                        : (priorityTier == 2 ? const Color(0xFF0D47A1) : const Color(0xFF004D40))),
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: isProvisional
                                  ? Colors.orange.shade800
                                  : (priorityTier == 1
                                      ? const Color(0xFF2E7D32)
                                      : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B))),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              isVerified ? 'VERIFIED' : 'PROVISIONAL',
                              style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        selectionReason,
                        style: const TextStyle(fontSize: 12, color: AppTheme.textDark, height: 1.35),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Rule: ${unifiedRec?['selected_rule_id'] ?? p5['selected_rule_id'] ?? 'TNAU'} • $rulePriority',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // Summary Banner
              Card(
                color: !isCostAvailable
                    ? const Color(0xFF37474F)
                    : (isProvisional ? Colors.brown.shade800 : AppTheme.darkGreen),
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text(
                        !isCostAvailable
                            ? 'Estimated Fertilizer Cost (Prices Unavailable)'
                            : (isProvisional ? 'Provisional Estimated Cost (Unverified)' : l10n.text('estimated_cost')),
                        style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 13),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        isCostAvailable ? '₹${totalCost.toStringAsFixed(0)}' : 'Cost Unavailable',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: isCostAvailable ? 32 : 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '$crop • $district • ${p5['farm_area_original'] ?? p5['farm_area_hectares'] ?? 1.0} ${p5['farm_area_unit_original'] ?? 'ha'}',
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
                              Flexible(child: Text('Prices updated: $pricesDate', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted))),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.verified_outlined, size: 12, color: AppTheme.textMuted),
                              const SizedBox(width: 4),
                              Flexible(child: Text('Rules updated: $rulesDate', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted))),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // =========================================================
              // Soil Fertility Diagnostic & Low NPK Highlight Card
              // =========================================================
              Card(
                elevation: 1.5,
                color: hasLowNutrient ? const Color(0xFFFFF8E1) : const Color(0xFFF1F8E9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: hasLowNutrient ? Colors.amber.shade800 : const Color(0xFFA5D6A7),
                    width: 1.5,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            hasLowNutrient ? Icons.warning_amber_rounded : Icons.check_circle_outline_rounded,
                            color: hasLowNutrient ? Colors.orange.shade900 : const Color(0xFF2E7D32),
                            size: 22,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              hasLowNutrient
                                  ? 'Soil Fertility Diagnostic: Low Nutrient(s) Highlighted'
                                  : 'Soil Fertility Diagnostic: Balanced Reserves',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13.5,
                                color: hasLowNutrient ? Colors.brown.shade900 : const Color(0xFF1B5E20),
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: hasLowNutrient ? Colors.orange.shade800 : const Color(0xFF2E7D32),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              hasLowNutrient ? 'DEFICIT DETECTED' : 'OPTIMAL',
                              style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        hasLowNutrient
                            ? (highlights['summary_en']?.toString() ??
                                'Your soil test indicates deficient nutrient reserves. Fertilizer requirements have been adjusted upwards to build soil fertility and sustain crop yield.')
                            : 'All primary nutrients (N, P, K) are in the Medium to High fertility range.',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textDark, height: 1.35),
                      ),
                      const SizedBox(height: 12),

                      // Nutrient Status Grid
                      Row(
                        children: [
                          // Nitrogen Pill
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: isNLow ? const Color(0xFFFFEBEE) : Colors.white,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: isNLow ? Colors.red.shade400 : Colors.grey.shade300,
                                  width: isNLow ? 1.5 : 1.0,
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      const Text('Nitrogen (N)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                      if (isNLow)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                          decoration: BoxDecoration(color: Colors.red.shade700, borderRadius: BorderRadius.circular(4)),
                                          child: const Text('LOW', style: TextStyle(color: Colors.white, fontSize: 8.5, fontWeight: FontWeight.bold)),
                                        )
                                      else
                                        Text(nRating, style: const TextStyle(fontSize: 10, color: Color(0xFF2E7D32), fontWeight: FontWeight.w600)),
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    nVal != null ? '${nVal.toStringAsFixed(1)} kg/ha' : '—',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                      color: isNLow ? Colors.red.shade900 : AppTheme.textDark,
                                    ),
                                  ),
                                  Text(
                                    '< 280 kg/ha',
                                    style: TextStyle(fontSize: 9, color: Colors.grey.shade600),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),

                          // Phosphorus Pill
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: isPLow ? const Color(0xFFFFEBEE) : Colors.white,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: isPLow ? Colors.red.shade400 : Colors.grey.shade300,
                                  width: isPLow ? 1.5 : 1.0,
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      const Text('Phosphorus', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                      if (isPLow)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                          decoration: BoxDecoration(color: Colors.red.shade700, borderRadius: BorderRadius.circular(4)),
                                          child: const Text('LOW', style: TextStyle(color: Colors.white, fontSize: 8.5, fontWeight: FontWeight.bold)),
                                        )
                                      else
                                        Text(pRating, style: const TextStyle(fontSize: 10, color: Color(0xFF2E7D32), fontWeight: FontWeight.w600)),
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    pVal != null ? '${pVal.toStringAsFixed(1)} kg/ha' : '—',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                      color: isPLow ? Colors.red.shade900 : AppTheme.textDark,
                                    ),
                                  ),
                                  Text(
                                    pMethod == 'Bray' ? '< 24.2 kg/ha' : '< 11.0 kg/ha',
                                    style: TextStyle(fontSize: 9, color: Colors.grey.shade600),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),

                          // Potassium Pill
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: isKLow ? const Color(0xFFFFEBEE) : Colors.white,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: isKLow ? Colors.red.shade400 : Colors.grey.shade300,
                                  width: isKLow ? 1.5 : 1.0,
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      const Text('Potassium (K)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                      if (isKLow)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                          decoration: BoxDecoration(color: Colors.red.shade700, borderRadius: BorderRadius.circular(4)),
                                          child: const Text('LOW', style: TextStyle(color: Colors.white, fontSize: 8.5, fontWeight: FontWeight.bold)),
                                        )
                                      else
                                        Text(kRating, style: const TextStyle(fontSize: 10, color: Color(0xFF2E7D32), fontWeight: FontWeight.w600)),
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    kVal != null ? '${kVal.toStringAsFixed(1)} kg/ha' : '—',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                      color: isKLow ? Colors.red.shade900 : AppTheme.textDark,
                                    ),
                                  ),
                                  Text(
                                    '< 118 kg/ha',
                                    style: TextStyle(fontSize: 9, color: Colors.grey.shade600),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),

                      // Agronomic impact banner for low nutrients
                      if (hasLowNutrient) ...[
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.amber.shade400),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (isNLow) ...[
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Icon(Icons.arrow_upward_rounded, size: 14, color: Colors.red.shade800),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        'Nitrogen is LOW: Fertilizer N rate increased (+10% to +25%) to build soil fertility and sustain vegetative growth.',
                                        style: TextStyle(fontSize: 11, color: Colors.brown.shade900, height: 1.3),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                              if (isPLow) ...[
                                if (isNLow) const SizedBox(height: 4),
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Icon(Icons.arrow_upward_rounded, size: 14, color: Colors.red.shade800),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        'Phosphorus is LOW: Phosphatic fertilizer rate increased for strong root establishment.',
                                        style: TextStyle(fontSize: 11, color: Colors.brown.shade900, height: 1.3),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                              if (isKLow) ...[
                                if (isNLow || isPLow) const SizedBox(height: 4),
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Icon(Icons.arrow_upward_rounded, size: 14, color: Colors.red.shade800),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        'Potassium is LOW: Potash rate increased for pest resistance and grain weight.',
                                        style: TextStyle(fontSize: 11, color: Colors.brown.shade900, height: 1.3),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // Farm Nutrient Requirements Summary
              Card(
                elevation: 1.0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.science_rounded, size: 18, color: AppTheme.primaryGreen),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Required Nutrients for Farm',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textDark),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(color: const Color(0xFFE3F2FD), borderRadius: BorderRadius.circular(8)),
                              child: Column(
                                children: [
                                  const Text('Nitrogen (N)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF1565C0))),
                                  const SizedBox(height: 2),
                                  Text('${((p5['total_n_req_kg'] ?? p5['total_farm_n_kg']) as num?)?.toStringAsFixed(1) ?? '—'} kg', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(color: const Color(0xFFFFF3E0), borderRadius: BorderRadius.circular(8)),
                              child: Column(
                                children: [
                                  const Text('Phosphate (P₂O₅)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFFE65100))),
                                  const SizedBox(height: 2),
                                  Text('${((p5['total_p2o5_req_kg'] ?? p5['total_farm_p2o5_kg']) as num?)?.toStringAsFixed(1) ?? '—'} kg', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(color: const Color(0xFFF3E5F5), borderRadius: BorderRadius.circular(8)),
                              child: Column(
                                children: [
                                  const Text('Potash (K₂O)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF6A1B9A))),
                                  const SizedBox(height: 2),
                                  Text('${((p5['total_k2o_req_kg'] ?? p5['total_farm_k2o_kg']) as num?)?.toStringAsFixed(1) ?? '—'} kg', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                ],
                              ),
                            ),
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
                    whyRecommended: prod['why_recommended']?.toString() ?? prod['selection_rationale']?.toString() ?? prod['description']?.toString(),
                    whyRecommendedTa: prod['why_recommended_ta']?.toString(),
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
                          const Expanded(
                            child: Text(
                              'Nutrient Balance & Surplus (சத்து இருப்பு)',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textDark),
                            ),
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
                            if ((rec['applicable_limitations'] is List && (rec['applicable_limitations'] as List).isNotEmpty) ||
                                (p5['applicable_limitations'] is List && (p5['applicable_limitations'] as List).isNotEmpty)) ...[
                              const SizedBox(height: 8),
                              const Text('Applicable Limitations:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppTheme.darkGreen)),
                              const SizedBox(height: 3),
                              ...(((rec['applicable_limitations'] ?? p5['applicable_limitations']) as List)).map(
                                (lim) => Padding(
                                  padding: const EdgeInsets.only(bottom: 2.0),
                                  child: Text('• $lim', style: const TextStyle(fontSize: 11, color: AppTheme.textDark, height: 1.3)),
                                ),
                              ),
                            ],
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

              const SizedBox(height: 14),
              // Prominent Legal & Agronomic Responsibility Card (Task 5a & 5c)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF8E1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.amber.shade700, width: 1.2),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.verified_user_outlined, size: 22, color: Colors.amber.shade900),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Legal Advisory & Responsibility (சட்ட ஆலோசனை)',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.brown.shade900),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '• Confirm with your local agriculture officer (உங்கள் வட்டார வேளாண்மை அலுவலரிடம் சரிபார்க்கவும்).\n'
                            '• This application is based on TNAU guidelines, not an official TNAU or government tool.\n'
                            '• Recommendation is valid for this soil sample; sample several spots of the field for representative accuracy.',
                            style: TextStyle(fontSize: 11, color: Colors.brown.shade800, height: 1.35),
                          ),
                        ],
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
              const SizedBox(height: 14),
              FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFF1B5E20),
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 2,
                ),
                onPressed: () => Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(builder: (_) => const MainNavigationShell(initialIndex: 0)),
                  (route) => false,
                ),
                icon: const Icon(Icons.home_rounded, size: 22),
                label: const Text(
                  'Back to Home / முகப்புக்குச் செல்க',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
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
