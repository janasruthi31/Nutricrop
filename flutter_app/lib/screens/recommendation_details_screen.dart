import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'report_generation_screen.dart';

class RecommendationDetailsScreen extends StatefulWidget {
  final String recommendationId;
  const RecommendationDetailsScreen({super.key, required this.recommendationId});

  @override
  State<RecommendationDetailsScreen> createState() => _RecommendationDetailsScreenState();
}

class _RecommendationDetailsScreenState extends State<RecommendationDetailsScreen> {
  Map<String, dynamic>? _record;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiClient.instance.getRecommendationDetails(widget.recommendationId);
      setState(() {
        _record = res;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = 'Could not load details for ${widget.recommendationId}.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Recommendation Details')),
        body: const LoadingView(message: 'Loading saved recommendation audit record...'),
      );
    }

    if (_error != null || _record == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Recommendation Details')),
        body: ErrorStateView(message: _error ?? 'Record not found.', onRetry: _load),
      );
    }

    final rawJson = _record!['response_json'] as Map<String, dynamic>? ?? {};
    final crop = _record!['crop'] ?? 'Crop';
    final district = _record!['district'] ?? 'District';
    final area = _record!['farm_area'] ?? 1.0;
    final cost = _record!['total_cost_inr'] ?? 0.0;
    final created = _record!['created_at'] ?? '';

    final p5 = rawJson['nutrient_requirements'] as Map? ?? {};
    final p6 = rawJson['fertilizer_plan'] as Map? ?? {};
    final products = (p6['recommended_products'] as List? ?? []);

    return Scaffold(
      appBar: AppBar(title: Text('$crop Recommendation Details')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                color: AppTheme.darkGreen,
                child: Padding(
                  padding: const EdgeInsets.all(18.0),
                  child: Column(
                    children: [
                      Text('Saved ID: ${widget.recommendationId}', style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 12)),
                      const SizedBox(height: 6),
                      Text('₹${cost.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white, fontSize: 30, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text('$crop • $district • $area ha • $created', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              const SectionHeader(title: 'Calculated NPK Quantities', subtitle: 'Target yield STCR baseline'),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Nitrogen (N):', style: TextStyle(fontWeight: FontWeight.w600)),
                          Text('${p5['n_req_kg_per_ha'] ?? p5['net_n_kg_per_ha'] ?? 'N/A'} kg/ha'),
                        ],
                      ),
                      const Divider(height: 18),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Phosphorus (P₂O₅):', style: TextStyle(fontWeight: FontWeight.w600)),
                          Text('${p5['p2o5_req_kg_per_ha'] ?? p5['net_p2o5_kg_per_ha'] ?? 'N/A'} kg/ha'),
                        ],
                      ),
                      const Divider(height: 18),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Potassium (K₂O):', style: TextStyle(fontWeight: FontWeight.w600)),
                          Text('${p5['k2o_req_kg_per_ha'] ?? p5['net_k2o_kg_per_ha'] ?? 'N/A'} kg/ha'),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              const SectionHeader(title: 'Purchased Fertilizer Products', subtitle: 'Selected by Linear Programming cost solver'),
              for (final prod in products) ...[
                FertilizerProductCard(
                  name: prod['product_name'] ?? prod['name'] ?? 'Fertilizer',
                  quantityKg: (prod['quantity_kg'] as num?)?.toDouble() ?? 0.0,
                  bags: (prod['bags'] as num?)?.toInt() ?? 0,
                  bagSizeKg: (prod['bag_size_kg'] as num?)?.toDouble() ?? 50.0,
                  totalCostInr: (prod['total_cost_inr'] as num?)?.toDouble() ?? 0.0,
                ),
                const SizedBox(height: 6),
              ],
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ReportGenerationScreen(
                        recommendationData: rawJson,
                        savedId: widget.recommendationId,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.picture_as_pdf_rounded),
                label: const Text('Download Official PDF Report'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
