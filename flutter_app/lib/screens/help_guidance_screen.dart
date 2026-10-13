import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

class HelpGuidanceScreen extends StatelessWidget {
  const HelpGuidanceScreen({super.key});

  Widget _guideItem({
    required String question,
    required String answer,
    required IconData icon,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: Icon(icon, color: AppTheme.primaryGreen),
        title: Text(question, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Text(answer, style: const TextStyle(fontSize: 13.5, color: AppTheme.textDark, height: 1.4)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('help_title'))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18.0),
          children: [
            Card(
              color: AppTheme.lightGreen,
              child: const Padding(
                padding: EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    Icon(Icons.support_agent_rounded, color: AppTheme.primaryGreen, size: 36),
                    SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        'Tamil Nadu Farmer Help & Decision Support Guide.\nClear answers to your agronomy questions.',
                        style: TextStyle(fontSize: 13, color: AppTheme.darkGreen, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _guideItem(
              icon: Icons.document_scanner_rounded,
              question: 'How do I upload my Soil Health Card?',
              answer: 'You can upload your official government Soil Health Card as a PDF document, or take a clear photograph with your phone camera. Our OCR reader automatically detects available Nitrogen, Phosphorus, Potassium, pH, and organic carbon.',
            ),
            _guideItem(
              icon: Icons.check_circle_outline_rounded,
              question: 'Why do I need to verify extracted soil values?',
              answer: 'OCR can misread numbers if the print or paper is folded. The verification screen lets you review every number and make corrections before any calculation is made. We never store unverified data.',
            ),
            _guideItem(
              icon: Icons.calculate_outlined,
              question: 'How are NPK requirements calculated?',
              answer: 'We use official Soil Test Crop Response (STCR) linear regression equations developed by Tamil Nadu Agricultural University (TNAU). They calculate the exact kilograms of Nitrogen, Phosphorus, and Potassium needed for your target yield, accounting for natural nutrients in your soil.',
            ),
            _guideItem(
              icon: Icons.price_check_rounded,
              question: 'How does fertilizer cost optimization work?',
              answer: 'Commercial fertilizers like Urea, DAP, and Potash come in fixed bag sizes (45kg and 50kg) with different nutrient ratios. Our Linear Programming solver finds the cheapest combination of bags that fulfills 100% of your crop nutrient requirement at subsidized MRP.',
            ),
            _guideItem(
              icon: Icons.analytics_outlined,
              question: 'What is the District Yield Benchmark?',
              answer: 'Our Machine Learning model (XGBoost) predicts the historical district-average yield for Tamil Nadu districts based on monsoon rainfall and crop reports. It serves as an informative regional benchmark, not a guaranteed farm yield.',
            ),
            _guideItem(
              icon: Icons.picture_as_pdf_outlined,
              question: 'Can I print or share my recommendation?',
              answer: 'Yes! Go to any saved recommendation and tap "Download PDF Report". The system generates an official summary sheet with bag counts, split application timing, and agronomic citations.',
            ),
          ],
        ),
      ),
    );
  }
}
