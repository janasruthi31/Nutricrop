import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
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
      'rule': 'TNAU STCR Irrigated Groundnut Calibration',
    },
  ];

  @override
  void initState() {
    super.initState();
    _updateYieldDefault();
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
    super.dispose();
  }

  void _proceed() {
    final yVal = double.tryParse(_targetYieldCtrl.text.trim());
    if (yVal == null || yVal <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a valid target yield.')));
      return;
    }

    final selectionData = {
      ...widget.farmDetails,
      'crop': _selectedCrop,
      'season': _selectedSeason,
      'target_yield': yVal,
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
                      Text('Season & Target Yield', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
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
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PreviousFertilizerScreen(crop: _selectedCrop),
                    ),
                  );
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
