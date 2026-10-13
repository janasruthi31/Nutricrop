import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'l10n/app_localizations.dart';
import 'screens/splash_screen.dart';
import 'theme/app_theme.dart';

void main() => runApp(const SoilApp());

class SoilApp extends StatelessWidget {
  const SoilApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: globalLocaleNotifier,
      builder: (context, _) {
        return MaterialApp(
          title: 'TN Fertilizer Optimizer',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          locale: globalLocaleNotifier.locale,
          supportedLocales: const [
            Locale('en', ''),
            Locale('ta', ''),
            Locale('hi', ''),
          ],
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const SplashScreen(),
        );
      },
    );
  }
}
