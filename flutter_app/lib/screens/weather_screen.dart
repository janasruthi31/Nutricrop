import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class WeatherScreen extends StatefulWidget {
  final String? initialDistrict;
  const WeatherScreen({super.key, this.initialDistrict});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  String _selectedDistrict = 'Thanjavur';
  Map<String, dynamic>? _weather;
  bool _isLoading = true;
  String? _error;

  static const List<String> districts = [
    'Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Mayiladuthurai', 'Cuddalore',
    'Madurai', 'Coimbatore', 'Salem', 'Trichy', 'Erode', 'Tirunelveli', 'Dindigul'
  ];

  @override
  void initState() {
    super.initState();
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
      final res = await ApiClient.instance.getWeatherGuidance(_selectedDistrict);
      setState(() => _weather = res);
    } catch (e) {
      setState(() => _error = 'Weather service temporarily unavailable. Soil-based recommendations remain active.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final risk = _weather?['risk_level'] ?? 'LOW';
    final advice = _weather?['actionable_advice'] ?? 'Weather suitable for fertilizer application and field operations.';
    final condition = _weather?['current_condition'] ?? 'Clear';
    final temp = _weather?['temperature_c'] ?? 31.5;
    final humidity = _weather?['humidity_pct'] ?? 72;
    final rainProb = _weather?['rainfall_probability_pct'] ?? 15;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('weather_title'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on_rounded, color: AppTheme.primaryGreen),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DropdownButton<String>(
                          value: _selectedDistrict,
                          isExpanded: true,
                          underline: const SizedBox(),
                          items: districts.map((d) => DropdownMenuItem(value: d, child: Text('$d District'))).toList(),
                          onChanged: (v) {
                            if (v != null) {
                              setState(() => _selectedDistrict = v);
                              _loadWeather();
                            }
                          },
                        ),
                      ),
                      IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _loadWeather),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),

              if (_isLoading)
                const LoadingView(message: 'Retrieving district agro-weather advisory...')
              else if (_error != null)
                Card(
                  color: const Color(0xFFFFF3E0),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(_error!, style: const TextStyle(color: Color(0xFFE65100))),
                  ),
                )
              else ...[
                // Weather Main Card
                Card(
                  color: AppTheme.darkGreen,
                  child: Padding(
                    padding: const EdgeInsets.all(22.0),
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
                                  '$_selectedDistrict, TN',
                                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  condition,
                                  style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 14),
                                ),
                              ],
                            ),
                            const Icon(Icons.wb_sunny_rounded, color: Color(0xFFFFD54F), size: 48),
                          ],
                        ),
                        const SizedBox(height: 18),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              '${temp.toStringAsFixed(1)}°C',
                              style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.bold),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: risk == 'HIGH' ? Colors.red : Colors.green.withOpacity(0.5),
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
                            Text('Humidity: $humidity%', style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 13)),
                            Text('Rain Probability: $rainProb%', style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 13)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Actionable Advisory Card
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
                          style: const TextStyle(fontSize: 14, color: AppTheme.textDark, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Best Practices Card
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Fertilizer Timing Best Practices', style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(height: 8),
                        Text(
                          '• Avoid applying urea broadcast before intense rainstorms to prevent runoff.\n'
                          '• Ensure thin standing water (2-3 cm) in paddy fields before top-dressing.\n'
                          '• Apply foliar sprays early in the morning (7:00-9:00 AM) or evening.',
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
