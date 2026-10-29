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
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onTabSelected,
        backgroundColor: Colors.white,
        elevation: 3,
        shadowColor: Colors.black26,
        surfaceTintColor: Colors.transparent,
        indicatorColor: const Color(0xFFC8E6C9),
        height: 72,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home_rounded, color: AppTheme.darkGreen),
            label: l10n.text('home'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.document_scanner_outlined),
            selectedIcon: const Icon(Icons.document_scanner_rounded, color: AppTheme.darkGreen),
            label: l10n.text('soil_reports'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.calculate_outlined),
            selectedIcon: const Icon(Icons.calculate_rounded, color: AppTheme.darkGreen),
            label: l10n.text('fertilizer'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.online_prediction_outlined),
            selectedIcon: const Icon(Icons.online_prediction_rounded, color: AppTheme.darkGreen),
            label: l10n.text('yield_and_weather'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline_rounded),
            selectedIcon: const Icon(Icons.person_rounded, color: AppTheme.darkGreen),
            label: l10n.text('profile'),
          ),
        ],
      ),
    );
  }
}
