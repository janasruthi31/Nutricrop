import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const SectionHeader({super.key, required this.title, this.subtitle, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 14, bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textDark,
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle!,
                    style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                  ),
                ]
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class LoadingView extends StatelessWidget {
  final String message;
  const LoadingView({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppTheme.primaryGreen),
            const SizedBox(height: 18),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 15, color: AppTheme.textMuted, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }
}

class ErrorStateView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorStateView({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline_rounded, size: 54, color: Color(0xFFD32F2F)),
            const SizedBox(height: 14),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 15, color: AppTheme.textDark, fontWeight: FontWeight.w500),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Try Again'),
              ),
            ]
          ],
        ),
      ),
    );
  }
}

class EmptyStateView extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String? buttonLabel;
  final VoidCallback? onAction;

  const EmptyStateView({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.buttonLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: const Color(0xFFA1B4A3)),
            const SizedBox(height: 16),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppTheme.textDark),
            ),
            const SizedBox(height: 6),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
            ),
            if (buttonLabel != null && onAction != null) ...[
              const SizedBox(height: 22),
              FilledButton(
                onPressed: onAction,
                child: Text(buttonLabel!),
              ),
            ]
          ],
        ),
      ),
    );
  }
}

class FertilizerProductCard extends StatelessWidget {
  final String name;
  final double quantityKg;
  final double? quantityPerHaKg;
  final double? totalFarmQuantityKg;
  final String? applicationTiming;
  final int bags;
  final double bagSizeKg;
  final double totalCostInr;
  final double? pricePerBagInr;
  final String? priceSource;
  final String? priceEffectiveDate;
  final String? description;

  const FertilizerProductCard({
    super.key,
    required this.name,
    required this.quantityKg,
    this.quantityPerHaKg,
    this.totalFarmQuantityKg,
    this.applicationTiming,
    required this.bags,
    required this.bagSizeKg,
    required this.totalCostInr,
    this.pricePerBagInr,
    this.priceSource,
    this.priceEffectiveDate,
    this.description,
  });

  @override
  Widget build(BuildContext context) {
    final farmQty = totalFarmQuantityKg ?? quantityKg;
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
                  child: const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    name,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textDark),
                  ),
                ),
                Text(
                  '₹${totalCostInr.toStringAsFixed(0)}',
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F6F0),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Total for Farm: ${farmQty.toStringAsFixed(1)} kg',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textDark),
                      ),
                      Text(
                        pricePerBagInr != null
                            ? '$bags bags (₹${pricePerBagInr!.toStringAsFixed(0)} / ${bagSizeKg.toStringAsFixed(0)}kg)'
                            : '$bags bags (${bagSizeKg.toStringAsFixed(0)} kg/bag)',
                        style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                      ),
                    ],
                  ),
                  if (quantityPerHaKg != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Rate per Hectare: ${quantityPerHaKg!.toStringAsFixed(1)} kg/ha',
                          style: const TextStyle(fontSize: 12, color: AppTheme.primaryGreen, fontWeight: FontWeight.w600),
                        ),
                        Text(
                          '≈ ${(quantityPerHaKg! * 0.4046856422).toStringAsFixed(1)} kg/acre',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            if (applicationTiming != null && applicationTiming!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.schedule_rounded, size: 16, color: Color(0xFF2E7D32)),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Application Timing: $applicationTiming',
                        style: const TextStyle(fontSize: 11, color: Color(0xFF1B5E20), fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (priceSource != null && priceSource!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  const Icon(Icons.verified_outlined, size: 14, color: AppTheme.primaryGreen),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      'Rate source: $priceSource${priceEffectiveDate != null ? ' (Eff: $priceEffectiveDate)' : ''}',
                      style: const TextStyle(fontSize: 11, color: AppTheme.darkGreen, fontStyle: FontStyle.italic),
                    ),
                  ),
                ],
              ),
            ],
            if (description != null && description!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(description!, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            ]
          ],
        ),
      ),
    );
  }
}
