import 'package:flutter_test/flutter_test.dart';
import 'package:soil_report_phase3/main.dart';

void main() {
  testWidgets('SoilApp smoke test', (WidgetTester tester) async {
    // Build our app and advance timer beyond splash screen duration
    await tester.pumpWidget(const SoilApp());
    await tester.pump(const Duration(milliseconds: 2000));
    expect(find.byType(SoilApp), findsOneWidget);
  });
}
