import 'package:flutter/material.dart';
import '../config.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'about_screen.dart';
import 'language_selection_screen.dart';
import 'login_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final currentLang = globalLocaleNotifier.locale.languageCode;
    final langName = currentLang == 'ta' ? 'தமிழ் (Tamil)' : currentLang == 'hi' ? 'हिन्दी (Hindi)' : 'English';

    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('settings'))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18.0),
          children: [
            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.language_rounded, color: AppTheme.primaryGreen),
                    title: Text(l10n.text('preferred_language')),
                    subtitle: Text(langName),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const LanguageSelectionScreen(isFromSettings: true),
                        ),
                      );
                    },
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.dns_outlined, color: AppTheme.primaryGreen),
                    title: const Text('Backend API Server'),
                    subtitle: Text(AppConfig.apiBase),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.info_outline_rounded, color: AppTheme.primaryGreen),
                    title: Text(l10n.text('about')),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const AboutScreen()));
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            Card(
              child: ListTile(
                leading: const Icon(Icons.logout_rounded, color: Colors.red),
                title: Text(l10n.text('logout'), style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                onTap: () {
                  ApiClient.instance.clearSession();
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                    (route) => false,
                  );
                },
              ),
            ),
            const SizedBox(height: 32),
            const Center(
              child: Column(
                children: [
                  Text(
                    'TN Fertilizer Optimizer v1.0.0',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMuted),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'SIH1639 — Sustainable Agriculture DSS',
                    style: TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
