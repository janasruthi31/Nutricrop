import 'package:flutter/material.dart';
import '../models/soil_field.dart';
import '../services/soil_api.dart';
import 'result_screen.dart';
import 'upload_screen.dart';

/// SCREEN 3 - Verify Soil Values. `ocr == null` means manual entry.
class VerifyScreen extends StatefulWidget {
  final Map<String, dynamic>? ocr;
  final ProfileCallback onValidatedProfile;
  const VerifyScreen({super.key, required this.ocr, required this.onValidatedProfile});
  @override
  State<VerifyScreen> createState() => _VerifyScreenState();
}

class _VerifyScreenState extends State<VerifyScreen> {
  final _api = SoilApi();
  late final List<FieldDraft> _drafts;
  final _district = TextEditingController(), _village = TextEditingController(), _sample = TextEditingController(), _date = TextEditingController();
  bool _busy = false, _ack = false;
  String? _error;

  bool get _manual => widget.ocr == null;

  @override
  void initState() {
    super.initState();
    if (_manual) {
      _drafts = fieldSpecs.map(FieldDraft.empty).toList();
    } else {
      final byKey = {for (final f in (widget.ocr!['fields'] as List)) (f as Map)['field'] as String: FieldDraft.fromJson(f.cast<String, dynamic>())};
      _drafts = fieldSpecs.map((s) => byKey[s.key] ?? FieldDraft.empty(s)).toList();
      final m = (widget.ocr!['metadata'] as Map?)?.cast<String, dynamic>() ?? {};
      _district.text = m['district']?.toString() ?? '';
      _village.text = m['village']?.toString() ?? '';
      _sample.text = m['sample_id']?.toString() ?? '';
      _date.text = m['test_date']?.toString() ?? '';
    }
  }

