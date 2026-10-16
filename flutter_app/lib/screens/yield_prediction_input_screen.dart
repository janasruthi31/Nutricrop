import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'yield_prediction_result_screen.dart';

class YieldPredictionInputScreen extends StatefulWidget {
  const YieldPredictionInputScreen({super.key});

  @override
  State<YieldPredictionInputScreen> createState() => _YieldPredictionInputScreenState();
}

class _YieldPredictionInputScreenState extends State<YieldPredictionInputScreen> {
  String _district = 'Thanjavur';
  String _crop = 'Rice';
  String _season = 'Samba/Thaladi/Pishanam';
  final int _year = 2024;

  final _swmCtrl = TextEditingController(text: '330.0');
  final _nemCtrl = TextEditingController(text: '640.0');
  final _winterCtrl = TextEditingController(text: '40.0');
  final _hotCtrl = TextEditingController(text: '150.0');
  final _annualCtrl = TextEditingController(text: '1160.0');

  bool _isLoading = false;
  String? _error;

  List<String> _districts = ['Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Madurai', 'Coimbatore'];
  List<String> _crops = ['Rice', 'Sugarcane', 'Cotton', 'Maize', 'Groundnut'];
  List<String> _seasons = ['Samba/Thaladi/Pishanam', 'Kharif', 'Rabi', 'Kuruvai', 'Annual'];
  Map<String, dynamic> _districtNormals = {};

  @override
  void initState() {
    super.initState();
    _loadMeta();
  }

  Future<void> _loadMeta() async {
    try {
      final meta = await ApiClient.instance.getYieldMeta();
      if (mounted) {
        setState(() {
          if (meta['districts'] != null) _districts = (meta['districts'] as List).cast<String>();
          if (meta['crops'] != null) _crops = (meta['crops'] as List).cast<String>();
          if (meta['seasons'] != null) _seasons = (meta['seasons'] as List).cast<String>();
          if (meta['district_rainfall_normals'] != null) {
            _districtNormals = (meta['district_rainfall_normals'] as Map).cast<String, dynamic>();
          }
          if (!_districts.contains(_district)) _district = _districts.first;
          if (!_crops.contains(_crop)) _crop = _crops.first;
          if (!_seasons.contains(_season)) _season = _seasons.first;
          _applyDistrictNormals(_district);
        });
      }
    } catch (_) {}
  }

  void _applyDistrictNormals(String district) {
    final normal = _districtNormals[district] as Map?;
    if (normal != null) {
      if (normal['rain_swm'] != null) _swmCtrl.text = normal['rain_swm'].toString();
      if (normal['rain_nem'] != null) _nemCtrl.text = normal['rain_nem'].toString();
      if (normal['rain_winter'] != null) _winterCtrl.text = normal['rain_winter'].toString();
      if (normal['rain_hot'] != null) _hotCtrl.text = normal['rain_hot'].toString();
      if (normal['rain_annual'] != null) _annualCtrl.text = normal['rain_annual'].toString();
    }
  }

  void _recalcAnnual() {
    final swm = double.tryParse(_swmCtrl.text) ?? 0;
    final nem = double.tryParse(_nemCtrl.text) ?? 0;
    final w = double.tryParse(_winterCtrl.text) ?? 0;
    final h = double.tryParse(_hotCtrl.text) ?? 0;
    _annualCtrl.text = (swm + nem + w + h).toStringAsFixed(1);
  }

  Future<void> _submit() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final res = await ApiClient.instance.predictYield(
        district: _district,
        crop: _crop,
        season: _season,
        year: _year,
        rainSwm: double.tryParse(_swmCtrl.text) ?? 330.0,
        rainNem: double.tryParse(_nemCtrl.text) ?? 640.0,
        rainWinter: double.tryParse(_winterCtrl.text) ?? 40.0,
        rainHot: double.tryParse(_hotCtrl.text) ?? 150.0,
        rainAnnual: double.tryParse(_annualCtrl.text) ?? 1160.0,
      );

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => YieldPredictionResultScreen(result: res),
        ),
      );
    } catch (e) {
      setState(() => _error = 'Prediction failed: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('predict_yield'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                color: AppTheme.lightGreen,
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline_rounded, color: AppTheme.primaryGreen),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          l10n.text('yield_disclaimer'),
                          style: const TextStyle(fontSize: 12.5, color: AppTheme.darkGreen),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              if (_error != null) ...[
                Text(_error!, style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
              ],
              DropdownButtonFormField<String>(
                value: _districts.contains(_district) ? _district : (_districts.isNotEmpty ? _districts.first : 'Thanjavur'),
                decoration: InputDecoration(
                  labelText: l10n.text('district'),
                  prefixIcon: const Icon(Icons.location_on_outlined),
                ),
                items: _districts.toSet().map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) {
                  if (v != null) {
                    setState(() {
                      _district = v;
                      _applyDistrictNormals(v);
                    });
                  }
                },
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                value: _crops.contains(_crop) ? _crop : (_crops.isNotEmpty ? _crops.first : 'Rice'),
                decoration: InputDecoration(
                  labelText: l10n.text('select_crop'),
                  prefixIcon: const Icon(Icons.eco_outlined),
                ),
                items: _crops.toSet().map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setState(() => _crop = v!),
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                value: _seasons.contains(_season) ? _season : (_seasons.isNotEmpty ? _seasons.first : 'Samba/Thaladi/Pishanam'),
                decoration: InputDecoration(
                  labelText: l10n.text('season'),
                  prefixIcon: const Icon(Icons.calendar_today_outlined),
                ),
                items: _seasons.toSet().map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                onChanged: (v) => setState(() => _season = v!),
              ),
              const SizedBox(height: 18),
              Text(
                'Seasonal Rainfall Normals for $_district (mm)',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textDark),
              ),
              const SizedBox(height: 4),
              const Text(
                'Auto-loaded from official Tamil Nadu Season & Crop Reports (2020-2025). Edit as needed for local variance.',
                style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _swmCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      onChanged: (_) => _recalcAnnual(),
                      decoration: const InputDecoration(labelText: 'SW Monsoon (mm)', helperText: 'Jun-Sep'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _nemCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      onChanged: (_) => _recalcAnnual(),
                      decoration: const InputDecoration(labelText: 'NE Monsoon (mm)', helperText: 'Oct-Dec'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _winterCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      onChanged: (_) => _recalcAnnual(),
                      decoration: const InputDecoration(labelText: 'Winter (mm)', helperText: 'Jan-Feb'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _hotCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      onChanged: (_) => _recalcAnnual(),
                      decoration: const InputDecoration(labelText: 'Hot Weather (mm)', helperText: 'Mar-May'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _annualCtrl,
                readOnly: true,
                decoration: const InputDecoration(
                  labelText: 'Annual Rainfall Total (mm)',
                  prefixIcon: Icon(Icons.water_drop_outlined),
                ),
              ),
              const SizedBox(height: 26),
              FilledButton.icon(
                onPressed: _isLoading ? null : _submit,
                icon: const Icon(Icons.online_prediction_rounded),
                label: _isLoading
                    ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(l10n.text('predict_yield')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
