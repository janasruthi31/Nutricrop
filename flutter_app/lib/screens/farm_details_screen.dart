import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'crop_selection_screen.dart';

class FarmDetailsScreen extends StatefulWidget {
  final Map<String, dynamic>? initialSoilProfile;
  const FarmDetailsScreen({super.key, this.initialSoilProfile});

  @override
  State<FarmDetailsScreen> createState() => _FarmDetailsScreenState();
}

class _FarmDetailsScreenState extends State<FarmDetailsScreen> {
  final _villageCtrl = TextEditingController();
  final _areaCtrl = TextEditingController(text: '1.0');
  String _district = 'Thanjavur';
  String _areaUnit = 'acre';
  String _irrigation = 'Irrigated';
  String _soilSeries = 'Palavidhi';
  bool _isLoading = false;

  static const List<String> tnDistricts = [
    'Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Mayiladuthurai', 'Cuddalore',
    'Coimbatore', 'Tiruppur', 'Erode', 'Madurai', 'Dindigul', 'Salem', 'Trichy',
    'Ariyalur', 'Chengalpattu', 'Dharmapuri', 'Kallakurichi', 'Kancheepuram',
    'Kanniyakumari', 'Karur', 'Krishnagiri', 'Namakkal', 'Nilgiris', 'Perambalur',
    'Pudukkottai', 'Ramanathapuram', 'Ranipet', 'Sivaganga', 'Tenkasi', 'Theni',
    'Thoothukudi', 'Tiruchirappalli', 'Tirunelveli', 'Tirupathur', 'Tiruvallur',
    'Tiruvannamalai', 'Vellore', 'Viluppuram', 'Virudhunagar'
  ];

  static const List<String> soilSeriesList = [
    'Palavidhi', 'Adanur', 'Kalathur', 'Irugur', 'Pilamedu', 'General / Other'
  ];

  @override
  void initState() {
    super.initState();
    _loadExistingFarm();
  }

  Future<void> _loadExistingFarm() async {
    try {
      final f = await ApiClient.instance.getFarmDetails();
      if (f.isNotEmpty && mounted) {
        setState(() {
          if (f['district'] != null && tnDistricts.contains(f['district'])) {
            _district = f['district'];
          }
          if (f['village'] != null) _villageCtrl.text = f['village'];
          if (f['area'] != null) _areaCtrl.text = f['area'].toString();
          if (f['area_unit'] != null) _areaUnit = f['area_unit'];
          if (f['irrigation'] != null) _irrigation = f['irrigation'];
          if (f['soil_series'] != null && soilSeriesList.contains(f['soil_series'])) {
            _soilSeries = f['soil_series'];
          }
        });
      }
    } catch (_) {}
  }

  Future<void> _submit() async {
    final areaVal = double.tryParse(_areaCtrl.text.trim());
    if (areaVal == null || areaVal <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a valid farm area greater than 0.')));
      return;
    }

    setState(() => _isLoading = true);
    final farmData = {
      'district': _district,
      'village': _villageCtrl.text.trim(),
      'area': areaVal,
      'area_unit': _areaUnit,
      'irrigation': _irrigation,
      'soil_series': _soilSeries,
    };

    try {
      await ApiClient.instance.saveFarmDetails(farmData);
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CropSelectionScreen(
            farmDetails: farmData,
            soilProfile: widget.initialSoilProfile,
          ),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error saving farm: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('farm_details_title'))),
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
                          'Farm location & soil class determine verified TNAU STCR fertilizer equations.',
                          style: const TextStyle(fontSize: 13, color: AppTheme.darkGreen),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              DropdownButtonFormField<String>(
                value: _district,
                decoration: InputDecoration(
                  labelText: l10n.text('district'),
                  prefixIcon: const Icon(Icons.location_on_rounded),
                ),
                items: tnDistricts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) => setState(() => _district = v!),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _villageCtrl,
                decoration: InputDecoration(
                  labelText: l10n.text('village'),
                  prefixIcon: const Icon(Icons.home_work_rounded),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: TextField(
                      controller: _areaCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: InputDecoration(
                        labelText: l10n.text('farm_area'),
                        prefixIcon: const Icon(Icons.straighten_rounded),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: DropdownButtonFormField<String>(
                      value: _areaUnit,
                      decoration: InputDecoration(labelText: l10n.text('area_unit')),
                      items: const [
                        DropdownMenuItem(value: 'acre', child: Text('Acres')),
                        DropdownMenuItem(value: 'hectare', child: Text('Hectares')),
                      ],
                      onChanged: (v) => setState(() => _areaUnit = v!),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _irrigation,
                decoration: InputDecoration(
                  labelText: l10n.text('irrigation_method'),
                  prefixIcon: const Icon(Icons.water_drop_rounded),
                ),
                items: const [
                  DropdownMenuItem(value: 'Irrigated', child: Text('Irrigated (பாசனம்)')),
                  DropdownMenuItem(value: 'Rainfed', child: Text('Rainfed (மானாவாரி)')),
                ],
                onChanged: (v) => setState(() => _irrigation = v!),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _soilSeries,
                decoration: InputDecoration(
                  labelText: l10n.text('soil_series'),
                  prefixIcon: const Icon(Icons.layers_rounded),
                ),
                items: soilSeriesList.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                onChanged: (v) => setState(() => _soilSeries = v!),
              ),
              const SizedBox(height: 28),
              FilledButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(l10n.text('continue_btn')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
