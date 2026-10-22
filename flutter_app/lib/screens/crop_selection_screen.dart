import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'npk_requirement_screen.dart';
import 'previous_fertilizer_screen.dart';

class CropSelectionScreen extends StatefulWidget {
  final Map<String, dynamic> farmDetails;
  final Map<String, dynamic>? soilProfile;

  const CropSelectionScreen({
    super.key,
    required this.farmDetails,
    this.soilProfile,
  });

  @override
  State<CropSelectionScreen> createState() => _CropSelectionScreenState();
}

class _CropSelectionScreenState extends State<CropSelectionScreen> {
  String _selectedCrop = 'Rice';
  String _selectedSeason = 'Kharif';
  final _targetYieldCtrl = TextEditingController(text: '6.0');
  String _previousCrop = 'None / Fallow';
  final _fymAppliedCtrl = TextEditingController(text: '0.0');
  final List<Map<String, dynamic>> _previousFertilizers = [];

  final List<String> _previousCropOptions = [
    'None / Fallow',
    'Blackgram',
    'Greengram',
    'Cowpea',
    'Groundnut',
    'Green Manure (Dhaincha/Sunnhemp)',
    'Rice',
    'Maize',
    'Cotton',
    'Sugarcane',
  ];

  final List<Map<String, dynamic>> _supportedCrops = [
    {
      'name': 'Rice',
      'local': 'நெல் (Paddy)',
      'icon': '🌾',
      'seasons': ['Kharif', 'Rabi', 'Samba', 'Kuruvai', 'Navarai'],
      'defaultYield': '6.0',
      'yieldUnit': 't/ha',
      'rule': 'TNAU STCR-IPNS Irrigated Rice (Cauvery Delta)',
    },
    {
      'name': 'Sugarcane',
      'local': 'கரும்பு',
      'icon': '🎋',
      'seasons': ['Annual', 'Special Season'],
      'defaultYield': '120.0',
      'yieldUnit': 't/ha',
      'rule': 'TNAU STCR Plant / Ratoon Cane Equations',
    },
    {
      'name': 'Cotton (lint)',
      'local': 'பருத்தி',
      'icon': '☁️',
      'seasons': ['Kharif', 'Winter'],
      'defaultYield': '2.5',
      'yieldUnit': 't/ha',
      'rule': 'TNAU STCR Cotton (MCU 5 / Black Soils)',
    },
    {
      'name': 'Maize',
      'local': 'மக்காச்சோளம்',
      'icon': '🌽',
      'seasons': ['Kharif', 'Rabi'],
      'defaultYield': '7.0',
      'yieldUnit': 't/ha',
      'rule': 'TNAU STCR Hybrid Maize Calibration',
    },
    {
      'name': 'Groundnut',
      'local': 'நிலக்கடலை',
      'icon': '🥜',
      'seasons': ['Kharif', 'Rabi'],
      'defaultYield': '2.5',
      'yieldUnit': 't/ha',
      'rule': 'TNAU Blanket Schedule (Pending Agronomic Validation)',
    },
  ];

  @override
  void initState() {
    super.initState();
    final recCrop = widget.soilProfile?['recommended_crop']?.toString() ??
        widget.soilProfile?['crop']?.toString() ??
        (widget.soilProfile?['printed_recommendation'] is Map
            ? (widget.soilProfile!['printed_recommendation'] as Map)['crop']?.toString()
            : null);
    if (recCrop != null) {
      final cLow = recCrop.toLowerCase();
      final match = _supportedCrops.firstWhere(
        (c) =>
            c['name'].toString().toLowerCase() == cLow ||
            (cLow.contains('groundnut') && c['name'] == 'Groundnut') ||
            (cLow.contains('peanut') && c['name'] == 'Groundnut') ||
            (cLow.contains('நிலக்கடலை') && c['name'] == 'Groundnut') ||
            (cLow.contains('rice') && c['name'] == 'Rice') ||
            (cLow.contains('paddy') && c['name'] == 'Rice') ||
            (cLow.contains('நெல்') && c['name'] == 'Rice') ||
            (cLow.contains('cane') && c['name'] == 'Sugarcane') ||
            (cLow.contains('கரும்பு') && c['name'] == 'Sugarcane'),
        orElse: () => _supportedCrops.first,
      );
      _selectedCrop = match['name'];
    }
    _updateYieldDefault();
    _syncHistoryFromStorage();
  }

