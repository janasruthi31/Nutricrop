import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:soil_report_phase3/l10n/app_localizations.dart';
import 'package:soil_report_phase3/screens/crop_selection_screen.dart';
import 'package:soil_report_phase3/screens/farm_details_screen.dart';
import 'package:soil_report_phase3/screens/language_selection_screen.dart';
import 'package:soil_report_phase3/screens/login_screen.dart';
import 'package:soil_report_phase3/screens/register_screen.dart';
import 'package:soil_report_phase3/screens/final_recommendation_screen.dart';
import 'package:soil_report_phase3/screens/dashboard_screen.dart';
import 'package:soil_report_phase3/screens/main_navigation_shell.dart';
import 'package:soil_report_phase3/screens/yield_prediction_input_screen.dart';
import 'package:soil_report_phase3/theme/app_theme.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:soil_report_phase3/services/api_client.dart';

Widget _buildTestableWidget(Widget child, {TextScaler? textScaler, Size? size}) {
  Widget content = child;
  if (size != null || textScaler != null) {
    content = MediaQuery(
      data: MediaQueryData(
        size: size ?? const Size(360, 800),
        textScaler: textScaler ?? TextScaler.noScaling,
      ),
      child: child,
    );
  }
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
    home: content,
  );
}

void main() {
  setUp(() {
    globalLocaleNotifier.setLanguageCode('en');
    ApiClient.enableRetry = false;
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

  testWidgets('FinalRecommendationScreen renders Back to Home button and Home action', (WidgetTester tester) async {
    final mockRec = {
      'crop': 'Groundnut',
      'district': 'Thanjavur',
      'recommendation_type': 'STANDARD_RDF',
      'status': 'OPTIMAL',
      'total_cost_inr': 4500.0,
      'is_verified': true,
      'fertilizers': [
        {
          'name': 'Urea',
          'quantity_kg': 45.0,
          'bags': 1,
          'bag_size_kg': 45.0,
          'total_cost_inr': 266.5,
        }
      ],
      'nutrient_requirements': {
        'n_req_kg_per_ha': 25.0,
        'p2o5_req_kg_per_ha': 50.0,
        'k2o_req_kg_per_ha': 75.0,
        'farm_area_hectares': 1.0,
      },
      'nutrient_balance': {},
      'nutrient_surplus_kg': {},
    };
    await tester.pumpWidget(_buildTestableWidget(FinalRecommendationScreen(recommendationData: mockRec)));
    expect(find.byIcon(Icons.home_rounded), findsWidgets);
    expect(find.text('Back to Home / முகப்புக்குச் செல்க'), findsOneWidget);
  });

  testWidgets('DashboardScreen renders in Tamil on narrow screen with 1.3x text scaling without overflow', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('ta');
    // Set a narrow phone screen size (320x640) and 1.3x text scaling factor
    await tester.binding.setSurfaceSize(const Size(320, 700));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_buildTestableWidget(
      const DashboardScreen(),
      textScaler: const TextScaler.linear(1.3),
      size: const Size(320, 700),
    ));
    await tester.pumpAndSettle();

    // Verify Tamil greeting & quick actions title
    expect(find.text('வணக்கம் உழவரே!'), findsOneWidget);
    expect(find.text('விரைவு சேவைகள்'), findsOneWidget);

    // Verify all 6 action cards are rendered and visible
    expect(find.text('மண் அட்டை பதிவேற்று'), findsWidgets);
    expect(find.text('உர பரிந்துரை பெறு'), findsOneWidget);
    expect(find.text('விளைச்சல் கணிப்பு'), findsOneWidget);
    expect(find.text('வானிலை ஆலோசனை'), findsOneWidget);
    expect(find.text('வரலாறு'), findsOneWidget);
    expect(find.text('Download Reports'), findsOneWidget);

    // Verify Short Flow banner and 3 STEPS badge
    expect(find.text('Short Flow / விரைவு முறை'), findsOneWidget);
    expect(find.text('3 STEPS'), findsOneWidget);

    // Verify no RenderFlex overflow error was thrown
    expect(tester.takeException(), isNull);
  });

  testWidgets('MainNavigationShell renders Material 3 NavigationBar with all 5 destinations in Tamil', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('ta');
    await tester.binding.setSurfaceSize(const Size(360, 740));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_buildTestableWidget(const MainNavigationShell()));
    await tester.pumpAndSettle();

    // Verify NavigationBar exists
    expect(find.byType(NavigationBar), findsOneWidget);

    // Verify 5 Tamil destinations
    expect(find.text('முகப்பு'), findsOneWidget);
    expect(find.text('மண் அறிக்கை'), findsOneWidget);
    expect(find.text('உர பரிந்துரை'), findsOneWidget);
    expect(find.text('விளைச்சல் & வானிலை'), findsOneWidget);
    expect(find.text('சுயவிவரம்'), findsOneWidget);

    // Test tab selection to Soil Reports (tab 1)
    await tester.tap(find.text('மண் அறிக்கை'));
    await tester.pumpAndSettle();

    // Test tab selection to Profile (tab 4)
    await tester.tap(find.text('சுயவிவரம்'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });

  testWidgets('DashboardScreen renders across English, Tamil, and Hindi without layout exceptions', (WidgetTester tester) async {
    addTearDown(() {
      tester.binding.setSurfaceSize(null);
      globalLocaleNotifier.setLanguageCode('en');
    });
    for (final lang in ['en', 'ta', 'hi']) {
      globalLocaleNotifier.setLanguageCode(lang);
      await tester.binding.setSurfaceSize(const Size(360, 740));
      await tester.pumpWidget(_buildTestableWidget(
        const DashboardScreen(),
        textScaler: const TextScaler.linear(1.2),
      ));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('FinalRecommendationScreen renders Unified Priority 2 badge, reason, and farm nutrients', (WidgetTester tester) async {
    globalLocaleNotifier.setLanguageCode('en');
    final mockRec = {
      'crop': 'Rice',
      'district': 'Thanjavur',
      'is_verified': true,
      'unified_recommendation': {
        'priority_tier': 2,
        'rule_priority': 'Priority 2 (Validated TNAU Soil-Test Based Recommendation)',
        'selected_rule_id': 'TNAU_STD_RICE_001',
        'selection_reason': 'Selected official TNAU soil-test calibrated schedule for Rice.',
        'status': 'SUCCESS',
        'total_cost_status': 'AVAILABLE',
      },
      'nutrient_requirements': {
        'selected_rule_id': 'TNAU_STD_RICE_001',
        'is_verified_rule': true,
        'total_n_req_kg': 60.0,
        'total_p2o5_req_kg': 25.0,
        'total_k2o_req_kg': 25.0,
        'farm_area_original': 1.0,
        'farm_area_unit_original': 'acre',
        'farm_area_hectares': 0.404686,
      },
      'fertilizer_plan': {
        'status': 'OPTIMIZATION_SUCCESS',
        'total_cost_inr': 2450.0,
        'total_cost_status': 'AVAILABLE',
        'recommended_products': [
          {
            'product_name': 'Neem Coated Urea',
            'quantity_kg': 75.0,
            'bags': 2,
            'bag_size_kg': 45.0,
            'total_cost_inr': 533.0,
          }
        ],
        'nutrient_balance': {
          'nitrogen': {'required_kg': 60.0, 'supplied_kg': 60.0, 'surplus_kg': 0.0, 'surplus_pct': 0.0},
          'phosphorus_p2o5': {'required_kg': 25.0, 'supplied_kg': 25.0, 'surplus_kg': 0.0, 'surplus_pct': 0.0},
          'potassium_k2o': {'required_kg': 25.0, 'supplied_kg': 25.0, 'surplus_kg': 0.0, 'surplus_pct': 0.0},
        },
      },
    };

    await tester.pumpWidget(_buildTestableWidget(FinalRecommendationScreen(recommendationData: mockRec)));
    await tester.pumpAndSettle();

    expect(find.textContaining('Unified Recommendation • Priority 2'), findsOneWidget);
    expect(find.textContaining('Selected official TNAU soil-test calibrated schedule for Rice.'), findsOneWidget);
    expect(find.text('Required Nutrients for Farm'), findsOneWidget);
    expect(find.text('₹2450'), findsOneWidget);
  });

  testWidgets('FinalRecommendationScreen renders Cost Unavailable instead of ₹0 when prices are missing', (WidgetTester tester) async {
    final mockRec = {
      'crop': 'Blackgram',
      'district': 'Thanjavur',
      'is_verified': true,
      'total_cost_status': 'UNAVAILABLE',
      'unified_recommendation': {
        'priority_tier': 2,
        'rule_priority': 'Priority 2 (Validated TNAU Soil-Test Based Recommendation)',
        'selected_rule_id': 'TNAU_STD_BLACKGRAM_RF_001',
        'selection_reason': 'Selected official TNAU soil-test calibrated recommendation.',
        'status': 'SUCCESS',
        'total_cost_status': 'UNAVAILABLE',
      },
      'nutrient_requirements': {
        'selected_rule_id': 'TNAU_STD_BLACKGRAM_RF_001',
        'total_n_req_kg': 12.5,
        'total_p2o5_req_kg': 25.0,
        'total_k2o_req_kg': 12.5,
      },
      'fertilizer_plan': {
        'status': 'OPTIMIZATION_SUCCESS',
        'total_cost_inr': 0.0,
        'total_cost_status': 'UNAVAILABLE',
        'recommended_products': [
          {
            'product_name': 'DAP',
            'quantity_kg': 54.3,
            'bags': 2,
            'bag_size_kg': 50.0,
            'total_cost_inr': 0.0,
          }
        ],
        'nutrient_balance': {},
      },
    };

    await tester.pumpWidget(_buildTestableWidget(FinalRecommendationScreen(recommendationData: mockRec)));
    await tester.pumpAndSettle();

    expect(find.text('Cost Unavailable'), findsOneWidget);
    expect(find.text('Price Unavailable'), findsOneWidget);
    expect(find.text('₹0'), findsNothing);
  });
}


