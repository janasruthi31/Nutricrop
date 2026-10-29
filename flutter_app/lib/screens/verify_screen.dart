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
  final _name = TextEditingController(), _survey = TextEditingController(), _cropCtrl = TextEditingController(), _farmArea = TextEditingController();
  bool _busy = false, _ack = false;
  String? _error;

  bool get _manual => widget.ocr == null;

  @override
  void dispose() {
    _district.dispose();
    _village.dispose();
    _sample.dispose();
    _date.dispose();
    _name.dispose();
    _survey.dispose();
    _cropCtrl.dispose();
    _farmArea.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    try {
      if (_manual) {
        _drafts = fieldSpecs.map(FieldDraft.empty).toList();
        _cropCtrl.text = 'Groundnut';
        _farmArea.text = '1.0';
      } else {
        final rawFields = widget.ocr?['fields'];
        final Map<String, FieldDraft> byKey = {};
        if (rawFields is List) {
          for (final f in rawFields) {
            if (f is Map) {
              final key = f['field']?.toString();
              if (key != null) {
                byKey[key] = FieldDraft.fromJson(Map<String, dynamic>.from(f));
              }
            }
          }
        } else if (rawFields is Map) {
          for (final entry in rawFields.entries) {
            final key = entry.key.toString();
            if (entry.value is Map) {
              final fMap = Map<String, dynamic>.from(entry.value as Map);
              fMap['field'] = key;
              byKey[key] = FieldDraft.fromJson(fMap);
            }
          }
        }
        _drafts = fieldSpecs.map((s) => byKey[s.key] ?? FieldDraft.empty(s)).toList();
        final m = (widget.ocr?['metadata'] is Map)
            ? Map<String, dynamic>.from(widget.ocr!['metadata'] as Map)
            : <String, dynamic>{};
        final r = (widget.ocr?['review_only'] is Map)
            ? Map<String, dynamic>.from(widget.ocr!['review_only'] as Map)
            : <String, dynamic>{};

        _name.text = r['farmer_name']?.toString() ?? m['farmer_name']?.toString() ?? '';
        _survey.text = r['survey_number']?.toString() ?? m['survey_number']?.toString() ?? '';
        _district.text = m['district']?.toString() ?? '';
        _village.text = m['village']?.toString() ?? '';
        _sample.text = m['sample_id']?.toString() ?? '';
        _date.text = m['test_date']?.toString() ?? '';
        _cropCtrl.text = m['crop']?.toString() ?? m['recommended_crop']?.toString() ?? 'Groundnut';
        _farmArea.text = (m['farm_area']?.toString() ?? '1.0');
      }
    } catch (_) {
      _drafts = fieldSpecs.map(FieldDraft.empty).toList();
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
                decoration: const InputDecoration(
                  labelText: 'Test method',
                  helperText: 'Confirm method from Soil Health Card (Olsen for neutral/alkaline, Bray for acidic). Do not guess.',
                  helperMaxLines: 2,
                ),
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
      final profile = (res['soil_profile'] as Map).cast<String, dynamic>();
      profile['farmer_name'] = _name.text.trim();
      profile['survey_number'] = _survey.text.trim();
      if (_cropCtrl.text.trim().isNotEmpty) {
        profile['crop'] = _cropCtrl.text.trim();
        profile['recommended_crop'] = _cropCtrl.text.trim();
      }
      if (_farmArea.text.trim().isNotEmpty) {
        profile['farm_area'] = double.tryParse(_farmArea.text.trim()) ?? (profile['farm_area'] ?? 1.0);
      }
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => ResultScreen(profile: profile, onValidatedProfile: widget.onValidatedProfile)));
    } on ApiError catch (e) {
      if (e.code == 'DUPLICATE_SUBMISSION') {
        final pid = e.details['soil_profile_id']?.toString();
        if (pid != null) {
          try {
            final profileRes = await _api.getProfile(pid);
            if (!mounted) return;
            final prof = (profileRes['soil_profile'] is Map ? profileRes['soil_profile'] : profileRes).cast<String, dynamic>();
            prof['farmer_name'] = _name.text.trim();
            prof['survey_number'] = _survey.text.trim();
            if (_cropCtrl.text.trim().isNotEmpty) {
              prof['crop'] = _cropCtrl.text.trim();
              prof['recommended_crop'] = _cropCtrl.text.trim();
            }
            if (_farmArea.text.trim().isNotEmpty) {
              prof['farm_area'] = double.tryParse(_farmArea.text.trim()) ?? (prof['farm_area'] ?? 1.0);
            }
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (_) => ResultScreen(
                  profile: prof,
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

  bool get _isTestDateOld {
    final t = _date.text.trim();
    if (t.isEmpty) return false;
    try {
      DateTime? d;
      if (t.contains('-')) {
        d = DateTime.tryParse(t);
      } else if (t.contains('/')) {
        final p = t.split('/');
        if (p.length == 3) {
          if (p[0].length == 4) {
            d = DateTime.tryParse('${p[0]}-${p[1].padLeft(2, '0')}-${p[2].padLeft(2, '0')}');
          } else if (p[2].length == 4) {
            d = DateTime.tryParse('${p[2]}-${p[1].padLeft(2, '0')}-${p[0].padLeft(2, '0')}');
          }
        }
      }
      if (d != null) {
        return DateTime.now().difference(d).inDays > 365;
      }
    } catch (_) {}
    return false;
  }

  Widget _card(FieldDraft d) {
    final spec = specFor(d.key);
    final chk = d.check;
    final shown = d.isRejected ? 'Rejected' : (d.valueText.isEmpty ? 'Not found - tap Edit to enter' : '${d.valueText}${d.unit != null ? ' ${d.unit}' : ''}');
    final status = d.isRejected ? FieldStatus.missing : (chk.status == FieldStatus.valid && d.serverStatus == FieldStatus.uncertain && d.action == 'accept' ? FieldStatus.uncertain : chk.status);

    final conf = d.ocrConfidence;
    final bool isLowConf = !_manual && conf != null &&
        ((conf <= 1.0 && conf < 0.70) || (conf > 1.0 && conf < 70.0));
    final bool isRed = isLowConf || status == FieldStatus.invalid;

    return Card(
      color: isRed ? Colors.red.shade50 : null,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: isRed ? Colors.red.shade700 : (status == FieldStatus.uncertain ? Colors.orange.shade400 : Colors.grey.shade300),
          width: isRed ? 2.0 : 1.0,
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Icon(
              isRed ? Icons.error_outline : Icons.circle,
              color: isRed ? Colors.red.shade700 : _color(status),
              size: 16,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    spec.label,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: isRed ? Colors.red.shade900 : null,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    shown,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: isRed ? Colors.red.shade900 : null,
                    ),
                  ),
                  if (isLowConf)
                    Container(
                      margin: const EdgeInsets.only(top: 4, bottom: 4),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(color: Colors.red.shade100, borderRadius: BorderRadius.circular(4)),
                      child: Text(
                        'Low OCR Confidence (${conf <= 1.0 ? (conf * 100).round() : conf.round()}%) - Please tap Edit to check',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.red.shade900),
                      ),
                    ),
                  if (d.key == 'phosphorus' && d.valueText.isNotEmpty) Text(d.method ?? 'Method not known'),
                  if (!_manual && d.ocrValue != null && !isLowConf)
                    Text('OCR value: ${d.ocrValue}${d.ocrConfidence != null ? ' (confidence ${(d.ocrConfidence! <= 1.0 ? (d.ocrConfidence! * 100).round() : d.ocrConfidence!.round())}%)' : ''}', style: const TextStyle(fontSize: 12)),
                  if (chk.message != null) Text(chk.message!, style: TextStyle(fontSize: 12, color: _color(chk.status))),
                  for (final m in d.serverMessages.take(2)) Text(m, style: const TextStyle(fontSize: 12, color: Colors.orange)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 76,
              height: 36,
              child: OutlinedButton(
                onPressed: () => _edit(d),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: const Size(60, 36),
                  foregroundColor: isRed ? Colors.red.shade700 : null,
                  side: isRed ? BorderSide(color: Colors.red.shade700) : null,
                ),
                child: const Text('Edit'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<String> warnings = [];
    final rawWarn = widget.ocr?['warnings'];
    if (rawWarn is List) {
      for (final w in rawWarn) {
        if (w is Map) {
          final msg = w['message'] ?? w['code'] ?? w.toString();
          warnings.add(msg.toString());
        } else if (w != null) {
          warnings.add(w.toString());
        }
      }
    }
    final invalidFields = _drafts.where((d) => !d.isRejected && d.check.blocksConfirm).toList();
    final ok = canConfirm(_drafts) && (_manual || _ack) && !_busy;
    return Scaffold(
      appBar: AppBar(title: const Text('Review Extracted Soil Information')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (_isTestDateOld)
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              border: Border.all(color: Colors.red.shade700, width: 1.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.history_toggle_off_rounded, color: Colors.red, size: 28),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Soil test date is more than 1 year old (${_date.text}). Soil nutrient fertility fluctuates each season. We strongly recommend testing a fresh soil sample for accurate dosing.',
                    style: TextStyle(color: Colors.red.shade900, fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
        if (!_manual) Container(
          padding: const EdgeInsets.all(12), margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(color: Colors.amber.shade100, borderRadius: BorderRadius.circular(8)),
          child: const Text('Extracted \u2014 Please Verify', style: TextStyle(fontWeight: FontWeight.w700)),
        ),
        for (final w in warnings) Padding(padding: const EdgeInsets.only(bottom: 6), child: Text('\u26A0 $w', style: const TextStyle(color: Colors.orange))),
        ..._drafts.map(_card),
        const SizedBox(height: 12),
        Card(
          elevation: 1.5,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(color: Colors.green.shade200),
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.assignment_ind_outlined, color: Colors.green.shade800, size: 22),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text('Farmer & Card Details (விவரங்கள்)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                const Text('Check or edit the extracted details before confirming:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                const Divider(height: 20),
                TextField(
                  controller: _name,
                  decoration: const InputDecoration(
                    labelText: 'Farmer Name (விவசாயி பெயர்)',
                    prefixIcon: Icon(Icons.person_outline),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _survey,
                  decoration: const InputDecoration(
                    labelText: 'Survey / Patta No. (புல / பட்டா எண்)',
                    prefixIcon: Icon(Icons.pin_drop_outlined),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _cropCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Crop (பயிர்)',
                          prefixIcon: Icon(Icons.grass_outlined),
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _farmArea,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(
                          labelText: 'Area (Acres / ஏக்கர்)',
                          prefixIcon: Icon(Icons.landscape_outlined),
                          isDense: true,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _district,
                        decoration: const InputDecoration(
                          labelText: 'District (மாவட்டம்)',
                          prefixIcon: Icon(Icons.location_city_outlined),
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _village,
                        decoration: const InputDecoration(
                          labelText: 'Village (கிராமம்)',
                          prefixIcon: Icon(Icons.home_outlined),
                          isDense: true,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _sample,
                        decoration: const InputDecoration(
                          labelText: 'Sample ID (மாதிரி எண்)',
                          prefixIcon: Icon(Icons.tag),
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _date,
                        decoration: const InputDecoration(
                          labelText: 'Test Date (YYYY-MM-DD)',
                          prefixIcon: Icon(Icons.calendar_today_outlined),
                          isDense: true,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
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
    final review = (widget.ocr?['review_only'] as Map?)?.cast<String, dynamic>() ?? {};
    return {
      'farmer_name': _name.text.trim().isNotEmpty ? _name.text.trim() : (review['farmer_name'] ?? m['farmer_name'] ?? 'Farmer'),
      'survey_number': _survey.text.trim().isNotEmpty ? _survey.text.trim() : (review['survey_number'] ?? m['survey_number'] ?? ''),
      'district': _district.text.trim().isNotEmpty ? _district.text.trim() : m['district'],
      'village': _village.text.trim().isNotEmpty ? _village.text.trim() : m['village'],
      'sample_id': _sample.text.trim().isNotEmpty ? _sample.text.trim() : m['sample_id'],
      'test_date': _date.text.trim().isNotEmpty ? _date.text.trim() : m['test_date'],
      'crop': _cropCtrl.text.trim().isNotEmpty ? _cropCtrl.text.trim() : (m['crop'] ?? m['recommended_crop'] ?? 'Groundnut'),
      'recommended_crop': _cropCtrl.text.trim().isNotEmpty ? _cropCtrl.text.trim() : (m['recommended_crop'] ?? m['crop'] ?? 'Groundnut'),
      'farm_area': double.tryParse(_farmArea.text.trim()) ?? (m['farm_area'] ?? 1.0),
      'farm_area_unit': m['farm_area_unit'] ?? 'acre',
      'printed_recommendation': m['printed_recommendation'],
      'phase4_readiness': {'ready': true},
      'missing_primary': <String>[],
      'soil_status': {},
      ...fieldsMap,
    };
  }
}
