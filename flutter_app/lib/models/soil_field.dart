/// Field metadata + client-side validation. The SERVER re-validates everything; this only gives instant feedback.
enum FieldStatus { missing, invalid, uncertain, valid }

FieldStatus statusFrom(String? s) =>
    FieldStatus.values.firstWhere((e) => e.name == s, orElse: () => FieldStatus.uncertain);

class FieldSpec {
  final String key, label;
  final List<String?> units; // null entry == "no unit" (pH)
  final double hardMin, hardMax;
  final bool primary;
  const FieldSpec(this.key, this.label, this.units, this.hardMin, this.hardMax, {this.primary = false});
}

const fieldSpecs = <FieldSpec>[
  FieldSpec('nitrogen', 'Nitrogen (N)', ['kg/ha', 'mg/kg'], 0, 5000, primary: true),
  FieldSpec('phosphorus', 'Phosphorus (P)', ['kg/ha', 'mg/kg'], 0, 2000, primary: true),
  FieldSpec('potassium', 'Potassium (K)', ['kg/ha', 'mg/kg'], 0, 5000, primary: true),
  FieldSpec('ph', 'pH', [null], 0, 14, primary: true),
  FieldSpec('organic_carbon', 'Organic Carbon (OC)', ['%'], 0, 60, primary: true),
  FieldSpec('ec', 'Electrical Conductivity (EC)', ['dS/m'], 0, 60),
  FieldSpec('sulphur', 'Sulphur (S)', ['mg/kg'], 0, 5000),
  FieldSpec('zinc', 'Zinc (Zn)', ['mg/kg'], 0, 1000),
  FieldSpec('iron', 'Iron (Fe)', ['mg/kg'], 0, 5000),
  FieldSpec('manganese', 'Manganese (Mn)', ['mg/kg'], 0, 2000),
  FieldSpec('copper', 'Copper (Cu)', ['mg/kg'], 0, 1000),
  FieldSpec('boron', 'Boron (B)', ['mg/kg'], 0, 200),
];

FieldSpec specFor(String key) => fieldSpecs.firstWhere((s) => s.key == key);

class CheckResult {
  final FieldStatus status;
  final String? message;
  const CheckResult(this.status, [this.message]);
  bool get blocksConfirm => status == FieldStatus.invalid;
}

class SoilValidator {
  /// Empty text => missing (allowed). Anything else must be a finite number inside the physical range,
  /// with an accepted unit; phosphorus method must be Olsen/Bray/null.
  static CheckResult check(String key, String? valueText, String? unit, String? method) {
    final spec = specFor(key);
    final t = valueText?.trim() ?? '';
    if (t.isEmpty) return const CheckResult(FieldStatus.missing);
    final v = double.tryParse(t);
    if (v == null || v.isNaN || v.isInfinite) {
      return CheckResult(FieldStatus.invalid, "'$t' is not a valid number.");
    }
    if (!spec.units.contains(unit)) {
      return CheckResult(FieldStatus.invalid, key == 'ph' ? 'pH has no unit.' : 'Please choose a unit for ${spec.label}.');
    }
    if (v < spec.hardMin || v > spec.hardMax) {
      return CheckResult(FieldStatus.invalid, '${spec.label} must be between ${spec.hardMin} and ${spec.hardMax}.');
    }
    if (key == 'phosphorus' && method != null && method != 'Olsen' && method != 'Bray') {
      return const CheckResult(FieldStatus.invalid, 'Phosphorus method must be Olsen or Bray.');
    }
    if (key == 'phosphorus' && method == null) {
      return const CheckResult(FieldStatus.uncertain, 'Phosphorus method (Olsen / Bray) unknown - status cannot be classified.');
    }
    return const CheckResult(FieldStatus.valid);
  }
}

/// One editable card's state on the verify screen.
class FieldDraft {
  final String key;
  final String? ocrValue;        // exactly what OCR read (null if not found)
  String valueText;              // what the farmer sees / edits
  String? unit;
  String? method;
  double? ocrConfidence;         // null when the engine gave none - never fabricated
  List<String> serverMessages;
  String action;                 // accept | edit | reject | manual
  FieldStatus serverStatus;

  FieldDraft({required this.key, this.ocrValue, required this.valueText, this.unit, this.method, this.ocrConfidence,
      this.serverMessages = const [], this.action = 'accept', this.serverStatus = FieldStatus.missing});

  factory FieldDraft.fromJson(Map<String, dynamic> j) {
    final v = j['value'];
    return FieldDraft(
      key: j['field'] as String,
      ocrValue: j['ocr_value']?.toString(),
      valueText: v == null ? '' : _trimNum(v),
      unit: j['unit'] as String?,
      method: j['test_method'] as String?,
      ocrConfidence: (j['ocr_confidence'] as num?)?.toDouble(),
      serverStatus: statusFrom(j['status'] as String?),
      serverMessages: ((j['issues'] as List?) ?? []).map((i) => (i as Map)['message'].toString()).toList(),
    );
  }

  factory FieldDraft.empty(FieldSpec s) =>
      FieldDraft(key: s.key, valueText: '', unit: s.units.first, action: 'manual');

  CheckResult get check => SoilValidator.check(key, valueText, unit, method);
  bool get isRejected => action == 'reject';

  Map<String, dynamic>? toConfirmJson() {
    if (isRejected) return {'action': 'reject'};
    if (valueText.trim().isEmpty) return null; // missing stays missing - never invented
    return {'value': double.tryParse(valueText.trim()) ?? valueText.trim(), 'unit': unit, 'test_method': method, 'action': action};
  }
}

String _trimNum(Object v) {
  final d = (v as num).toDouble();
  return d == d.roundToDouble() ? d.toInt().toString() : d.toString();
}

/// Confirm gate: no shown field may be invalid, and at least one value must exist.
bool canConfirm(List<FieldDraft> drafts) {
  final live = drafts.where((d) => !d.isRejected);
  if (live.any((d) => d.check.blocksConfirm)) return false;
  return live.any((d) => d.check.status != FieldStatus.missing);
}
