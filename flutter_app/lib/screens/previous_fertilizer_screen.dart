import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class PreviousFertilizerScreen extends StatefulWidget {
  final String crop;
  const PreviousFertilizerScreen({super.key, required this.crop});

  @override
  State<PreviousFertilizerScreen> createState() => _PreviousFertilizerScreenState();
}

class _PreviousFertilizerScreenState extends State<PreviousFertilizerScreen> {
  List<dynamic> _history = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiClient.instance.getFertilizerHistory();
      setState(() {
        _history = list.where((item) => item['crop'] == widget.crop || widget.crop.isEmpty).toList();
        _error = null;
      });
    } catch (e) {
      setState(() => _error = 'Could not load fertilizer records.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _showAddDialog() async {
    final prodCtrl = TextEditingController(text: 'Farmyard Manure (FYM)');
    final qtyCtrl = TextEditingController(text: '5.0');
    String unit = 'tonnes';
    String stage = 'Basal';

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setD) => AlertDialog(
          title: const Text('Add Previous Fertilizer'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: prodCtrl,
                  decoration: const InputDecoration(labelText: 'Fertilizer / Organic Manure'),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: qtyCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Quantity'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: unit,
                        items: const [
                          DropdownMenuItem(value: 'tonnes', child: Text('Tonnes')),
                          DropdownMenuItem(value: 'kg', child: Text('kg')),
                          DropdownMenuItem(value: 'bags', child: Text('Bags')),
                        ],
                        onChanged: (v) => setD(() => unit = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: stage,
                  decoration: const InputDecoration(labelText: 'Application Timing'),
                  items: const [
                    DropdownMenuItem(value: 'Basal', child: Text('Basal (Before Sowing)')),
                    DropdownMenuItem(value: 'Top Dress', child: Text('Top Dressing')),
                    DropdownMenuItem(value: 'Previous Season', child: Text('Previous Season Residual')),
                  ],
                  onChanged: (v) => setD(() => stage = v!),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final q = double.tryParse(qtyCtrl.text.trim()) ?? 0;
                if (q > 0) {
                  await ApiClient.instance.addFertilizerHistory({
                    'crop': widget.crop,
                    'fertilizer_product': prodCtrl.text.trim(),
                    'quantity': q,
                    'unit': unit,
                    'application_date': DateTime.now().toString().substring(0, 10),
                    'notes': stage,
                  });
                  if (mounted) Navigator.pop(ctx);
                  _loadHistory();
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text('${l10n.text('previous_fertilizer')} (${widget.crop})')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddDialog,
        backgroundColor: AppTheme.primaryGreen,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('Add Entry', style: TextStyle(color: Colors.white)),
      ),
      body: SafeArea(
        child: _isLoading
            ? const LoadingView(message: 'Loading fertilizer history...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _loadHistory)
                : _history.isEmpty
                    ? EmptyStateView(
                        icon: Icons.history_edu_rounded,
                        title: 'No Fertilizer History Recorded',
                        subtitle: 'Recording organic manure (FYM) or previous fertilizers helps calculate Integrated Plant Nutrition (IPNS) balance.',
                        buttonLabel: 'Add First Record',
                        onAction: _showAddDialog,
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _history.length,
                        itemBuilder: (ctx, i) {
                          final item = _history[i];
                          return Card(
                            child: ListTile(
                              leading: const CircleAvatar(
                                backgroundColor: AppTheme.lightGreen,
                                child: Icon(Icons.compost_rounded, color: AppTheme.primaryGreen),
                              ),
                              title: Text(item['fertilizer_product'] ?? 'Fertilizer', style: const TextStyle(fontWeight: FontWeight.bold)),
                              subtitle: Text('${item['quantity']} ${item['unit']} • ${item['notes'] ?? 'Application'} (${item['application_date'] ?? 'Recent'})'),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                                onPressed: () async {
                                  await ApiClient.instance.deleteFertilizerHistory(item['id']);
                                  _loadHistory();
                                },
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