  Future<void> _syncHistoryFromStorage() async {
    try {
      final list = await ApiClient.instance.getFertilizerHistory();
      if (list.isNotEmpty && mounted) {
        setState(() {
          for (final item in list) {
            final prod = item['fertilizer_product']?.toString() ?? item['product']?.toString() ?? '';
            final qty = (item['quantity'] is num)
                ? (item['quantity'] as num).toDouble()
                : (double.tryParse(item['quantity']?.toString() ?? '0') ?? 0.0);
            final unit = item['unit']?.toString() ?? 'kg';
            if (qty > 0) {
              if (prod.toLowerCase().contains('fym') || prod.toLowerCase().contains('manure')) {
                _fymAppliedCtrl.text = qty.toString();
              } else {
                final already = _previousFertilizers.any((f) => f['product'] == prod);
                if (!already) {
                  _previousFertilizers.add({
                    'product': prod,
                    'quantity': qty,
                    'unit': unit,
                    'months_ago': 2.0,
                  });
                }
              }
            }
          }
        });
      }
    } catch (_) {}
  }

  void _updateYieldDefault() {
    final c = _supportedCrops.firstWhere((x) => x['name'] == _selectedCrop, orElse: () => _supportedCrops.first);
    _targetYieldCtrl.text = c['defaultYield'];
    if (!(c['seasons'] as List).contains(_selectedSeason)) {
      _selectedSeason = (c['seasons'] as List).first;
    }
  }

  @override
  void dispose() {
    _targetYieldCtrl.dispose();
    _fymAppliedCtrl.dispose();
    super.dispose();
  }