  Future<void> _edit(FieldDraft d) async {
    final spec = specFor(d.key);
    final ctrl = TextEditingController(text: d.valueText);
    String? unit = d.unit ?? spec.units.first;
    String? method = d.method;
    final result = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(builder: (ctx, setS) {
        final chk = SoilValidator.check(d.key, ctrl.text, unit, method);
        return Padding(
          padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.of(ctx).viewInsets.bottom),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(spec.label, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            if (d.ocrValue != null) Text('OCR read: ${d.ocrValue}'),
            const SizedBox(height: 12),
            TextField(controller: ctrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), onChanged: (_) => setS(() {}),
                decoration: InputDecoration(labelText: 'Value', errorText: chk.status == FieldStatus.invalid ? chk.message : null)),
            if (spec.units.length > 1 || spec.units.first != null)
              DropdownButtonFormField<String?>(
                value: spec.units.contains(unit) ? unit : spec.units.first,
                decoration: const InputDecoration(labelText: 'Unit'),
                items: spec.units.toSet().map((u) => DropdownMenuItem(value: u, child: Text(u ?? '-'))).toList(),
                onChanged: (v) => setS(() => unit = v),
              ),
            if (d.key == 'phosphorus')
              DropdownButtonFormField<String?>(
                value: (method == 'Olsen' || method == 'Bray') ? method : null,
                decoration: const InputDecoration(labelText: 'Test method'),
                items: const [
                  DropdownMenuItem(value: null, child: Text('Not known')),
                  DropdownMenuItem(value: 'Olsen', child: Text('Olsen')),
                  DropdownMenuItem(value: 'Bray', child: Text('Bray')),
                ],
                onChanged: (v) => setS(() => method = v),
              ),
            const SizedBox(height: 16),
            Row(children: [
              TextButton(onPressed: () => Navigator.pop(ctx, 'reject'), child: const Text('Reject value')),
              const Spacer(),
              FilledButton(onPressed: chk.blocksConfirm ? null : () => Navigator.pop(ctx, 'save'), child: const Text('Save')),
            ]),
          ]),
        );
      }),
    );
    if (result == null) return;
    setState(() {
      if (result == 'reject') {
        d.action = 'reject';
        d.valueText = '';
      } else {
        d.valueText = ctrl.text.trim();
        d.unit = unit;
        d.method = method;
        d.action = (_manual || d.ocrValue == null) ? 'manual' : 'edit';
      }
    });
  }

  Future<void> _confirm() async {
    setState(() { _busy = true; _error = null; });
    final fields = <String, dynamic>{};
    for (final d in _drafts) {
      final j = d.toConfirmJson();
      if (j != null) fields[d.key] = j;
    }
    String? testDate = _date.text.trim().isEmpty ? null : _date.text.trim();
    if (testDate != null) {
      final parts = testDate.split(RegExp(r'[/.-]'));
      if (parts.length == 3) {
        if (parts[0].length == 4) {
          testDate = '${parts[0]}-${parts[1].padLeft(2, '0')}-${parts[2].padLeft(2, '0')}';
        } else if (parts[2].length == 4) {
          testDate = '${parts[2]}-${parts[1].padLeft(2, '0')}-${parts[0].padLeft(2, '0')}';
        }
      }
    }
    try {
      final res = await _api.confirm({
        if (!_manual) 'document_id': widget.ocr!['document_id'],
        'fields': fields,
        'district': _district.text.trim().isEmpty ? null : _district.text.trim(),
        'village': _village.text.trim().isEmpty ? null : _village.text.trim(),
        'sample_id': _sample.text.trim().isEmpty ? null : _sample.text.trim(),
        'test_date': testDate,
        'farmer_confirmed': true,
        'allow_duplicate': true,
      });
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => ResultScreen(profile: (res['soil_profile'] as Map).cast<String, dynamic>(), onValidatedProfile: widget.onValidatedProfile)));
    } on ApiError catch (e) {
      if (e.code == 'DUPLICATE_SUBMISSION') {
        final pid = e.details['soil_profile_id']?.toString();
        if (pid != null) {
          try {
            final profileRes = await _api.getProfile(pid);
            if (!mounted) return;
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (_) => ResultScreen(
                  profile: (profileRes['soil_profile'] is Map ? profileRes['soil_profile'] : profileRes).cast<String, dynamic>(),
                  onValidatedProfile: widget.onValidatedProfile,
                ),
              ),
            );
            return;
          } catch (_) {}
        }
      }
      setState(() => _error = e.code == 'DUPLICATE_SUBMISSION' ? 'This soil report was already confirmed earlier.' : e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Color _color(FieldStatus s) => switch (s) {
        FieldStatus.valid => Colors.green,
        FieldStatus.uncertain => Colors.orange,
        FieldStatus.invalid => Colors.red,
        FieldStatus.missing => Colors.grey,
      };

  Widget _card(FieldDraft d) {
    final spec = specFor(d.key);
    final chk = d.check;
    final shown = d.isRejected ? 'Rejected' : (d.valueText.isEmpty ? 'Not found - tap Edit to enter' : '${d.valueText}${d.unit != null ? ' ${d.unit}' : ''}');
    final status = d.isRejected ? FieldStatus.missing : (chk.status == FieldStatus.valid && d.serverStatus == FieldStatus.uncertain && d.action == 'accept' ? FieldStatus.uncertain : chk.status);
    return Card(
      child: ListTile(
        leading: Icon(Icons.circle, color: _color(status), size: 14),
        title: Text(spec.label),
        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(shown, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
          if (d.key == 'phosphorus' && d.valueText.isNotEmpty) Text(d.method ?? 'Method not known'),
          if (!_manual && d.ocrValue != null) Text('OCR value: ${d.ocrValue}${d.ocrConfidence != null ? '  (confidence ${(d.ocrConfidence! * 100).round()}%)' : ''}', style: const TextStyle(fontSize: 12)),
          if (chk.message != null) Text(chk.message!, style: TextStyle(fontSize: 12, color: _color(chk.status))),
          for (final m in d.serverMessages.take(2)) Text(m, style: const TextStyle(fontSize: 12, color: Colors.orange)),
        ]),
        trailing: TextButton(onPressed: () => _edit(d), child: const Text('Edit')),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final warnings = ((widget.ocr?['warnings'] as List?) ?? []).map((w) => (w as Map)['message'].toString()).toList();
    final invalidFields = _drafts.where((d) => !d.isRejected && d.check.blocksConfirm).toList();
    final ok = canConfirm(_drafts) && (_manual || _ack) && !_busy;
    return Scaffold(
      appBar: AppBar(title: const Text('Review Extracted Soil Information')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (!_manual) Container(
          padding: const EdgeInsets.all(12), margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(color: Colors.amber.shade100, borderRadius: BorderRadius.circular(8)),
          child: const Text('Extracted \u2014 Please Verify', style: TextStyle(fontWeight: FontWeight.w700)),
        ),
        for (final w in warnings) Padding(padding: const EdgeInsets.only(bottom: 6), child: Text('\u26A0 $w', style: const TextStyle(color: Colors.orange))),
        ..._drafts.map(_card),
        const SizedBox(height: 8),
        const Text('Report details', style: TextStyle(fontWeight: FontWeight.w600)),
        TextField(controller: _district, decoration: const InputDecoration(labelText: 'District')),
        TextField(controller: _village, decoration: const InputDecoration(labelText: 'Village')),
        TextField(controller: _sample, decoration: const InputDecoration(labelText: 'Sample ID')),
        TextField(controller: _date, decoration: const InputDecoration(labelText: 'Test date (YYYY-MM-DD)')),
        if (!_manual) CheckboxListTile(value: _ack, onChanged: (v) => setState(() => _ack = v ?? false), controlAffinity: ListTileControlAffinity.leading,
            title: const Text('I have checked these values against my soil report')),
        if (invalidFields.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 8, bottom: 6),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.shade300),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(children: [
                  Icon(Icons.error_outline, color: Colors.red, size: 18),
                  SizedBox(width: 8),
                  Text('Please fix the following to confirm:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red)),
                ]),
                const SizedBox(height: 4),
                for (final d in invalidFields)
                  Padding(
                    padding: const EdgeInsets.only(left: 4, bottom: 2),
                    child: Text('• ${specFor(d.key).label}: ${d.check.message ?? "Invalid value or unit"}',
                        style: const TextStyle(color: Colors.red, fontSize: 13)),
                  ),
              ],
            ),
          ),
        if (!_ack && !_manual && invalidFields.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 6, bottom: 4),
            child: Text('ℹ️ Please tick the checkbox above to confirm you verified these values.',
                style: TextStyle(color: Colors.grey, fontSize: 13, fontStyle: FontStyle.italic)),
          ),
        if (_error != null) ...[
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(_error!, style: const TextStyle(color: Colors.red))),
          if (_error!.contains('already confirmed'))
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: FilledButton.tonalIcon(
                onPressed: () {
                  final profile = _buildProfileFromDrafts();
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ResultScreen(
                        profile: profile,
                        onValidatedProfile: widget.onValidatedProfile,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.arrow_forward_rounded),
                label: const Text('Continue to Recommendations With This Report'),
              ),
            ),
        ],
        const SizedBox(height: 12),
        FilledButton(onPressed: ok ? _confirm : null, child: _busy ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Confirm & Validate')),
      ]),
    );
  }

  Map<String, dynamic> _buildProfileFromDrafts() {
    final fieldsMap = <String, dynamic>{};
    for (final d in _drafts) {
      if (!d.isRejected && d.valueText.isNotEmpty) {
        final val = double.tryParse(d.valueText);
        fieldsMap[d.key] = {
          'value': val,
          'unit': d.unit,
          if (d.method != null) 'method': d.method,
        };
      }
    }
    final m = (widget.ocr?['metadata'] as Map?)?.cast<String, dynamic>() ?? {};
    return {
      'district': _district.text.trim().isNotEmpty ? _district.text.trim() : m['district'],
      'village': _village.text.trim().isNotEmpty ? _village.text.trim() : m['village'],
      'sample_id': _sample.text.trim().isNotEmpty ? _sample.text.trim() : m['sample_id'],
      'test_date': _date.text.trim().isNotEmpty ? _date.text.trim() : m['test_date'],
      'crop': m['crop'] ?? m['recommended_crop'] ?? 'Groundnut',
      'recommended_crop': m['recommended_crop'] ?? m['crop'] ?? 'Groundnut',
      'farm_area': m['farm_area'] ?? 1.0,
      'farm_area_unit': m['farm_area_unit'] ?? 'acre',
      'printed_recommendation': m['printed_recommendation'],
      'phase4_readiness': {'ready': true},
      'missing_primary': <String>[],
      'soil_status': {},
      ...fieldsMap,
    };
  }
}
