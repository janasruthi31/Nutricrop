import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class LanguageSelectionScreen extends StatelessWidget {
  final bool isFromSettings;
  const LanguageSelectionScreen({super.key, this.isFromSettings = false});

  Widget _langOption(BuildContext context, {required String code, required String name, required String nativeName, required String flag}) {
    final isSelected = globalLocaleNotifier.locale.languageCode == code;
    return Card(
      elevation: isSelected ? 3 : 1,
      color: isSelected ? AppTheme.lightGreen : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: isSelected ? AppTheme.primaryGreen : const Color(0xFFD4E2D2),
          width: isSelected ? 2 : 1,
        ),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        leading: Text(flag, style: const TextStyle(fontSize: 28)),
        title: Text(nativeName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textDark)),
        subtitle: Text(name, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
        trailing: isSelected
            ? const Icon(Icons.check_circle_rounded, color: AppTheme.primaryGreen, size: 26)
            : const Icon(Icons.radio_button_off_rounded, color: Colors.grey),
        onTap: () {
          globalLocaleNotifier.setLanguageCode(code);
          if (isFromSettings) {
            Navigator.pop(context);
          } else {
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
          }
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.text('select_language')),
        automaticallyImplyLeading: isFromSettings,
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: (constraints.maxHeight - 48).clamp(0.0, double.infinity)),
                child: IntrinsicHeight(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const SizedBox(height: 12),
                      Text(
                        l10n.text('select_language'),
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppTheme.textDark),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        l10n.text('language_desc'),
                        style: const TextStyle(fontSize: 14, color: AppTheme.textMuted),
                      ),
                      const SizedBox(height: 32),
                      _langOption(
                        context,
                        code: 'ta',
                        name: 'Tamil',
                        nativeName: 'தமிழ்',
                        flag: '🌾',
                      ),
                      const SizedBox(height: 14),
                      _langOption(
                        context,
                        code: 'en',
                        name: 'English',
                        nativeName: 'English',
                        flag: '🇮🇳',
                      ),
                      const SizedBox(height: 14),
                      _langOption(
                        context,
                        code: 'hi',
                        name: 'Hindi',
                        nativeName: 'हिन्दी',
                        flag: '🌱',
                      ),
                      const Spacer(),
                      const SizedBox(height: 20),
                      if (!isFromSettings)
                        FilledButton(
                          onPressed: () {
                            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
                          },
                          child: Text(l10n.text('continue_btn')),
                        ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