  void _proceed() {
    final yVal = double.tryParse(_targetYieldCtrl.text.trim());
    if (yVal == null || yVal <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a valid target yield.')));
      return;
    }
    final fymVal = double.tryParse(_fymAppliedCtrl.text.trim()) ?? 0.0;

    final selectionData = {
      ...widget.farmDetails,
      'crop': _selectedCrop,
      'season': _selectedSeason,
      'target_yield': yVal,
      'previous_crop': _previousCrop,
      'fym_applied_t_per_ha': fymVal,
      'previous_fertilizers': _previousFertilizers,
    };

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => NpkRequirementScreen(
          flowData: selectionData,
          soilProfile: widget.soilProfile,
        ),
      ),
    );
  }

  Future<void> _showAddFertilizerDialog() async {
    String prod = 'DAP';
    final qtyCtrl = TextEditingController(text: '1.0');
    String unit = 'bags';
    final monthsCtrl = TextEditingController(text: '2.0');

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setD) => AlertDialog(
          title: const Text('Add Previous Fertilizer Record'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: prod,
                  decoration: const InputDecoration(labelText: 'Fertilizer Product'),
                  items: const [
                    DropdownMenuItem(value: 'DAP', child: Text('DAP (18-46-0)')),
                    DropdownMenuItem(value: 'Urea', child: Text('Urea (46-0-0)')),
                    DropdownMenuItem(value: 'MOP', child: Text('MOP / Potash (0-0-60)')),
                    DropdownMenuItem(value: 'SSP', child: Text('SSP (0-16-0)')),
                    DropdownMenuItem(value: 'Complex 20:20:0', child: Text('Complex 20:20:0')),
                    DropdownMenuItem(value: 'Complex 17:17:17', child: Text('Complex 17:17:17')),
                  ],
                  onChanged: (v) => setD(() => prod = v ?? 'DAP'),
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
                          DropdownMenuItem(value: 'bags', child: Text('Bags')),
                          DropdownMenuItem(value: 'kg', child: Text('kg')),
                          DropdownMenuItem(value: 'tonnes', child: Text('Tonnes')),
                        ],
                        onChanged: (v) => setD(() => unit = v ?? 'bags'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: monthsCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Months Ago',
                    helperText: 'Recent applications (≤6 mo) carry residual credit',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(
              onPressed: () {
                final q = double.tryParse(qtyCtrl.text.trim()) ?? 0.0;
                final m = double.tryParse(monthsCtrl.text.trim()) ?? 2.0;
                if (q > 0) {
                  setState(() {
                    _previousFertilizers.add({
                      'product': prod,
                      'quantity': q,
                      'unit': unit,
                      'months_ago': m,
                    });
                  });
                  Navigator.pop(ctx);
                }
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final activeCropInfo = _supportedCrops.firstWhere((x) => x['name'] == _selectedCrop);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('select_crop'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                l10n.text('select_crop'),
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              const Text(
                'Only crops with verified official TNAU STCR agronomic equations are listed.',
                style: TextStyle(fontSize: 13, color: AppTheme.textMuted),
              ),
              const SizedBox(height: 16),
              for (final c in _supportedCrops) ...[
                Card(
                  elevation: _selectedCrop == c['name'] ? 2.5 : 1,
                  color: _selectedCrop == c['name'] ? AppTheme.lightGreen : Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: BorderSide(
                      color: _selectedCrop == c['name'] ? AppTheme.primaryGreen : const Color(0xFFDCE6DB),
                      width: _selectedCrop == c['name'] ? 2 : 1,
                    ),
                  ),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    leading: Text(c['icon'], style: const TextStyle(fontSize: 26)),
                    title: Text('${c['name']} — ${c['local']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(c['rule'], style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                    trailing: _selectedCrop == c['name']
                        ? const Icon(Icons.check_circle_rounded, color: AppTheme.primaryGreen)
                        : const Icon(Icons.radio_button_off_rounded, color: Colors.grey),
                    onTap: () {
                      setState(() {
                        _selectedCrop = c['name'];
                        _updateYieldDefault();
                      });
                    },
                  ),
                ),
                const SizedBox(height: 8),
              ],
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Season & Target Yield', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: (activeCropInfo['seasons'] as List<String>).contains(_selectedSeason)
                            ? _selectedSeason
                            : (activeCropInfo['seasons'] as List<String>).first,
                        decoration: InputDecoration(labelText: l10n.text('season')),
                        items: (activeCropInfo['seasons'] as List<String>)
                            .toSet()
                            .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                            .toList(),
                        onChanged: (v) => setState(() => _selectedSeason = v!),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _targetYieldCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: '${l10n.text('target_yield')} (${activeCropInfo['yieldUnit']})',
                          helperText: 'Default: ${activeCropInfo['defaultYield']} ${activeCropInfo['yieldUnit']}',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Agronomic History Card (Previous Crop, FYM, Previous Fertilizer Records)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Agronomic History & Manure',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Biological N fixation from previous legumes and residual manure reduce your chemical fertilizer need.',
                        style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: _previousCrop,
                        decoration: InputDecoration(labelText: l10n.text('previous_crop')),
                        items: _previousCropOptions
                            .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                            .toList(),
                        onChanged: (v) => setState(() => _previousCrop = v ?? 'None / Fallow'),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _fymAppliedCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: l10n.text('fym_applied'),
                          helperText: 'Default: 0.0 tonnes/ha (zero deduction if none applied)',
                        ),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              l10n.text('previous_fertilizer'),
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                            ),
                          ),
                          TextButton.icon(
                            onPressed: _showAddFertilizerDialog,
                            icon: const Icon(Icons.add_circle_outline, size: 18),
                            label: Text(l10n.text('add_fertilizer_record')),
                          ),
                        ],
                      ),
                      if (_previousFertilizers.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          children: [
                            for (int i = 0; i < _previousFertilizers.length; i++)
                              Chip(
                                label: Text(
                                  '${_previousFertilizers[i]['product']}: ${_previousFertilizers[i]['quantity']} ${_previousFertilizers[i]['unit']} (${_previousFertilizers[i]['months_ago']} mo ago)',
                                  style: const TextStyle(fontSize: 12),
                                ),
                                deleteIcon: const Icon(Icons.close, size: 16),
                                onDeleted: () => setState(() => _previousFertilizers.removeAt(i)),
                              ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () async {
                  await Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PreviousFertilizerScreen(crop: _selectedCrop),
                    ),
                  );
                  _syncHistoryFromStorage();
                },
                icon: const Icon(Icons.history_rounded),
                label: Text(l10n.text('previous_fertilizer')),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _proceed,
                child: Text(l10n.text('continue_btn')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

