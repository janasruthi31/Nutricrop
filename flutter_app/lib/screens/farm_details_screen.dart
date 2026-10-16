import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
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
  double? _latitude;
  double? _longitude;
  String? _taluk;

  bool _isLoading = false;
  bool _isDetectingLocation = false;
  String? _locationStatusMessage;

  static const List<String> tnDistricts = [
    'Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Mayiladuthurai', 'Cuddalore',
    'Coimbatore', 'Tiruppur', 'Erode', 'Madurai', 'Dindigul', 'Salem', 'Trichy',
    'Ariyalur', 'Chengalpattu', 'Dharmapuri', 'Kallakurichi', 'Kancheepuram',
    'Kanniyakumari', 'Karur', 'Krishnagiri', 'Namakkal', 'Nilgiris', 'Perambalur',
    'Pudukkottai', 'Ramanathapuram', 'Ranipet', 'Sivaganga', 'Tenkasi', 'Theni',
    'Thoothukudi', 'Tiruchirappalli', 'Tirunelveli', 'Tirupathur', 'Tiruvallur',
    'Tiruvannamalai', 'Vellore', 'Viluppuram', 'Virudhunagar', 'Chennai'
  ];

  static const List<String> soilSeriesList = [
    'Palavidhi', 'Adanur', 'Kalathur', 'Irugur', 'Pilamedu', 'Coimbatore', 'General / Other'
  ];

  @override
  void initState() {
    super.initState();
    _loadExistingFarm();
  }

  Future<void> _loadExistingFarm() async {
    // 1. Initialize from soil report if passed
    if (widget.initialSoilProfile != null) {
      final p = widget.initialSoilProfile!;
      final d = p['district']?.toString();
      final v = p['village']?.toString();
      if (d != null && tnDistricts.contains(d)) {
        setState(() => _district = d);
      }
      if (v != null && v.isNotEmpty) {
        setState(() => _villageCtrl.text = v);
      }
    }

    // 2. Load stored farm details if any
    try {
      final f = await ApiClient.instance.getFarmDetails();
      if (f.isNotEmpty && mounted) {
        setState(() {
          if (widget.initialSoilProfile == null && f['district'] != null && tnDistricts.contains(f['district'])) {
            _district = f['district'];
          }
          if (widget.initialSoilProfile == null && f['village'] != null && f['village'].toString().isNotEmpty) {
            _villageCtrl.text = f['village'];
          }
          if (f['latitude'] != null) _latitude = (f['latitude'] as num).toDouble();
          if (f['longitude'] != null) _longitude = (f['longitude'] as num).toDouble();
          if (f['taluk'] != null) _taluk = f['taluk'].toString();
          if (f['area_unit'] != null) {
            final u = f['area_unit'].toString().toLowerCase();
            _areaUnit = (u.startsWith('hect') || u == 'ha') ? 'hectare' : 'acre';
          }
          if (f['irrigation'] != null) {
            final ir = f['irrigation'].toString().toLowerCase();
            _irrigation = ir == 'rainfed' ? 'Rainfed' : 'Irrigated';
          }
          if (f['soil_series'] != null && soilSeriesList.contains(f['soil_series'])) {
            _soilSeries = f['soil_series'];
          }
        });
      }
    } catch (_) {}
  }

  Future<void> _detectLocation() async {
    setState(() {
      _isDetectingLocation = true;
      _locationStatusMessage = 'Checking device location permissions...';
    });

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _locationStatusMessage = 'Location services disabled. Please enable GPS or select district manually.';
          _isDetectingLocation = false;
        });
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _locationStatusMessage = 'Location permissions denied. Please choose your district manually.';
            _isDetectingLocation = false;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _locationStatusMessage = 'Location permissions permanently denied in browser/device settings.';
          _isDetectingLocation = false;
        });
        return;
      }

      setState(() => _locationStatusMessage = 'Acquiring GPS fix from device...');
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 15),
      );

      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
        _locationStatusMessage = 'Resolving Tamil Nadu administrative district...';
      });

      // Call reverse geocoding API on backend
      final geo = await ApiClient.instance.reverseGeocode(lat: position.latitude, lon: position.longitude);
      final dist = geo['district']?.toString();
      final vil = geo['village']?.toString();
      final tal = geo['taluk']?.toString();

      setState(() {
        if (dist != null && tnDistricts.contains(dist)) {
          _district = dist;
        }
        if (vil != null && vil.isNotEmpty && _villageCtrl.text.isEmpty) {
          _villageCtrl.text = vil;
        }
        if (tal != null) _taluk = tal;
        _locationStatusMessage = 'GPS fixed: ${_latitude!.toStringAsFixed(4)}°N, ${_longitude!.toStringAsFixed(4)}°E ($dist)';
      });
    } catch (e) {
      setState(() {
        _locationStatusMessage = 'GPS unavailable ($e). Please select district manually.';
      });
    } finally {
      if (mounted) setState(() => _isDetectingLocation = false);
    }
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
      'taluk': _taluk,
      'latitude': _latitude,
      'longitude': _longitude,
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
                          l10n.text('farm_details_desc'),
                          style: const TextStyle(fontSize: 13, color: AppTheme.darkGreen, height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // GPS Detection Card
              Card(
                elevation: 1.5,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.green.shade200)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.my_location_rounded, color: AppTheme.primaryGreen),
                          const SizedBox(width: 10),
                          const Text(
                            'Farm Location (GPS Detection)',
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textDark),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Retrieve device GPS coordinates and reverse-geocode into Tamil Nadu district and village.',
                        style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 12,
                        runSpacing: 8,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(160, 42),
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            ),
                            onPressed: _isDetectingLocation ? null : _detectLocation,
                            icon: _isDetectingLocation
                                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryGreen))
                                : const Icon(Icons.gps_fixed_rounded, size: 18),
                            label: Text(_isDetectingLocation ? 'Detecting...' : 'Detect My Location'),
                          ),
                          if (_latitude != null && _longitude != null)
                            Text(
                              '${_latitude!.toStringAsFixed(4)}°N, ${_longitude!.toStringAsFixed(4)}°E',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.primaryGreen),
                            ),
                        ],
                      ),
                      if (_locationStatusMessage != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          _locationStatusMessage!,
                          style: TextStyle(fontSize: 12, color: _latitude != null ? Colors.green.shade800 : Colors.orange.shade800, fontStyle: FontStyle.italic),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // District
              Text(
                l10n.text('district'),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: tnDistricts.contains(_district) ? _district : 'Thanjavur',
                decoration: const InputDecoration(prefixIcon: Icon(Icons.location_city_rounded)),
                items: tnDistricts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) => setState(() => _district = v ?? 'Thanjavur'),
              ),
              const SizedBox(height: 16),

              // Village
              Text(
                l10n.text('village'),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              TextField(
                controller: _villageCtrl,
                decoration: InputDecoration(
                  hintText: l10n.text('village_hint'),
                  prefixIcon: const Icon(Icons.home_work_outlined),
                ),
              ),
              const SizedBox(height: 16),

              // Farm Area & Unit
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 3,
                    child: TextField(
                      controller: _areaCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: InputDecoration(
                        labelText: l10n.text('farm_area'),
                        prefixIcon: const Icon(Icons.square_foot_rounded),
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    flex: 2,
                    child: DropdownButtonFormField<String>(
                      value: (_areaUnit.toLowerCase().startsWith('hect') || _areaUnit.toLowerCase() == 'ha') ? 'hectare' : 'acre',
                      decoration: InputDecoration(
                        labelText: l10n.text('unit'),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'acre', child: Text('Acre')),
                        DropdownMenuItem(value: 'hectare', child: Text('Hectare')),
                      ],
                      onChanged: (v) => setState(() => _areaUnit = v ?? 'acre'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Irrigation Method
              Text(
                l10n.text('irrigation'),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: (_irrigation.toLowerCase() == 'rainfed') ? 'Rainfed' : 'Irrigated',
                decoration: const InputDecoration(prefixIcon: Icon(Icons.water_drop_outlined)),
                items: const [
                  DropdownMenuItem(value: 'Irrigated', child: Text('Irrigated (பாசனம்)')),
                  DropdownMenuItem(value: 'Rainfed', child: Text('Rainfed (மானாவாரி)')),
                ],
                onChanged: (v) => setState(() => _irrigation = v ?? 'Irrigated'),
              ),
              const SizedBox(height: 16),

              // Soil Series
              Text(
                l10n.text('soil_type'),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: soilSeriesList.contains(_soilSeries) ? _soilSeries : 'General / Other',
                decoration: const InputDecoration(prefixIcon: Icon(Icons.landscape_outlined)),
                items: soilSeriesList.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                onChanged: (v) => setState(() => _soilSeries = v ?? 'General / Other'),
              ),
              const SizedBox(height: 28),

              FilledButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text(l10n.text('continue_to_crops')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
