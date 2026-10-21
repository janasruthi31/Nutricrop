import 'package:flutter/material.dart';
import '../config.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'about_screen.dart';
import 'language_selection_screen.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  void _showServerConfigDialog() {
    final controller = TextEditingController(text: AppConfig.apiBase);
    String statusMsg = '';
    bool isTesting = false;

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.dns_outlined, color: AppTheme.primaryGreen),
              SizedBox(width: 8),
              Text('Backend API Server', style: TextStyle(fontSize: 18)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Select a preset or enter the host address of your running FastAPI server:',
                  style: TextStyle(fontSize: 13, color: Colors.black87),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    ActionChip(
                      label: const Text('Localhost (USB Reverse)'),
                      onPressed: () {
                        setDialogState(() {
                          controller.text = 'http://127.0.0.1:8000';
                        });
                      },
                    ),
                    ActionChip(
                      label: const Text('Wi-Fi (10.1.144.51)'),
                      onPressed: () {
                        setDialogState(() {
                          controller.text = 'http://10.1.144.51:8000';
                        });
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: controller,
                  decoration: const InputDecoration(
                    labelText: 'API Base URL',
                    hintText: 'http://10.1.144.51:8000',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.link_rounded),
                  ),
                ),
                if (statusMsg.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: statusMsg.startsWith('Connected') ? Colors.green.shade50 : Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: statusMsg.startsWith('Connected') ? Colors.green : Colors.red,
                      ),
                    ),
                    child: Text(
                      statusMsg,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: statusMsg.startsWith('Connected') ? Colors.green.shade800 : Colors.red.shade800,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: isTesting
                  ? null
                  : () async {
                      setDialogState(() {
                        isTesting = true;
                        statusMsg = 'Testing connection...';
                      });
                      AppConfig.setApiBase(controller.text);
                      try {
                        final res = await ApiClient.instance.checkHealth();
                        setDialogState(() {
                          isTesting = false;
                          statusMsg = 'Connected! Database: ${res["database"]} • Status: ${res["status"]}';
                        });
                      } catch (e) {
                        setDialogState(() {
                          isTesting = false;
                          statusMsg = 'Failed to connect. Please check IP and port.';
                        });
                      }
                    },
              child: isTesting
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Test Connection'),
            ),
            ElevatedButton(
              onPressed: () {
                AppConfig.setApiBase(controller.text);
                setState(() {});
                Navigator.pop(dialogCtx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('API Server updated: ${AppConfig.apiBase}'),
                    backgroundColor: AppTheme.primaryGreen,
                  ),
                );
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

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
                    trailing: const Icon(Icons.edit_rounded, size: 20, color: AppTheme.primaryGreen),
                    onTap: _showServerConfigDialog,
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.storage_rounded, color: AppTheme.primaryGreen),
                    title: const Text('SQLite Database Storage'),
                    subtitle: const Text('soil_phase3.sqlite3 • Connected'),
                    trailing: const Icon(Icons.check_circle_rounded, color: Colors.green),
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Row(
                            children: [
                              Icon(Icons.storage_rounded, color: AppTheme.primaryGreen),
                              SizedBox(width: 8),
                              Text('SQLite Database', style: TextStyle(fontSize: 18)),
                            ],
                          ),
                          content: const Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Status: Connected & Synchronized', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
                              SizedBox(height: 8),
                              Text('File: phase3_soil/soil_phase3.sqlite3', style: TextStyle(fontFamily: 'monospace', fontSize: 12)),
                              SizedBox(height: 12),
                              Text('Active Stored Tables:'),
                              Text('• Confirmed Soil Reports (soil_profiles)'),
                              Text('• Soil Test Parameters (soil_profile_fields)'),
                              Text('• Farmer Farms & Area (farmer_farms)'),
                              Text('• Saved Fertilizer Plans (saved_recommendations)'),
                              Text('• Farmer Auth & Credentials (users)'),
                              Text('• Open-Meteo Weather Cache (weather_cache)'),
                            ],
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(ctx),
                              child: const Text('Close'),
                            ),
                          ],
                        ),
                      );
                    },
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
