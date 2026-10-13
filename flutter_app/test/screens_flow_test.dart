import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:soil_report_phase3/l10n/app_localizations.dart';
import 'package:soil_report_phase3/screens/crop_selection_screen.dart';
import 'package:soil_report_phase3/screens/farm_details_screen.dart';
import 'package:soil_report_phase3/screens/language_selection_screen.dart';
import 'package:soil_report_phase3/screens/login_screen.dart';
import 'package:soil_report_phase3/screens/register_screen.dart';
import 'package:soil_report_phase3/screens/yield_prediction_input_screen.dart';
import 'package:soil_report_phase3/theme/app_theme.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

Widget _buildTestableWidget(Widget child) {
  return MaterialApp(
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
    home: child,
  );
}

void main() {
  setUp(() {
    globalLocaleNotifier.setLanguageCode('en');
  });

  testWidgets('LanguageSelectionScreen displays English, Tamil, Hindi options', (WidgetTester tester) async {
    await tester.pumpWidget(_buildTestableWidget(const LanguageSelectionScreen()));
    expect(find.text('தமிழ்'), findsOneWidget);
    expect(find.text('English'), findsWidgets);
    expect(find.text('हिन्दी'), findsOneWidget);
  });

  testWidgets('LoginScreen renders email, password fields and login button', (WidgetTester tester) async {
    await tester.pumpWidget(_buildTestableWidget(const LoginScreen()));
    expect(find.byType(TextField), findsNWidgets(2));
    expect(find.text('Farmer Login'), findsOneWidget);
    expect(find.text('Log In'), findsOneWidget);
  });

  testWidgets('RegisterScreen renders form fields', (WidgetTester tester) async {
    await tester.pumpWidget(_buildTestableWidget(const RegisterScreen()));
    expect(find.text('Farmer Registration'), findsOneWidget);
    expect(find.byType(TextField), findsNWidgets(4));
  });

  testWidgets('FarmDetailsScreen renders district dropdown and area input', (WidgetTester tester) async {
    await tester.pumpWidget(_buildTestableWidget(const FarmDetailsScreen()));
    expect(find.text('Farm & Crop Details'), findsOneWidget);
    expect(find.text('Thanjavur'), findsOneWidget);
  });

  testWidgets('CropSelectionScreen renders verified crops', (WidgetTester tester) async {
    final mockFarm = {
      'district': 'Thanjavur',
      'village': 'Needamangalam',
      'area': 1.0,
      'area_unit': 'hectare',
      'irrigation': 'Irrigated',
      'soil_series': 'Palavidhi',
    };
    await tester.pumpWidget(_buildTestableWidget(CropSelectionScreen(farmDetails: mockFarm)));
    expect(find.text('Target Crop'), findsWidgets);
    expect(find.textContaining('Rice'), findsWidgets);
  });

  testWidgets('YieldPredictionInputScreen renders rainfall inputs', (WidgetTester tester) async {
    await tester.pumpWidget(_buildTestableWidget(const YieldPredictionInputScreen()));
    expect(find.text('Predict Crop Yield'), findsWidgets);
    expect(find.textContaining('SW Monsoon'), findsOneWidget);
    expect(find.textContaining('NE Monsoon'), findsOneWidget);
  });

  testWidgets('Dynamic Tamil Language Switching Verification', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('ta');
    await tester.pumpWidget(_buildTestableWidget(const FarmDetailsScreen()));
    expect(find.text('பண்ணை மற்றும் பயிர் விவரங்கள்'), findsOneWidget);
  });

  testWidgets('Dynamic Hindi Language Switching Verification', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('hi');
    await tester.pumpWidget(_buildTestableWidget(const FarmDetailsScreen()));
    expect(find.text('खेत और फसल विवरण'), findsOneWidget);
  });

  testWidgets('LoginScreen displays Forgot Password button and opens recovery dialog', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('en');
    await tester.pumpWidget(_buildTestableWidget(const LoginScreen()));
    final forgotBtn = find.text('Forgot Password?');
    expect(forgotBtn, findsOneWidget);
    await tester.tap(forgotBtn);
    await tester.pumpAndSettle();
    expect(find.text('Enter your registered email or phone to reset your password.'), findsOneWidget);
  });

  testWidgets('Localized error messages exist in all 3 languages', (WidgetTester tester) async {
    for (final code in ['en', 'ta', 'hi']) {
      final loc = AppLocalizations(Locale(code));
      expect(loc.text('upload_failure').isNotEmpty, isTrue);
      expect(loc.text('ocr_failure').isNotEmpty, isTrue);
      expect(loc.text('missing_values').isNotEmpty, isTrue);
      expect(loc.text('unsupported_crop').isNotEmpty, isTrue);
      expect(loc.text('optimization_failure').isNotEmpty, isTrue);
      expect(loc.text('weather_failure').isNotEmpty, isTrue);
      expect(loc.text('yield_failure').isNotEmpty, isTrue);
    }
  });
}
