import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'final_recommendation_screen.dart';
import 'main_navigation_shell.dart';

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
      double? zinc;
      double? sulphur;
      double? boron;
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
      if (widget.flowData['zinc'] != null) {
        zinc = double.tryParse(widget.flowData['zinc'].toString());
      }
      if (widget.flowData['sulphur'] != null) {
        sulphur = double.tryParse(widget.flowData['sulphur'].toString());
      }
      if (widget.flowData['boron'] != null) {
        boron = double.tryParse(widget.flowData['boron'].toString());
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

        if (p['zinc'] is Map && p['zinc']['value'] != null) {
          final val = double.tryParse(p['zinc']['value'].toString());
          if (val != null) zinc = val;
        } else if (p['zinc'] is num) {
          zinc = (p['zinc'] as num).toDouble();
        }

        if (p['sulphur'] is Map && p['sulphur']['value'] != null) {
          final val = double.tryParse(p['sulphur']['value'].toString());
          if (val != null) sulphur = val;
        } else if (p['sulphur'] is num) {
          sulphur = (p['sulphur'] as num).toDouble();
        }

        if (p['boron'] is Map && p['boron']['value'] != null) {
          final val = double.tryParse(p['boron']['value'].toString());
          if (val != null) boron = val;
        } else if (p['boron'] is num) {
          boron = (p['boron'] as num).toDouble();
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
                if (k == 'zinc' || k == 'zn') zinc = numVal;
                if (k == 'sulphur' || k == 's') sulphur = numVal;
                if (k == 'boron' || k == 'b') boron = numVal;
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
        'zinc': zinc,
        'sulphur': sulphur,
        'boron': boron,
        'fym_applied_t_per_ha': widget.flowData['fym_applied_t_per_ha'] ?? 0.0,
        'previous_crop': widget.flowData['previous_crop'],
        'previous_fertilizers': widget.flowData['previous_fertilizers'] ?? [],
        'farm_area': farmArea,
        'farm_area_unit': farmAreaUnit,
        'soil_profile': widget.soilProfile,
        'recommendation_mode': 'UNIFIED',
        'recommendation_type': null,
        'allow_unverified': false,
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

  Widget _buildCardComparisonSection(Map<String, dynamic> cardComp, AppLocalizations l10n) {
    final table = cardComp['comparison_table'] as Map<String, dynamic>? ?? {};
    final warning = cardComp['warning']?.toString();
    final differs30 = cardComp['differs_more_than_30_pct'] == true;

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: differs30 ? Colors.amber.shade700 : AppTheme.primaryGreen.withOpacity(0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  differs30 ? Icons.warning_amber_rounded : Icons.compare_arrows_rounded,
                  color: differs30 ? Colors.amber.shade900 : AppTheme.primaryGreen,
                  size: 22,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    l10n.text('card_comparison_title'),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textDark),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (warning != null && differs30) ...[
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Text(
                  warning,
                  style: TextStyle(fontSize: 12, color: Colors.brown.shade900, height: 1.3),
                ),
              ),
              const SizedBox(height: 12),
            ],
            Table(
              columnWidths: const {
                0: FlexColumnWidth(1.2),
                1: FlexColumnWidth(1.5),
                2: FlexColumnWidth(1.5),
                3: FlexColumnWidth(1.2),
              },
              border: TableBorder(
                horizontalInside: BorderSide(color: Colors.grey.shade200, width: 1),
              ),
              children: [
                TableRow(
                  decoration: BoxDecoration(color: Colors.grey.shade100),
                  children: [
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                      child: Text('Nutrient', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                      child: Text(l10n.text('card_prints'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                      child: Text(l10n.text('calculated_need'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                      child: Text(l10n.text('difference'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                  ],
                ),
                ...['nitrogen', 'phosphorus', 'potassium'].map((nutrientKey) {
                  final row = table[nutrientKey] as Map<String, dynamic>? ?? {};
                  final cardVal = row['card_printed_kg_per_acre'];
                  final calcVal = row['calculated_need_kg_per_acre'];
                  final diffPct = row['difference_pct'];
                  final label = nutrientKey == 'nitrogen'
                      ? 'N'
                      : (nutrientKey == 'phosphorus' ? 'P₂O₅' : 'K₂O');

                  return TableRow(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                        child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                        child: Text(
                          cardVal != null ? '$cardVal kg/ac' : l10n.text('not_printed_on_card'),
                          style: TextStyle(
                            fontSize: 11,
                            color: cardVal != null ? AppTheme.textDark : AppTheme.textMuted,
                            fontStyle: cardVal != null ? FontStyle.normal : FontStyle.italic,
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                        child: Text(
                          calcVal != null ? '$calcVal kg/ac' : '—',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                        child: Text(
                          diffPct != null ? '${diffPct.toString()}%' : '—',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: (diffPct != null && (diffPct as num) > 30) ? Colors.orange.shade900 : AppTheme.textDark,
                          ),
                        ),
                      ),
                    ],
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAgronomicBreakdownSection(Map<String, dynamic> p5, AppLocalizations l10n) {
    final breakdown = p5['nutrient_breakdown'] as Map<String, dynamic>?;
    if (breakdown == null || breakdown.isEmpty) return const SizedBox.shrink();

    Widget buildBreakdownItem(String label, String value, {bool isDeduction = false, bool isFinal = false}) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 3.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: isFinal ? 13 : 12,
                  fontWeight: isFinal ? FontWeight.bold : FontWeight.normal,
                  color: isFinal ? AppTheme.darkGreen : AppTheme.textDark,
                ),
              ),
            ),
            Text(
              isDeduction ? '- $value' : (isFinal ? '= $value' : value),
              style: TextStyle(
                fontSize: isFinal ? 13 : 12,
                fontWeight: isFinal ? FontWeight.bold : FontWeight.w600,
                color: isFinal
                    ? AppTheme.primaryGreen
                    : (isDeduction ? Colors.red.shade700 : AppTheme.textDark),
              ),
            ),
          ],
        ),
      );
    }

    Widget buildNutrientColumn(String title, String symbol, Color color, Map<String, dynamic>? data) {
      if (data == null) return const SizedBox.shrink();
      final reqHa = data['crop_requirement_kg_per_ha'] ?? 0.0;
      final soilHa = data['soil_supply_kg_per_ha'] ?? 0.0;
      final fymHa = data['fym_credit_kg_per_ha'] ?? 0.0;
      final prevCropHa = data['previous_crop_credit_kg_per_ha'] ?? 0.0;
      final prevFertHa = data['previous_fertilizer_residual_kg_per_ha'] ?? 0.0;
      final finalHa = data['final_net_dose_kg_per_ha'] ?? 0.0;

      return Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.3), width: 1.2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 12,
                  backgroundColor: color.withOpacity(0.15),
                  child: Text(symbol, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
                ),
                const SizedBox(width: 8),
                Text(title, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
              ],
            ),
            const Divider(height: 16),
            buildBreakdownItem(l10n.text('crop_requirement'), '$reqHa kg/ha'),
            buildBreakdownItem(l10n.text('soil_supply_credit'), '$soilHa kg/ha', isDeduction: true),
            if ((fymHa as num) > 0)
              buildBreakdownItem(l10n.text('fym_credit'), '$fymHa kg/ha', isDeduction: true),
            if ((prevCropHa as num) > 0)
              buildBreakdownItem(l10n.text('previous_crop_credit'), '$prevCropHa kg/ha', isDeduction: true),
            if ((prevFertHa as num) > 0)
              buildBreakdownItem(l10n.text('previous_fertilizer_residual'), '$prevFertHa kg/ha', isDeduction: true),
            const Divider(height: 12),
            buildBreakdownItem(l10n.text('final_net_dose'), '$finalHa kg/ha', isFinal: true),
          ],
        ),
      );
    }

    return Card(
      elevation: 1.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.calculate_outlined, color: AppTheme.primaryGreen, size: 22),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    l10n.text('nutrient_breakdown_title'),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Net Dose = Crop Need - Soil Supply - FYM Credit - Prev Crop Credit - Prev Fertilizer Residual (clamped at 0)',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 12),
            buildNutrientColumn('Nitrogen (N)', 'N', const Color(0xFF1976D2), breakdown['nitrogen'] as Map<String, dynamic>?),
            buildNutrientColumn('Phosphorus (P₂O₅)', 'P', const Color(0xFFE65100), breakdown['phosphorus'] as Map<String, dynamic>?),
            buildNutrientColumn('Potassium (K₂O)', 'K', const Color(0xFF6A1B9A), breakdown['potassium'] as Map<String, dynamic>?),
          ],
        ),
      ),
    );
  }

  Widget _nutrientCard({
    required String name,
    required String symbol,
    required double perHa,
    required double perAcre,
    required double total,
    required String primaryUnit,
    required Color color,
    List<dynamic>? range,
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
                  Wrap(
                    crossAxisAlignment: WrapCrossAlignment.center,
                    spacing: 6,
                    runSpacing: 2,
                    children: [
                      Text(
                        '${primaryRate.toStringAsFixed(1)} $primaryRateUnit',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: color),
                      ),
                      Text(
                        '(approx ${secondaryRate.toStringAsFixed(1)} $secondaryRateUnit)',
                        style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                  if (range != null && range.length == 2) ...[
                    const SizedBox(height: 3),
                    Text(
                      'Recommended Range: ${range[0]} – ${range[1]} $primaryRateUnit',
                      style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: Colors.blueGrey.shade700),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${total.toStringAsFixed(1)} kg',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: color),
                ),
                const Text('Farm Total', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildMicronutrientSection(Map<String, dynamic> p5, AppLocalizations l10n) {
    final advisory = p5['micronutrient_advisory'] as Map<String, dynamic>? ?? {};
    if (advisory.isEmpty) return const SizedBox.shrink();

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.teal.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.science_rounded, color: Colors.teal.shade800, size: 22),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Secondary & Micronutrient Advisory (TNAU CPG 2020)',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5, color: Colors.teal.shade900),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ...advisory.entries.map((e) {
              final val = e.value as Map<String, dynamic>? ?? {};
              final isDef = val['is_deficient'] == true;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isDef ? const Color(0xFFFFF3E0) : const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: isDef ? Colors.orange.shade300 : Colors.green.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          val['nutrient']?.toString() ?? e.key.toUpperCase(),
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12.5, color: isDef ? Colors.brown.shade900 : Colors.green.shade900),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isDef ? Colors.orange.shade700 : Colors.green.shade700,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            val['status']?.toString() ?? (isDef ? 'Deficient' : 'Sufficient'),
                            style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          'Test: ${val['value_ppm']} ppm',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      val['advisory']?.toString() ?? '',
                      style: TextStyle(fontSize: 11.5, color: isDef ? Colors.brown.shade800 : Colors.green.shade900, height: 1.3),
                    ),
                    if (val['caution'] != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        'Caution: ${val['caution']}',
                        style: TextStyle(fontSize: 10.5, fontStyle: FontStyle.italic, color: Colors.red.shade900),
                      ),
                    ],
                  ],
                ),
              );
            }),
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

    final unifiedRec = _recommendationResponse?['unified_recommendation'] as Map<String, dynamic>?;
    final ruleId = unifiedRec?['selected_rule_id']?.toString() ?? p5['selected_rule_id']?.toString() ?? 'N/A';
    final method = p5['calculation_method']?.toString() ?? p5['selected_method']?.toString() ?? 'Deterministic Agronomic Schedule';
    final isVerified = _recommendationResponse?['is_verified'] == true || p5['is_verified_rule'] == true;
    final status = _recommendationResponse?['status']?.toString() ?? p5['status']?.toString() ?? 'UNKNOWN';
    final isSuccess = (status == 'SUCCESS' || status == 'OPTIMAL') && isVerified;

    final priorityTier = (unifiedRec?['priority_tier'] as num?)?.toInt() ?? (p5['priority_tier'] as num?)?.toInt() ?? 3;
    final rulePriority = unifiedRec?['rule_priority']?.toString() ?? p5['rule_priority']?.toString() ?? 'Verified TNAU Recommendation';
    final selectionReason = unifiedRec?['selection_reason']?.toString() ??
        p5['selection_reason']?.toString() ??
        'Selected automatically using available soil-test information, target crop, and verified TNAU rules.';
    final recSource = p5['recommendation_source']?.toString() ?? 'TNAU Crop Production Guide 2020';

    final farmAreaOrig = (p5['farm_area_original'] as num?)?.toDouble() ?? (widget.flowData['area'] is num ? (widget.flowData['area'] as num).toDouble() : 1.0);
    final farmAreaUnitOrig = p5['farm_area_unit_original']?.toString() ?? (widget.flowData['area_unit']?.toString() ?? 'acre');
    final farmAreaHa = (p5['farm_area_hectares'] as num?)?.toDouble() ?? (farmAreaUnitOrig == 'acre' ? farmAreaOrig * 0.4046856422 : farmAreaOrig);

    final isAcre = farmAreaUnitOrig.toLowerCase().contains('acre');
    final rangesMap = isAcre ? p5['recommended_range_kg_per_acre'] : p5['recommended_range_kg_per_ha'];
    final rangeN = rangesMap is Map ? rangesMap['N'] as List? : null;
    final rangeP = rangesMap is Map ? rangesMap['P2O5'] as List? : null;
    final rangeK = rangesMap is Map ? rangesMap['K2O'] as List? : null;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.text('npk_title')),
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
        child: _isLoading
            ? const LoadingView(message: 'Calculating nutrient requirements and unit conversions...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _calculateNpk)
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Unified Recommendation Header Banner
                        Card(
                          elevation: 1.5,
                          color: isSuccess
                              ? (priorityTier == 1
                                  ? const Color(0xFFE8F5E9)
                                  : (priorityTier == 2 ? const Color(0xFFE3F2FD) : const Color(0xFFE0F2F1)))
                              : const Color(0xFFFFF3E0),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(
                              color: isSuccess
                                  ? (priorityTier == 1
                                      ? const Color(0xFF2E7D32)
                                      : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B)))
                                  : Colors.orange.shade800,
                              width: 1.2,
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
                                      isSuccess ? Icons.verified_rounded : Icons.warning_amber_rounded,
                                      color: isSuccess
                                          ? (priorityTier == 1
                                              ? const Color(0xFF2E7D32)
                                              : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B)))
                                          : Colors.orange.shade900,
                                      size: 24,
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        isSuccess ? 'Your Fertilizer Recommendation' : 'Recommendation Status: $status',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                          color: isSuccess ? AppTheme.darkGreen : Colors.brown.shade900,
                                        ),
                                      ),
                                    ),
                                    if (isSuccess)
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: priorityTier == 1
                                              ? const Color(0xFF2E7D32)
                                              : (priorityTier == 2 ? const Color(0xFF1565C0) : const Color(0xFF00796B)),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Text(
                                          'Priority $priorityTier',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                if (isSuccess) ...[
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: Colors.white.withOpacity(0.8),
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: Colors.grey.shade300),
                                    ),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            const Icon(Icons.psychology_alt_rounded, size: 16, color: AppTheme.darkGreen),
                                            const SizedBox(width: 6),
                                            Text(
                                              'Why this recommendation?',
                                              style: TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 12,
                                                color: Colors.green.shade900,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          selectionReason,
                                          style: const TextStyle(fontSize: 11.5, color: AppTheme.textDark, height: 1.3),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'Rule: $ruleId • $rulePriority ($method)',
                                          style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          'Source: $recSource',
                                          style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                ],
                                Wrap(
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  spacing: 6,
                                  runSpacing: 2,
                                  children: [
                                    Text('Crop: ${widget.flowData['crop']}', style: const TextStyle(fontSize: 12, color: AppTheme.textDark, fontWeight: FontWeight.w600)),
                                    const Text('•', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                    Text(
                                      'Farm Area: $farmAreaOrig $farmAreaUnitOrig (${farmAreaHa.toStringAsFixed(2)} ha)',
                                      style: const TextStyle(fontSize: 12, color: AppTheme.textDark),
                                    ),
                                    const Text('•', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                    Text('District: ${widget.flowData['district'] ?? 'Thanjavur'}', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                                    if (widget.flowData['target_yield'] != null && priorityTier == 1) ...[
                                      const Text('•', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                      Text('Target Yield: ${widget.flowData['target_yield']} t/ha', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                                    ],
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Informative Error / Unavailable Rule Card (Safety First)
                        if (!isSuccess) ...[
                          Card(
                            color: const Color(0xFFFFF3E0),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
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
                                      Expanded(
                                        child: Text(
                                          status == 'INCOMPATIBLE_SOIL_TEST_METHOD'
                                              ? 'Incompatible Soil Test Method (Bray-1 P)'
                                              : (status == 'UNSUPPORTED_SOIL_SERIES'
                                                  ? 'Unsupported Soil Series'
                                                  : (status == 'NO_VERIFIED_RULE' || status == 'NO_VALIDATED_RECOMMENDATION'
                                                      ? 'No Validated Agricultural Rule Available'
                                                      : (status == 'MISSING_INPUTS'
                                                          ? 'Essential Soil Test Values Missing'
                                                          : 'Recommendation Status: $status'))),
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFFBF360C)),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  Text(
                                    _recommendationResponse?['actionable_message']?.toString() ??
                                        p5['actionable_message']?.toString() ??
                                        p5['message']?.toString() ??
                                        'No verified agricultural recommendation rule could be matched for the provided parameters. AgroWise AI strictly adheres to agricultural standards: fertilizer doses are never fabricated or estimated when validated rules or soil test values are absent.',
                                    style: const TextStyle(fontSize: 13, color: AppTheme.textDark, height: 1.4),
                                  ),
                                  if (p5['missing_inputs'] is List && (p5['missing_inputs'] as List).isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Text(
                                      'Missing parameters: ${(p5['missing_inputs'] as List).join(', ')}',
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFFD84315)),
                                    ),
                                  ],
                                  const SizedBox(height: 12),
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: Colors.orange.shade200),
                                    ),
                                    child: const Text(
                                      'Safety Notice: Applying an arbitrary or uncalibrated fertilizer dose may cause nutrient toxicity, salinity, groundwater contamination, or crop lodging. Please check your soil test report or consult your local Agricultural Extension Center (AEC).',
                                      style: TextStyle(fontSize: 11, color: Color(0xFFBF360C), fontStyle: FontStyle.italic, height: 1.3),
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: OutlinedButton.icon(
                                          onPressed: () => Navigator.pop(context),
                                          icon: const Icon(Icons.arrow_back_rounded),
                                          label: const Text('Back / Edit Inputs'),
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: FilledButton.icon(
                                          onPressed: () => Navigator.of(context).pushAndRemoveUntil(
                                            MaterialPageRoute(builder: (_) => const MainNavigationShell(initialIndex: 0)),
                                            (route) => false,
                                          ),
                                          style: FilledButton.styleFrom(backgroundColor: AppTheme.darkGreen),
                                          icon: const Icon(Icons.home_rounded),
                                          label: const Text('Home'),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ] else ...[
                          if (p5['card_comparison'] is Map && (p5['card_comparison'] as Map)['has_comparison'] == true) ...[
                            _buildCardComparisonSection(p5['card_comparison'] as Map<String, dynamic>, l10n),
                            const SizedBox(height: 14),
                          ],
                          _buildAgronomicBreakdownSection(p5, l10n),
                          const SizedBox(height: 14),

                          // Nutrient Requirement Cards
                          _nutrientCard(
                            name: 'Nitrogen Requirement (N)',
                            symbol: 'N',
                            perHa: netNHa,
                            perAcre: netNAcre,
                            total: totN,
                            primaryUnit: farmAreaUnitOrig,
                            color: const Color(0xFF1976D2),
                            range: rangeN,
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
                            range: rangeP,
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
                            range: rangeK,
                          ),
                          const SizedBox(height: 14),

                          // Sampling Note
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.blueGrey.shade50,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.blueGrey.shade200),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.info_outline_rounded, size: 16, color: Colors.blueGrey.shade700),
                                const SizedBox(width: 8),
                                const Expanded(
                                  child: Text(
                                    'Valid for this sample; sample several spots of the field for representative accuracy.',
                                    style: TextStyle(fontSize: 11, color: Colors.blueGrey),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 14),

                          // Secondary & Micronutrient Advisory
                          _buildMicronutrientSection(p5, l10n),
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

                        // Authoritative Reference Card
                        if (p5['authoritative_reference'] is Map || unifiedRec?['authoritative_reference'] is Map) ...[
                          Builder(
                            builder: (_) {
                              final auth = (unifiedRec?['authoritative_reference'] ?? p5['authoritative_reference']) as Map;
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

                        if (isSuccess) ...[
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
                            style: FilledButton.styleFrom(
                              backgroundColor: AppTheme.darkGreen,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            icon: const Icon(Icons.calculate_rounded),
                            label: Text(
                              l10n.text('optimal_plan_title'),
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                            ),
                          ),
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
