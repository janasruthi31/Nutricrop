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
  String _recommendationMode = 'SOIL_HEALTH_CARD';

  @override
  void initState() {
    super.initState();
    // Default mode: If printed chemical NPK recommendations exist on report,
    // start with 'SOIL_HEALTH_CARD' mode, otherwise 'GENERAL_BLANKET'
    final prec = widget.soilProfile?['printed_recommendation'] ?? widget.flowData['printed_recommendation'];
    final bool hasPrintedDose = prec is Map &&
        (prec['n'] != null ||
            prec['p2o5'] != null ||
            prec['k2o'] != null ||
            prec['n_kg_per_acre'] != null ||
            prec['nitrogen_kg_per_acre'] != null);
    if (hasPrintedDose) {
      _recommendationMode = 'SOIL_HEALTH_CARD';
    } else {
      _recommendationMode = 'GENERAL_BLANKET';
    }
    _calculateNpk();
  }

  void _switchMode(String newMode) {
    if (_recommendationMode == newMode) return;
    setState(() {
      _recommendationMode = newMode;
    });
    _calculateNpk();
  }

  Future<void> _calculateNpk() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Extract soil test values from soilProfile or flowData without dummy defaults
      double? soilN;
      String soilNUnit = 'kg/acre';
      double? soilP;
      String soilPUnit = 'kg/acre';
      double? soilK;
      String soilKUnit = 'kg/acre';
      double? organicCarbon;
      double? ph;
      double? ec;
      String pMethod = 'Olsen';

      // Check flowData first
      if (widget.flowData['soil_nitrogen'] != null) {
        soilN = double.tryParse(widget.flowData['soil_nitrogen'].toString());
      }
      if (widget.flowData['soil_phosphorus'] != null) {
        soilP = double.tryParse(widget.flowData['soil_phosphorus'].toString());
      }
      if (widget.flowData['soil_potassium'] != null) {
        soilK = double.tryParse(widget.flowData['soil_potassium'].toString());
      }
      if (widget.flowData['organic_carbon'] != null) {
        organicCarbon = double.tryParse(widget.flowData['organic_carbon'].toString());
      }
      if (widget.flowData['ph'] != null) {
        ph = double.tryParse(widget.flowData['ph'].toString());
      }
      if (widget.flowData['ec'] != null) {
        ec = double.tryParse(widget.flowData['ec'].toString());
      }

      if (widget.soilProfile != null) {
        final p = widget.soilProfile!;
        if (p['nitrogen'] is Map && p['nitrogen']['value'] != null) {
          final val = double.tryParse(p['nitrogen']['value'].toString());
          if (val != null) soilN = val;
          if (p['nitrogen']['unit'] != null) soilNUnit = p['nitrogen']['unit'].toString();
        } else if (p['nitrogen'] is num) {
          soilN = (p['nitrogen'] as num).toDouble();
        }

        if (p['phosphorus'] is Map && p['phosphorus']['value'] != null) {
          final val = double.tryParse(p['phosphorus']['value'].toString());
          if (val != null) soilP = val;
          if (p['phosphorus']['unit'] != null) soilPUnit = p['phosphorus']['unit'].toString();
          if (p['phosphorus']['method'] != null) pMethod = p['phosphorus']['method'].toString();
        } else if (p['phosphorus'] is num) {
          soilP = (p['phosphorus'] as num).toDouble();
        }

        if (p['potassium'] is Map && p['potassium']['value'] != null) {
          final val = double.tryParse(p['potassium']['value'].toString());
          if (val != null) soilK = val;
          if (p['potassium']['unit'] != null) soilKUnit = p['potassium']['unit'].toString();
        } else if (p['potassium'] is num) {
          soilK = (p['potassium'] as num).toDouble();
        }

        if (p['organic_carbon'] is Map && p['organic_carbon']['value'] != null) {
          final val = double.tryParse(p['organic_carbon']['value'].toString());
          if (val != null) organicCarbon = val;
        } else if (p['organic_carbon'] is num) {
          organicCarbon = (p['organic_carbon'] as num).toDouble();
        }

        if (p['ph'] is Map && p['ph']['value'] != null) {
          final val = double.tryParse(p['ph']['value'].toString());
          if (val != null) ph = val;
        } else if (p['ph'] is num) {
          ph = (p['ph'] as num).toDouble();
        }

        if (p['ec'] is Map && p['ec']['value'] != null) {
          final val = double.tryParse(p['ec']['value'].toString());
          if (val != null) ec = val;
        } else if (p['ec'] is num) {
          ec = (p['ec'] as num).toDouble();
        }

        if (p['fields'] is List) {
          final fields = p['fields'] as List;
          for (final f in fields) {
            if (f is Map) {
              final k = f['field']?.toString() ?? '';
              final val = (f['confirmed_value'] ?? f['value'] ?? f['ocr_value']);
              final numVal = double.tryParse(val?.toString() ?? '');
              if (numVal != null) {
                if (k == 'nitrogen') {
                  soilN = numVal;
                  if (f['unit'] != null) soilNUnit = f['unit'].toString();
                }
                if (k == 'phosphorus') {
                  soilP = numVal;
                  if (f['unit'] != null) soilPUnit = f['unit'].toString();
                  if (f['test_method'] != null) pMethod = f['test_method'].toString();
                }
                if (k == 'potassium') {
                  soilK = numVal;
                  if (f['unit'] != null) soilKUnit = f['unit'].toString();
                }
                if (k == 'organic_carbon') organicCarbon = numVal;
                if (k == 'ph') ph = numVal;
                if (k == 'ec') ec = numVal;
              }
            }
          }
        }
      }

      final farmArea = (widget.flowData['area'] is num)
          ? (widget.flowData['area'] as num).toDouble()
          : (double.tryParse(widget.flowData['area']?.toString() ?? '1.0') ?? 1.0);
      final farmAreaUnit = widget.flowData['area_unit']?.toString().toLowerCase().contains('hect') == true
          ? 'hectare'
          : 'acre';

      final payload = {
        'crop': widget.flowData['crop'] ?? 'Rice',
        'variety': widget.flowData['variety'],
        'district': widget.flowData['district'] ?? 'Thanjavur',
        'soil_series': widget.flowData['soil_series'] ?? 'Palavidhi',
        'season': widget.flowData['season'] ?? 'Kharif',
        'irrigation_method': widget.flowData['irrigation'] ?? 'Irrigated',
        'target_yield': widget.flowData['target_yield'] ?? 2.5,
        'soil_nitrogen': soilN,
        'soil_nitrogen_unit': soilNUnit,
        'soil_phosphorus': soilP,
        'soil_phosphorus_unit': soilPUnit,
        'soil_phosphorus_method': pMethod,
        'soil_potassium': soilK,
        'soil_potassium_unit': soilKUnit,
        'organic_carbon': organicCarbon,
        'ph': ph,
        'ec': ec,
        'fym_applied_t_per_ha': widget.flowData['fym_applied_t_per_ha'],
        'farm_area': farmArea,
        'farm_area_unit': farmAreaUnit,
        'soil_profile': widget.soilProfile,
        'recommendation_mode': _recommendationMode == 'SOIL_HEALTH_CARD' ? 'SOIL_HEALTH_CARD' : 'CALCULATED_AGRONOMIC',
        'recommendation_type': _recommendationMode == 'GENERAL_BLANKET' ? 'GENERAL_BLANKET' : (_recommendationMode == 'SOIL_HEALTH_CARD' ? 'SOIL_HEALTH_CARD' : 'SOIL_SPECIFIC_STCR'),
        'allow_unverified': true,
      };

      // Check for printed recommendation in soilProfile or flowData
      final prec = widget.soilProfile?['printed_recommendation'] ?? widget.flowData['printed_recommendation'];
      if (prec is Map) {
        payload['printed_recommendation'] = prec;
        if (prec['n_kg_per_acre'] != null) payload['printed_n_rate'] = prec['n_kg_per_acre'];
        if (prec['p2o5_kg_per_acre'] != null) payload['printed_p2o5_rate'] = prec['p2o5_kg_per_acre'];
        if (prec['k2o_kg_per_acre'] != null) payload['printed_k2o_rate'] = prec['k2o_kg_per_acre'];
        if (prec['unit'] != null) payload['printed_rate_unit'] = prec['unit'];
      }

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

  Widget _nutrientCard({
    required String name,
    required String symbol,
    required double perHa,
    required double perAcre,
    required double total,
    required String primaryUnit,
    required Color color,
  }) {
    final isAcrePrimary = primaryUnit.toLowerCase().contains('acre');
    final primaryRate = isAcrePrimary ? perAcre : perHa;
    final primaryRateUnit = isAcrePrimary ? 'kg/acre' : 'kg/ha';
    final secondaryRate = isAcrePrimary ? perHa : perAcre;
    final secondaryRateUnit = isAcrePrimary ? 'kg/ha' : 'kg/acre';

    return Card(
      elevation: 1.5,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(14),
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
                  Row(
                    children: [
                      Text(
                        '${primaryRate.toStringAsFixed(1)} $primaryRateUnit',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: color),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '(approx ${secondaryRate.toStringAsFixed(1)} $secondaryRateUnit)',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${total.toStringAsFixed(1)} kg',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
                ),
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

    final netNHa = (p5['n_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_n_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final netPHa = (p5['p2o5_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_p2o5_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final netKHa = (p5['k2o_req_kg_per_ha'] as num?)?.toDouble() ?? (p5['net_k2o_kg_per_ha'] as num?)?.toDouble() ?? 0.0;

    final netNAcre = (p5['n_req_kg_per_acre'] as num?)?.toDouble() ?? (netNHa * 0.4046856422);
    final netPAcre = (p5['p2o5_req_kg_per_acre'] as num?)?.toDouble() ?? (netPHa * 0.4046856422);
    final netKAcre = (p5['k2o_req_kg_per_acre'] as num?)?.toDouble() ?? (netKHa * 0.4046856422);

    final totN = (p5['total_n_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_n_kg'] as num?)?.toDouble() ?? 0.0;
    final totP = (p5['total_p2o5_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_p2o5_kg'] as num?)?.toDouble() ?? 0.0;
    final totK = (p5['total_k2o_req_kg'] as num?)?.toDouble() ?? (p5['total_farm_k2o_kg'] as num?)?.toDouble() ?? 0.0;

    final ruleId = p5['selected_rule_id']?.toString() ?? 'N/A';
    final method = p5['calculation_method']?.toString() ?? p5['selected_method']?.toString() ?? 'Deterministic Agronomic Schedule';
    final isVerified = _recommendationResponse?['is_verified'] == true || p5['is_verified_rule'] == true;
    final verificationStatus = p5['verification_status']?.toString() ?? (isVerified ? 'VERIFIED' : 'PENDING_AGRONOMIC_VALIDATION');
    final recSource = p5['recommendation_source']?.toString() ?? (_recommendationMode == 'SOIL_HEALTH_CARD' ? 'Uploaded Soil Health Card' : (_recommendationMode == 'GENERAL_BLANKET' ? 'TNAU Crop Production Guide 2020' : 'TNAU Agronomic Schedule'));

    final farmAreaOrig = (p5['farm_area_original'] as num?)?.toDouble() ?? (widget.flowData['area'] is num ? (widget.flowData['area'] as num).toDouble() : 1.0);
    final farmAreaUnitOrig = p5['farm_area_unit_original']?.toString() ?? (widget.flowData['area_unit']?.toString() ?? 'acre');
    final farmAreaHa = (p5['farm_area_hectares'] as num?)?.toDouble() ?? (farmAreaUnitOrig == 'acre' ? farmAreaOrig * 0.4046856422 : farmAreaOrig);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('npk_title'))),
      body: SafeArea(
        child: _isLoading
            ? const LoadingView(message: 'Calculating nutrient requirements and unit conversions...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _calculateNpk)
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Mode Selection Toggle (3 Modes: Soil Health Card, General Blanket, Soil-Specific STCR)
                        Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade200,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => _switchMode('SOIL_HEALTH_CARD'),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 8),
                                    decoration: BoxDecoration(
                                      color: _recommendationMode == 'SOIL_HEALTH_CARD' ? Colors.white : Colors.transparent,
                                      borderRadius: BorderRadius.circular(8),
                                      boxShadow: _recommendationMode == 'SOIL_HEALTH_CARD'
                                          ? [const BoxStyle(color: Colors.black12, blurRadius: 4)]
                                          : null,
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      'Soil Health Card\n(Printed)',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: _recommendationMode == 'SOIL_HEALTH_CARD' ? FontWeight.bold : FontWeight.normal,
                                        color: _recommendationMode == 'SOIL_HEALTH_CARD' ? AppTheme.darkGreen : AppTheme.textMuted,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => _switchMode('GENERAL_BLANKET'),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 8),
                                    decoration: BoxDecoration(
                                      color: _recommendationMode == 'GENERAL_BLANKET' ? Colors.white : Colors.transparent,
                                      borderRadius: BorderRadius.circular(8),
                                      boxShadow: _recommendationMode == 'GENERAL_BLANKET'
                                          ? [const BoxStyle(color: Colors.black12, blurRadius: 4)]
                                          : null,
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      'General Blanket\n(TNAU Verified)',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: _recommendationMode == 'GENERAL_BLANKET' ? FontWeight.bold : FontWeight.normal,
                                        color: _recommendationMode == 'GENERAL_BLANKET' ? const Color(0xFF0277BD) : AppTheme.textMuted,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => _switchMode('CALCULATED_AGRONOMIC'),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 8),
                                    decoration: BoxDecoration(
                                      color: _recommendationMode == 'CALCULATED_AGRONOMIC' ? Colors.white : Colors.transparent,
                                      borderRadius: BorderRadius.circular(8),
                                      boxShadow: _recommendationMode == 'CALCULATED_AGRONOMIC'
                                          ? [const BoxStyle(color: Colors.black12, blurRadius: 4)]
                                          : null,
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      'Soil-Specific STCR\n(Target Yield)',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: _recommendationMode == 'CALCULATED_AGRONOMIC' ? FontWeight.bold : FontWeight.normal,
                                        color: _recommendationMode == 'CALCULATED_AGRONOMIC' ? AppTheme.darkGreen : AppTheme.textMuted,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Header / Rule Status Banner
                        Card(
                          color: _recommendationMode == 'SOIL_HEALTH_CARD'
                              ? const Color(0xFFE8F5E9)
                              : (_recommendationMode == 'GENERAL_BLANKET'
                                  ? const Color(0xFFE1F5FE)
                                  : (isVerified ? AppTheme.lightGreen : const Color(0xFFFFF8E1))),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(
                                      _recommendationMode == 'SOIL_HEALTH_CARD'
                                          ? Icons.description_rounded
                                          : (_recommendationMode == 'GENERAL_BLANKET'
                                              ? Icons.assignment_turned_in_rounded
                                              : (isVerified ? Icons.verified_rounded : Icons.warning_amber_rounded)),
                                      color: _recommendationMode == 'SOIL_HEALTH_CARD'
                                          ? const Color(0xFF2E7D32)
                                          : (_recommendationMode == 'GENERAL_BLANKET'
                                              ? const Color(0xFF0277BD)
                                              : (isVerified ? AppTheme.primaryGreen : Colors.amber.shade900)),
                                      size: 24,
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        _recommendationMode == 'SOIL_HEALTH_CARD'
                                            ? 'Uploaded Soil Health Card Recommendation'
                                            : (_recommendationMode == 'GENERAL_BLANKET'
                                                ? 'General Blanket Recommendation (Rule: $ruleId)'
                                                : (isVerified
                                                    ? 'Soil-Specific STCR Rule: $ruleId'
                                                    : 'Rule Pending Agronomic Validation: $ruleId')),
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 14,
                                          color: _recommendationMode == 'SOIL_HEALTH_CARD'
                                              ? const Color(0xFF1B5E20)
                                              : (_recommendationMode == 'GENERAL_BLANKET'
                                                  ? const Color(0xFF01579B)
                                                  : (isVerified ? AppTheme.darkGreen : Colors.brown.shade900)),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'Recommendation Type: ${_recommendationMode == 'SOIL_HEALTH_CARD' ? 'Uploaded Soil Health Card (Printed Dose)' : (_recommendationMode == 'GENERAL_BLANKET' ? 'Verified TNAU Blanket Recommendation (Soil Rating Adjusted)' : (isVerified ? 'Verified TNAU STCR Targeted-Yield Equation' : 'Provisional Rule (Pending Agronomic Validation)'))}',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: _recommendationMode == 'GENERAL_BLANKET' ? const Color(0xFF0277BD) : (isVerified ? AppTheme.darkGreen : Colors.brown.shade900),
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Validation Status: $verificationStatus',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: isVerified ? AppTheme.primaryGreen : Colors.amber.shade900,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text('Recommendation Source: $recSource', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                                Text('Calculation Method: $method', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Text('Crop: ${widget.flowData['crop']}', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                    const Text(' | ', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                    Text(
                                      'Farm Area: $farmAreaOrig $farmAreaUnitOrig (${farmAreaHa.toStringAsFixed(2)} ha)',
                                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                                    ),
                                    if (_recommendationMode == 'CALCULATED_AGRONOMIC') ...[
                                      const Text(' | ', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                      Text('Target: ${widget.flowData['target_yield']} t/ha',
                                          style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                    ],
                                  ],
                                ),
                                if (!isVerified && _recommendationMode == 'CALCULATED_AGRONOMIC') ...[
                                  const SizedBox(height: 10),
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: Colors.amber.shade50,
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: Colors.amber.shade700, width: 1.5),
                                    ),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Icon(Icons.warning_amber_rounded, size: 20, color: Colors.amber.shade900),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(
                                                'This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable.',
                                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.brown.shade900),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          'Rule $ruleId applies a standard TNAU schedule awaiting official site-specific STCR equation calibration. To use a verified schedule, switch to "General Blanket" or "Soil Health Card" above.',
                                          style: TextStyle(fontSize: 11, color: Colors.brown.shade800, height: 1.4),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Missing Inputs Warning or Nutrient Requirement Cards
                        if (p5['status'] == 'MISSING_INPUTS' || p5['status'] == 'VALIDATION_ERROR') ...[
                          Card(
                            color: const Color(0xFFFFF3E0),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: BorderSide(color: Colors.orange.shade800, width: 1.5),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Icon(Icons.error_outline_rounded, color: Colors.orange.shade900, size: 24),
                                      const SizedBox(width: 10),
                                      const Expanded(
                                        child: Text(
                                          'Recommendation Cannot Yet Be Calculated Reliably',
                                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFFBF360C)),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    p5['message']?.toString() ?? 'Required soil data or an applicable validated rule is unavailable.',
                                    style: const TextStyle(fontSize: 13, color: AppTheme.textDark, height: 1.4),
                                  ),
                                  if (p5['missing_inputs'] is List && (p5['missing_inputs'] as List).isNotEmpty) ...[
                                    const SizedBox(height: 6),
                                    Text(
                                      'Missing parameters: ${(p5['missing_inputs'] as List).join(', ')}',
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFFD84315)),
                                    ),
                                  ],
                                  const SizedBox(height: 8),
                                  const Text(
                                    'AgroWise AI adheres strictly to agronomic standards: fertilizer doses are never fabricated or estimated when essential soil test values are absent.',
                                    style: TextStyle(fontSize: 11, color: AppTheme.textMuted, fontStyle: FontStyle.italic),
                                  ),
                                  if (_recommendationMode == 'SOIL_HEALTH_CARD') ...[
                                    const SizedBox(height: 12),
                                    Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: Colors.blue.shade50,
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(color: Colors.blue.shade300),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            'Why is this empty?',
                                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blue.shade900),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            'The soil testing laboratory left the recommendation columns ("உரக் கலவை-1 / உரக் கலவை-2") blank on this physical card. Tap below to view the official TNAU recommended schedule calculated from your soil test values.',
                                            style: TextStyle(fontSize: 12, color: Colors.blue.shade900, height: 1.3),
                                          ),
                                          const SizedBox(height: 10),
                                          FilledButton.icon(
                                            onPressed: () => _switchMode('GENERAL_BLANKET'),
                                            icon: const Icon(Icons.verified_rounded, size: 18),
                                            label: const Text('View TNAU Verified Recommendation'),
                                            style: FilledButton.styleFrom(backgroundColor: const Color(0xFF0277BD)),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ] else ...[
                          // Nutrient Requirement Cards
                          _nutrientCard(
                            name: 'Nitrogen Requirement (N)',
                            symbol: 'N',
                            perHa: netNHa,
                            perAcre: netNAcre,
                            total: totN,
                            primaryUnit: farmAreaUnitOrig,
                            color: const Color(0xFF1976D2),
                          ),
                          const SizedBox(height: 8),
                          _nutrientCard(
                            name: 'Phosphorus Requirement (P₂O₅)',
                            symbol: 'P₂O₅',
                            perHa: netPHa,
                            perAcre: netPAcre,
                            total: totP,
                            primaryUnit: farmAreaUnitOrig,
                            color: const Color(0xFFE65100),
                          ),
                          const SizedBox(height: 8),
                          _nutrientCard(
                            name: 'Potassium Requirement (K₂O)',
                            symbol: 'K₂O',
                            perHa: netKHa,
                            perAcre: netKAcre,
                            total: totK,
                            primaryUnit: farmAreaUnitOrig,
                            color: const Color(0xFF6A1B9A),
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Soil Test Status & Official TNAU Interpretation Card
                        Card(
                          elevation: 1.0,
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Row(
                                  children: [
                                    Icon(Icons.science_outlined, size: 20, color: AppTheme.primaryGreen),
                                    SizedBox(width: 8),
                                    Text('Soil Report Nutrient Status & Interpretation', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                  ],
                                ),
                                const SizedBox(height: 10),
                                if (p5['soil_nutrient_status'] is Map) ...[
                                  for (final entry in (p5['soil_nutrient_status'] as Map).entries) ...[
                                    if (entry.value is Map) ...[
                                      Container(
                                        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
                                        margin: const EdgeInsets.only(bottom: 6),
                                        decoration: BoxDecoration(
                                          color: Colors.grey.shade50,
                                          borderRadius: BorderRadius.circular(6),
                                          border: Border.all(color: Colors.grey.shade200),
                                        ),
                                        child: Row(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  Text(
                                                    '${entry.key.toString().toUpperCase()}: ${entry.value['value'] ?? 'N/A'} ${entry.value['unit'] ?? ''}',
                                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                                  ),
                                                  if (entry.value['interpretation_threshold'] != null)
                                                    Text(
                                                      entry.value['interpretation_threshold'].toString(),
                                                      style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                                                    ),
                                                ],
                                              ),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: (entry.value['status'] == 'Deficient' || entry.value['rating'] == 'Low')
                                                    ? Colors.orange.shade100
                                                    : ((entry.value['status'] == 'Excessive' || entry.value['rating'] == 'High')
                                                        ? Colors.purple.shade100
                                                        : Colors.green.shade100),
                                                borderRadius: BorderRadius.circular(12),
                                              ),
                                              child: Text(
                                                '${entry.value['status'] ?? entry.value['rating'] ?? 'Tested'}',
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                  color: (entry.value['status'] == 'Deficient' || entry.value['rating'] == 'Low')
                                                      ? Colors.orange.shade900
                                                      : ((entry.value['status'] == 'Excessive' || entry.value['rating'] == 'High')
                                                          ? Colors.purple.shade900
                                                          : Colors.green.shade900),
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ],
                                ] else ...[
                                  const Text('Soil-test parameters are not fully classified.', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                ],
                                const SizedBox(height: 8),
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: Colors.blue.shade50,
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: const Text(
                                    'Note: Nutrients are identified as Deficient, Sufficient, or Excessive strictly according to valid laboratory test values and applicable TNAU thresholds. Soil test values reflect natural soil fertility and are completely separate from fertilizer doses.',
                                    style: TextStyle(fontSize: 11, color: Color(0xFF0D47A1), fontStyle: FontStyle.italic),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),

                        // Derivation Explanation Card
                        if (p5['derivation_explanation'] != null) ...[
                          Card(
                            elevation: 1.0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: BorderSide(color: Colors.green.shade200),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(14.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Row(
                                    children: [
                                      Icon(Icons.psychology_alt_outlined, color: AppTheme.primaryGreen, size: 20),
                                      SizedBox(width: 8),
                                      Text('How This Recommendation Was Derived', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    p5['derivation_explanation'].toString(),
                                    style: const TextStyle(fontSize: 12, color: AppTheme.textDark, height: 1.4),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                        ],

                        // Authoritative Reference Card
                        if (p5['authoritative_reference'] is Map) ...[
                          Builder(
                            builder: (_) {
                              final auth = p5['authoritative_reference'] as Map;
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
                                        Text('Source: ${auth['url']}', style: const TextStyle(fontSize: 11, color: Color(0xFF1565C0))),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                        ],

                        // Agronomic Rule & Conversion Details Card
                        Card(
                          elevation: 1.0,
                          child: Padding(
                            padding: const EdgeInsets.all(14.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Conversion & Calculation Precision', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                const SizedBox(height: 6),
                                const Text(
                                  '• Standard conversion factors: 1 hectare = 2.4710538147 acres; 1 acre = 0.4046856422 hectares.\n• Farm totals are calculated directly using your confirmed farm area without double-conversion.\n• Elemental P and K are converted strictly to fertilizer oxide forms (P₂O₅ and K₂O).\n• No ML yield models are used to invent fertilizer rates.',
                                  style: TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.4),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),

                        if (p5['status'] != 'MISSING_INPUTS' && p5['status'] != 'VALIDATION_ERROR') ...[
                          if (!isVerified) ...[
                            FilledButton.icon(
                              onPressed: () => _switchMode('GENERAL_BLANKET'),
                              style: FilledButton.styleFrom(
                                backgroundColor: const Color(0xFF0277BD),
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              icon: const Icon(Icons.verified_rounded),
                              label: const Text('Switch to Verified General Recommendation'),
                            ),
                            const SizedBox(height: 10),
                            if (widget.soilProfile?['printed_recommendation'] != null || widget.flowData['printed_recommendation'] != null) ...[
                              OutlinedButton.icon(
                                onPressed: () => _switchMode('SOIL_HEALTH_CARD'),
                                style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                                icon: const Icon(Icons.description_rounded),
                                label: const Text('Use Soil Health Card Printed Recommendation'),
                              ),
                              const SizedBox(height: 10),
                            ],
                          OutlinedButton.icon(
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
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.brown.shade800,
                              side: BorderSide(color: Colors.amber.shade700),
                              padding: const EdgeInsets.symmetric(vertical: 14),
                            ),
                            icon: const Icon(Icons.info_outline_rounded, color: Colors.amber),
                            label: const Text('View Provisional Plan (Unverified Only)'),
                          ),
                        ] else ...[
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
                            style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                            icon: const Icon(Icons.calculate_rounded),
                            label: Text(l10n.text('optimal_plan_title')),
                          ),
                        ],
                      ],
                    ],
                  ),
                ),
      ),
    );
  }
}

class BoxStyle extends BoxShadow {
  const BoxStyle({super.color, super.blurRadius});
}
