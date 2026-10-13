import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

class ApplicationScheduleScreen extends StatelessWidget {
  final Map<String, dynamic> scheduleData;
  final String crop;

  const ApplicationScheduleScreen({
    super.key,
    required this.scheduleData,
    required this.crop,
  });

  Widget _stageCard({
    required BuildContext context,
    required String title,
    required String timing,
    required String description,
    required IconData icon,
    required List<String> products,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppTheme.lightGreen,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: AppTheme.primaryGreen, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textDark)),
                      Text(timing, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(description, style: const TextStyle(fontSize: 13, color: AppTheme.textDark, height: 1.3)),
            const SizedBox(height: 10),
            const Divider(),
            const Text('Fertilizer Products at this stage:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            const SizedBox(height: 6),
            for (final p in products)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2.0),
                child: Row(
                  children: [
                    const Icon(Icons.arrow_right_rounded, color: AppTheme.primaryGreen),
                    Expanded(child: Text(p, style: const TextStyle(fontSize: 13))),
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
    return Scaffold(
      appBar: AppBar(title: Text('${l10n.text('application_schedule')} ($crop)')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18.0),
          children: [
            Card(
              color: AppTheme.lightGreen,
              child: const Padding(
                padding: EdgeInsets.all(14.0),
                child: Row(
                  children: [
                    Icon(Icons.tips_and_updates_outlined, color: AppTheme.primaryGreen),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Splitting nitrogen and potassium applications avoids leaching losses in Cauvery delta soils.',
                        style: TextStyle(fontSize: 12.5, color: AppTheme.darkGreen),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            _stageCard(
              context: context,
              title: l10n.text('basal_stage'),
              timing: 'Day 0 (At Sowing / Transplanting)',
              description: 'Apply full phosphorus (DAP / SSP), 25% of nitrogen, and 25% of potassium before last puddling/harrowing.',
              icon: Icons.grain_rounded,
              products: [
                '100% Di-Ammonium Phosphate (DAP) or SSP',
                '25% Neem Coated Urea dose',
                '25% Muriate of Potash (MOP)',
                'Well decomposed FYM (12.5 t/ha) if available',
              ],
            ),
            const SizedBox(height: 12),
            _stageCard(
              context: context,
              title: l10n.text('tillering_stage'),
              timing: '20-25 Days After Sowing/Transplanting',
              description: 'Top-dress 50% of the total nitrogen requirement during active tillering to encourage vigorous root & shoot growth.',
              icon: Icons.grass_rounded,
              products: [
                '50% Neem Coated Urea dose',
                'Ensure standing water is drained or thin layer before top-dressing',
              ],
            ),
            const SizedBox(height: 12),
            _stageCard(
              context: context,
              title: l10n.text('panicle_stage'),
              timing: '40-45 Days (Panicle Initiation)',
              description: 'Apply remaining 25% of nitrogen and 75% of potassium to enhance grain filling, test weight, and disease tolerance.',
              icon: Icons.spa_rounded,
              products: [
                'Remaining 25% Neem Coated Urea',
                'Remaining 75% Muriate of Potash (MOP)',
              ],
            ),
          ],
        ),
      ),
    );
  }
}
