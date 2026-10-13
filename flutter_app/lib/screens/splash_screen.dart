import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'language_selection_screen.dart';
import 'main_navigation_shell.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkInit();
  }

  Future<void> _checkInit() async {
    await Future.delayed(const Duration(milliseconds: 1600));
    if (!mounted) return;

    // Check if session exists or go to language/login
    if (ApiClient.instance.authToken != null) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainNavigationShell()));
    } else {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LanguageSelectionScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkGreen,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.15), blurRadius: 18, offset: const Offset(0, 6)),
                  ],
                ),
                child: const Icon(Icons.agriculture_rounded, size: 68, color: AppTheme.primaryGreen),
              ),
              const SizedBox(height: 28),
              const Text(
                'TN Fertilizer Optimizer',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'AI & Soil-Specific Decision Support\nfor Tamil Nadu Farmers',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFFC8E6C9),
                  fontSize: 14,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 48),
              const SizedBox(
                width: 36,
                height: 36,
                child: CircularProgressIndicator(
                  strokeWidth: 3,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
