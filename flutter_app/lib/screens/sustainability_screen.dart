import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

class SustainabilityScreen extends StatelessWidget {
  final Map<String, dynamic> recommendationData;
  const SustainabilityScreen({super.key, required this.recommendationData});

  Widget _insightTile({
    required IconData icon,
    required String title,
    required String desc,
    required Color color,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textDark)),
                  const SizedBox(height: 4),
                  Text(desc, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.35)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final crop = recommendationData['crop'] ?? 'Crop';

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('sustainability_title'))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18.0),
          children: [
            Card(
              color: AppTheme.lightGreen,
              child: Padding(
                padding: const EdgeInsets.all(18.0),
                child: Column(
                  children: [
                    const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen, size: 42),
                    const SizedBox(height: 10),
                    const Text(
                      'Sustainable Soil Health & Nutrient Balance',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.darkGreen),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Calculated using TNAU STCR-IPNS (Integrated Plant Nutrition System) for $crop.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 13, color: AppTheme.textDark),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _insightTile(
              icon: Icons.balance_rounded,
              title: 'Balanced Nutrient Supply',
              desc: 'By testing your soil, fertilizer doses are matched to existing soil fertility. This avoids excessive nitrogen broadcasting which attracts stem borers and causes lodging.',
              color: const Color(0xFF2E7D32),
            ),
            const SizedBox(height: 10),
            _insightTile(
              icon: Icons.savings_outlined,
              title: 'Optimized Fertilizer Expenditure',
              desc: 'Linear programming solver selects the lowest cost combination of straight and complex fertilizers, saving typical farmers 15-25% compared to arbitrary DAP/Urea bags.',
              color: const Color(0xFF0288D1),
            ),
            const SizedBox(height: 10),
            _insightTile(
              icon: Icons.water_drop_outlined,
              title: 'Groundwater & River Protection',
              desc: 'Prevents excess nitrate runoff into Cauvery delta irrigation canals and protects local drinking water aquifers from contamination.',
              color: const Color(0xFF7B1FA2),
            ),
            const SizedBox(height: 10),
            _insightTile(
              icon: Icons.compost_rounded,
              title: 'Organic Matter (IPNS Component)',
              desc: 'Integrating 12.5 t/ha Farmyard Manure (FYM) or green manure with chemical fertilizers improves soil microbial biomass, moisture retention, and cation exchange capacity.',
              color: const Color(0xFFE65100),
            ),
          ],
        ),
      ),
    );
  }
}
