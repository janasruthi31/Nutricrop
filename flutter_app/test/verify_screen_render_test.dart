import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:soil_report_phase3/screens/verify_screen.dart';

void main() {
  testWidgets('VerifyScreen renders with full 12 fields from real PDF', (WidgetTester tester) async {
    final mockOcr = {
      "status": "extracted",
      "verification_required": true,
      "document_id": "8f6d7b15e2a547b7a637d483560de8f2",
      "ocr_id": "f324276f5b7842c0b51441777fb624ff",
      "fields": [
        {'field': 'nitrogen', 'label': 'Nitrogen (N)', 'ocr_value': '39', 'value': 39.0, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': 'Low', 'verification_state': 'extracted_unverified'},
        {'field': 'phosphorus', 'label': 'Phosphorus (P)', 'ocr_value': '4', 'value': 4.0, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'uncertain', 'issues': [{'code': 'p_method_unknown', 'severity': 'warning', 'message': 'Phosphorus test method (Olsen or Bray) is not known.'}], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'potassium', 'label': 'Potassium (K)', 'ocr_value': '259', 'value': 259.0, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': 'High', 'verification_state': 'extracted_unverified'},
        {'field': 'ph', 'label': 'pH', 'ocr_value': '7.3', 'value': 7.3, 'unit': null, 'original_unit': null, 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'organic_carbon', 'label': 'Organic Carbon (OC)', 'ocr_value': '0.45', 'value': 0.45, 'unit': '%', 'original_unit': '%', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': 'Low', 'verification_state': 'extracted_unverified'},
        {'field': 'ec', 'label': 'Electrical Conductivity (EC)', 'ocr_value': '0.41', 'value': 0.41, 'unit': 'dS/m', 'original_unit': 'dS/m', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'sulphur', 'label': 'Sulphur (S)', 'ocr_value': '5', 'value': 5.0, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'zinc', 'label': 'Zinc (Zn)', 'ocr_value': '0.43', 'value': 0.43, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'iron', 'label': 'Iron (Fe)', 'ocr_value': '1.9', 'value': 1.9, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'manganese', 'label': 'Manganese (Mn)', 'ocr_value': '2.59', 'value': 2.59, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'copper', 'label': 'Copper (Cu)', 'ocr_value': '0.5', 'value': 0.5, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'},
        {'field': 'boron', 'label': 'Boron (B)', 'ocr_value': '0.56', 'value': 0.56, 'unit': 'kg/acre', 'original_unit': 'kg/acre', 'test_method': null, 'method_source': null, 'ocr_confidence': 0.98, 'status': 'valid', 'issues': [], 'classification': null, 'verification_state': 'extracted_unverified'}
      ],
      "metadata": {
        "crop_raw": "நிலக்கடலை",
        "crop": "groundnut",
        "farm_area": 1.0,
        "farm_area_unit": "acre",
        "sample_id": "TN/ERD/02488",
        "district": "Erode",
        "village": "வரதநல்லூர்"
      },
      "mean_ocr_confidence": 0.98,
      "warnings": [
        {
          "code": "p_method_unknown",
          "severity": "warning",
          "message": "Phosphorus test method (Olsen / Bray) not found. Please select it if you know it."
        }
      ]
    };

    await tester.pumpWidget(
      MaterialApp(
        home: VerifyScreen(
          ocr: mockOcr,
          onValidatedProfile: (_) {},
        ),
      ),
    );

    expect(find.text('Review Extracted Soil Information'), findsOneWidget);
    expect(find.text('Nitrogen (N)'), findsOneWidget);
    expect(find.text('Phosphorus (P)'), findsOneWidget);
    expect(find.text('Potassium (K)'), findsOneWidget);
    expect(find.text('pH'), findsOneWidget);
  });
}
