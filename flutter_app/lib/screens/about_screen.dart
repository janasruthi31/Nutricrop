import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('about_title'))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20.0),
          children: [
            Center(
              child: Container(
                padding: const EdgeInsets.all(18),
                decoration: const BoxDecoration(
                  color: AppTheme.lightGreen,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.agriculture_rounded, size: 54, color: AppTheme.primaryGreen),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'AI-Based Soil-Specific Fertilizer Recommendation & Crop Yield Prediction System for Tamil Nadu Farmers',
              textAlign: TextAlign.center,
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textDark),
            ),
            const SizedBox(height: 6),
            const Text(
              'Project Reference: SIH1639',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppTheme.primaryGreen, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 20),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('System Architecture & Phased Design', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    SizedBox(height: 8),
                    Text(
                      '• Phase 1 & 2: 38-District Tamil Nadu Season & Crop Reports (2020-25) + XGBoost ML District Yield Benchmark Model.\n'
                      '• Phase 3: Soil Health Card OCR Sniffing, Range Validation & Farmer Confirmation.\n'
                      '• Phase 4: Verified TNAU / STCR / IPNS Agronomic Rule Selector.\n'
                      '• Phase 5: Deterministic NPK Nutrient Requirement Calculation Engine.\n'
                      '• Phase 6: SciPy Linear Programming Fertilizer Cost & Bag Optimizer.\n'
                      '• Phase 7: District Agro-Weather Advisories & Master Pipeline.\n'
                      '• Phase 8: Automated Test Suite & ReportLab PDF Generator.',
                      style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.45),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Official Agronomic Data Sources', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    SizedBox(height: 8),
                    Text(
                      '1. Tamil Nadu Agricultural University (TNAU) Agritech Portal\n'
                      '2. STCR-IPNS Calibration Schemes (Dept. of Soil Science, TNAU Coimbatore)\n'
                      '3. Season and Crop Reports of Tamil Nadu (Dept. of Economics and Statistics)\n'
                      '4. National Soil Health Card Scheme Guidelines (Ministry of Agriculture, GoI)',
                      style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.45),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            const Card(
              color: Color(0xFFF1F8E9),
              child: Padding(
                padding: EdgeInsets.all(14.0),
                child: Text(
                  'Disclaimer: Fertilizer recommendations and bag counts are calculated using verified scientific models for educational and advisory support. Yield predictions represent regional district benchmarks, not individual field guarantees.',
                  style: TextStyle(fontSize: 12, color: AppTheme.darkGreen, height: 1.35),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
