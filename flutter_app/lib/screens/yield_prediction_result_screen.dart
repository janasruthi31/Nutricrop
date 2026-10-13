import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

class YieldPredictionResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;
  const YieldPredictionResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final estKg = (result['estimated_yield_kg_per_ha'] as num?)?.toDouble() ?? 0.0;
    final estTonnes = estKg / 1000.0;
    final crop = result['crop'] ?? 'Crop';
    final district = result['district'] ?? 'District';
    final season = result['season'] ?? 'Season';
    final year = result['year'] ?? 2024;
    final disclaimer = result['disclaimer'] ?? l10n.text('yield_disclaimer');

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('yield_title'))),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(22.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                color: AppTheme.primaryGreen,
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    children: [
                      Text(
                        l10n.text('estimated_district_yield'),
                        style: const TextStyle(color: Color(0xFFC8E6C9), fontSize: 13),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${estKg.toStringAsFixed(0)} kg/ha',
                        style: const TextStyle(color: Colors.white, fontSize: 34, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '≈ ${estTonnes.toStringAsFixed(2)} Tonnes / hectare',
                        style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 14),
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(
                          '$crop • $district • $season ($year)',
                          style: const TextStyle(color: Colors.white, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.psychology_rounded, color: AppTheme.primaryGreen),
                          SizedBox(width: 8),
                          Text('Phase 2 Machine Learning Model', style: TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Algorithm: Gradient Boosted Trees (XGBoost Regressor)\n'
                        'Trained on: Tamil Nadu Season & Crop Reports (2020-21 to 2024-25)\n'
                        'Features: District, Crop, Season, SWM, NEM, Winter & Annual Rainfall.',
                        style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.4),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
              Card(
                color: const Color(0xFFFFF8E1),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: Color(0xFFFFECB3)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Color(0xFFF57F17)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          disclaimer,
                          style: const TextStyle(fontSize: 12.5, color: Color(0xFF5D4037), height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const Spacer(),
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Back to Prediction Form'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
