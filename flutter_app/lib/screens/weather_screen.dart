import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class WeatherScreen extends StatefulWidget {
  final String? initialDistrict;
  final double? initialLat;
  final double? initialLon;

  const WeatherScreen({
    super.key,
    this.initialDistrict,
    this.initialLat,
    this.initialLon,
  });

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  String _selectedDistrict = 'Thanjavur';
  double? _lat;
  double? _lon;
  Map<String, dynamic>? _weather;
  bool _isLoading = true;
  String? _error;

  static const List<String> districts = [
    'Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Mayiladuthurai', 'Cuddalore',
    'Coimbatore', 'Tiruppur', 'Erode', 'Salem', 'Namakkal', 'Dharmapuri',
    'Krishnagiri', 'Tiruchirappalli', 'Karur', 'Perambalur', 'Ariyalur',
    'Pudukkottai', 'Madurai', 'Dindigul', 'Theni', 'Virudhunagar', 'Sivaganga',
    'Ramanathapuram', 'Tirunelveli', 'Tenkasi', 'Thoothukudi', 'Kanniyakumari',
    'Nilgiris', 'Vellore', 'Ranipet', 'Tirupathur', 'Tiruvannamalai', 'Viluppuram',
    'Kallakurichi', 'Kancheepuram', 'Chengalpattu', 'Tiruvallur', 'Chennai'
  ];

  @override
  void initState() {
    super.initState();
    _lat = widget.initialLat;
    _lon = widget.initialLon;
    if (widget.initialDistrict != null && districts.contains(widget.initialDistrict)) {
      _selectedDistrict = widget.initialDistrict!;
    }
    _loadWeather();
  }

  Future<void> _loadWeather() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final res = await ApiClient.instance.getWeatherGuidance(
        _selectedDistrict,
        _lat,
        _lon,
      );
      if (res['status'] == 'WEATHER_UNAVAILABLE') {
        setState(() {
          _error = res['advisory_en'] ?? 'Live weather service unreachable.';
          _weather = res;
        });
      } else {
        setState(() {
          _weather = res;
          if (res['latitude'] != null) _lat = (res['latitude'] as num).toDouble();
          if (res['longitude'] != null) _lon = (res['longitude'] as num).toDouble();
        });
      }
    } catch (e) {
      setState(() => _error = 'Could not reach weather service. Soil recommendations remain active.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final risk = _weather?['risk_level'] ?? 'LOW';
    final lang = globalLocaleNotifier.locale.languageCode;

    String advice = 'Weather suitable for fertilizer application and field operations.';
    if (lang == 'ta' && _weather?['advisory_ta'] != null) {
      advice = _weather!['advisory_ta'].toString();
    } else if (_weather?['actionable_advice'] != null) {
      advice = _weather!['actionable_advice'].toString();
    } else if (_weather?['advisory_en'] != null) {
      advice = _weather!['advisory_en'].toString();
    }

    final condition = (lang == 'ta' && _weather?['condition_ta'] != null)
        ? _weather!['condition_ta'].toString()
        : (_weather?['current_condition'] ?? _weather?['condition'] ?? 'Clear');

    final tempVal = _weather?['temperature_c'] ?? _weather?['temp_max_c'];
    final tempStr = (tempVal is num) ? '${tempVal.toDouble().toStringAsFixed(1)}°C' : '--';
    final humidityStr = _weather?['humidity_pct'] != null ? '${_weather!['humidity_pct']}%' : '--';
    final rainMmStr = _weather?['rainfall_mm_24h'] != null ? '${(_weather!['rainfall_mm_24h'] as num).toDouble().toStringAsFixed(1)} mm' : '--';
    final windStr = _weather?['wind_speed_kmh'] != null ? '${(_weather!['wind_speed_kmh'] as num).toDouble().toStringAsFixed(1)} km/h' : '--';
    final isCached = _weather?['is_cached'] == true;
    final dataSource = _weather?['data_source'] ?? 'Open-Meteo';
    final obsTime = _weather?['observation_time'] ?? '';
    final forecastDays = (_weather?['forecast_days'] as List? ?? []);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('weather_title'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // District selection & GPS badge
              Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on_rounded, color: AppTheme.primaryGreen),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DropdownButton<String>(
                          value: districts.contains(_selectedDistrict) ? _selectedDistrict : 'Thanjavur',
                          isExpanded: true,
                          underline: const SizedBox(),
                          items: districts.map((d) => DropdownMenuItem(value: d, child: Text('$d District'))).toList(),
                          onChanged: (v) {
                            if (v != null) {
                              setState(() {
                                _selectedDistrict = v;
                                _lat = null;
                                _lon = null;
                              });
                              _loadWeather();
                            }
                          },
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.refresh_rounded),
                        tooltip: 'Refresh Weather',
                        onPressed: _loadWeather,
                      ),
                    ],
                  ),
                ),
              ),

              if (_lat != null && _lon != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4.0, vertical: 4.0),
                  child: Row(
                    children: [
                      Icon(Icons.gps_fixed_rounded, size: 14, color: Colors.grey.shade600),
                      const SizedBox(width: 6),
                      Text(
                        'Farm GPS: ${_lat!.toStringAsFixed(4)}°N, ${_lon!.toStringAsFixed(4)}°E',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: isCached ? Colors.orange.shade100 : Colors.green.shade100,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          isCached ? 'Cached' : 'Live Open-Meteo',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isCached ? Colors.orange.shade900 : Colors.green.shade900),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 10),

              if (_isLoading)
                const LoadingView(message: 'Retrieving live Open-Meteo agro-weather...')
              else if (_error != null && _weather == null)
                Card(
                  color: const Color(0xFFFFF3E0),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.cloud_off_rounded, color: Color(0xFFE65100)),
                            SizedBox(width: 8),
                            Text('Weather Service Offline', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFE65100))),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(_error!, style: const TextStyle(color: Color(0xFFE65100), fontSize: 13)),
                        const SizedBox(height: 10),
                        FilledButton.tonal(onPressed: _loadWeather, child: const Text('Retry')),
                      ],
                    ),
                  ),
                )
              else ...[
                // Main Weather Display Card
                Card(
                  color: AppTheme.darkGreen,
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '$_selectedDistrict, Tamil Nadu',
                                  style: const TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  condition,
                                  style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 14),
                                ),
                              ],
                            ),
                            const Icon(Icons.cloud_queue_rounded, color: Color(0xFFFFD54F), size: 44),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              tempStr,
                              style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.bold),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: risk == 'HIGH'
                                    ? Colors.red
                                    : (risk == 'MEDIUM' ? Colors.orange : Colors.green.shade700),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                'Rain Risk: $risk',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                            )
                          ],
                        ),
                        const SizedBox(height: 14),
                        const Divider(color: Colors.white24),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('Humidity: $humidityStr', style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 12.5)),
                            Text('24h Rain: $rainMmStr', style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 12.5)),
                            Text('Wind: $windStr', style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 12.5)),
                          ],
                        ),
                        if (obsTime.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Observed: $obsTime via $dataSource',
                            style: const TextStyle(color: Color(0xFFA5D6A7), fontSize: 11),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Fertilizer Scheduling Advisory
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.notifications_active_rounded, color: AppTheme.primaryGreen),
                            const SizedBox(width: 10),
                            Text(
                              l10n.text('weather_advice'),
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textDark),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          advice,
                          style: const TextStyle(fontSize: 14, color: AppTheme.textDark, height: 1.45),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // 7-Day Forecast Section
                if (forecastDays.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 4.0),
                    child: Text(
                      '7-Day Farm Weather Forecast',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textDark),
                    ),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 125,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: forecastDays.length,
                      itemBuilder: (ctx, idx) {
                        final d = forecastDays[idx];
                        final date = d['date']?.toString().split('-').skip(1).join('/') ?? '';
                        final maxT = d['temp_max_c'] != null ? '${(d['temp_max_c'] as num).round()}°' : '--';
                        final minT = d['temp_min_c'] != null ? '${(d['temp_min_c'] as num).round()}°' : '--';
                        final rain = d['precipitation_mm'] != null ? '${(d['precipitation_mm'] as num).toStringAsFixed(1)}mm' : '0mm';
                        final rainP = d['precipitation_probability_pct'] ?? 0;
                        final cond = (lang == 'ta' && d['condition_ta'] != null) ? d['condition_ta'] : (d['condition_en'] ?? 'Fair');

                        return Container(
                          width: 105,
                          margin: const EdgeInsets.only(right: 8),
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.grey.shade200),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              Text(date, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                              Text(cond, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted), maxLines: 1, overflow: TextOverflow.ellipsis),
                              Text('$maxT / $minT', style: const TextStyle(fontSize: 12, color: AppTheme.textDark)),
                              Text(rain, style: TextStyle(fontSize: 11, color: (d['precipitation_mm'] as num? ?? 0) > 5 ? Colors.blue.shade700 : Colors.grey)),
                              Text('$rainP% rain', style: TextStyle(fontSize: 10, color: (rainP as num) > 50 ? Colors.red.shade700 : Colors.grey)),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Agronomic Guidance Principles
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('TNAU Weather-Aware Application Rules', style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(height: 8),
                        Text(
                          '• Avoid broadcasting Urea before heavy rain to prevent leaching into waterways.\n'
                          '• Maintain 2-3 cm standing water in paddy fields during top-dressing.\n'
                          '• Avoid foliar sprays when wind speed exceeds 15 km/h to prevent spray drift.\n'
                          '• During hot weather (>35°C), apply fertilizers early morning (7-9 AM) with irrigation.',
                          style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.4),
                        ),
                      ],
                    ),
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
