import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import 'recommendation_details_screen.dart';

class RecommendationHistoryScreen extends StatefulWidget {
  const RecommendationHistoryScreen({super.key});

  @override
  State<RecommendationHistoryScreen> createState() => _RecommendationHistoryScreenState();
}

class _RecommendationHistoryScreenState extends State<RecommendationHistoryScreen> {
  List<dynamic> _list = [];
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
      final res = await ApiClient.instance.listRecommendations();
      setState(() {
        _list = res;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = 'Failed to load recommendation history.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.text('history')),
        actions: [
          IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _load),
        ],
      ),
      body: SafeArea(
        child: _isLoading
            ? const LoadingView(message: 'Loading your saved recommendations...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _load)
                : _list.isEmpty
                    ? EmptyStateView(
                        icon: Icons.history_rounded,
                        title: 'No Recommendations Saved Yet',
                        subtitle: 'Run a fertilizer recommendation and tap "Save Recommendation" to view them here.',
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16.0),
                        itemCount: _list.length,
                        itemBuilder: (ctx, i) {
                          final item = _list[i];
                          final id = item['recommendation_id'] ?? '';
                          final crop = item['crop'] ?? 'Crop';
                          final district = item['district'] ?? 'District';
                          final area = item['farm_area'] ?? 1.0;
                          final unit = item['farm_area_unit'] ?? 'ha';
                          final cost = (item['total_cost_inr'] as num?)?.toDouble() ?? 0.0;
                          final date = (item['created_at']?.toString() ?? '').split('T').first;

                          return Card(
                            child: ListTile(
                              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              leading: Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: AppTheme.lightGreen,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen),
                              ),
                              title: Text('$crop — $district', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const SizedBox(height: 2),
                                  Text('Area: $area $unit • Date: $date', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                  const SizedBox(height: 2),
                                  Text('Est. Cost: ₹${cost.toStringAsFixed(0)}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryGreen)),
                                ],
                              ),
                              trailing: const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => RecommendationDetailsScreen(recommendationId: id),
                                  ),
                                );
                              },
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
