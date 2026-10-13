import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';
import 'dashboard_screen.dart';
import 'farm_details_screen.dart';
import 'profile_screen.dart';
import 'upload_screen.dart';
import 'yield_prediction_input_screen.dart';

class MainNavigationShell extends StatefulWidget {
  final int initialIndex;
  const MainNavigationShell({super.key, this.initialIndex = 0});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
  }

  void _onTabSelected(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    final List<Widget> pages = [
      DashboardScreen(onSwitchTab: _onTabSelected),
      UploadScreen(
        onValidatedProfile: (profile) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => FarmDetailsScreen(initialSoilProfile: profile),
            ),
          );
        },
      ),
      const FarmDetailsScreen(),
      const YieldPredictionInputScreen(),
      const ProfileScreen(),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _onTabSelected,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppTheme.primaryGreen,
        unselectedItemColor: const Color(0xFF7D8F7F),
        items: [
          BottomNavigationBarItem(
            icon: const Icon(Icons.home_rounded),
            label: l10n.text('home'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.document_scanner_rounded),
            label: l10n.text('soil_reports'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.calculate_rounded),
            label: l10n.text('fertilizer'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.online_prediction_rounded),
            label: l10n.text('yield_and_weather'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.person_rounded),
            label: l10n.text('profile'),
          ),
        ],
      ),
    );
  }
}
