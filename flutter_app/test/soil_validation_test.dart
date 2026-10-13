import 'package:flutter_test/flutter_test.dart';
import 'package:soil_report_phase3/models/soil_field.dart';

FieldDraft d(String k, String v, {String? unit, String? method}) =>
    FieldDraft(key: k, valueText: v, unit: unit ?? specFor(k).units.first, method: method);

void main() {
  test('empty value is missing, not invalid', () {
    expect(SoilValidator.check('nitrogen', '', 'kg/ha', null).status, FieldStatus.missing);
  });
  test('non numeric and out of range are invalid', () {
    expect(SoilValidator.check('nitrogen', 'abc', 'kg/ha', null).status, FieldStatus.invalid);
    expect(SoilValidator.check('ph', '16.8', null, null).status, FieldStatus.invalid);
    expect(SoilValidator.check('nitrogen', '-5', 'kg/ha', null).status, FieldStatus.invalid);
  });
  test('unit must be accepted for the field', () {
    expect(SoilValidator.check('nitrogen', '280', 'lb/acre', null).status, FieldStatus.invalid);
    expect(SoilValidator.check('ph', '6.8', 'kg/ha', null).status, FieldStatus.invalid);
  });
  test('phosphorus method: unknown is uncertain, Olsen valid, other invalid', () {
    expect(SoilValidator.check('phosphorus', '18', 'kg/ha', null).status, FieldStatus.uncertain);
    expect(SoilValidator.check('phosphorus', '18', 'kg/ha', 'Olsen').status, FieldStatus.valid);
    expect(SoilValidator.check('phosphorus', '18', 'kg/ha', 'Mehlich').status, FieldStatus.invalid);
  });
  test('confirm gate', () {
    expect(canConfirm([d('nitrogen', '280'), d('ph', '6.8')]), isTrue);
    expect(canConfirm([d('nitrogen', '280'), d('ph', '16')]), isFalse);
    expect(canConfirm([d('nitrogen', ''), d('ph', '')]), isFalse);
    final rejected = d('ph', '16')..action = 'reject';
    expect(canConfirm([d('nitrogen', '280'), rejected]), isTrue);
  });
  test('missing stays missing and rejected is sent as reject', () {
    expect(d('ec', '').toConfirmJson(), isNull);
    expect((d('ec', '0.4')..action = 'reject').toConfirmJson(), {'action': 'reject'});
  });
  test('draft from server json keeps OCR value and null confidence', () {
    final x = FieldDraft.fromJson({'field': 'nitrogen', 'ocr_value': '280', 'value': 280.0, 'unit': 'kg/ha', 'status': 'valid', 'ocr_confidence': null});
    expect(x.ocrValue, '280');
    expect(x.valueText, '280');
    expect(x.ocrConfidence, isNull);
  });
}
