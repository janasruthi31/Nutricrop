import 'package:flutter/material.dart';
import 'upload_screen.dart';

/// SCREEN 4 - Validation Result. The button hands the VALIDATED profile to Phase 4 (no fertilizer logic here).
class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> profile;
  final ProfileCallback onValidatedProfile;
  const ResultScreen({super.key, required this.profile, required this.onValidatedProfile});

  @override
  Widget build(BuildContext context) {
    final ready = (profile['phase4_readiness'] as Map?)?['ready'] == true;
    final missing = ((profile['missing_primary'] as List?) ?? []).cast<String>();
    final status = (profile['soil_status'] as Map?)?.cast<String, dynamic>() ?? {};
    return Scaffold(
      appBar: AppBar(title: const Text('Validation Result'), automaticallyImplyLeading: false),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const ListTile(leading: Icon(Icons.check_circle, color: Colors.green), title: Text('Soil report processed')),
        const ListTile(leading: Icon(Icons.check_circle, color: Colors.green), title: Text('Values confirmed by you and validated')),
        const ListTile(leading: Icon(Icons.check_circle, color: Colors.green), title: Text('Units verified')),
        if (missing.isNotEmpty) ListTile(leading: const Icon(Icons.info_outline, color: Colors.orange), title: Text('Not provided: ${missing.join(', ')}')),
        const Divider(),
        const Text('Soil status (TNAU ratings)', style: TextStyle(fontWeight: FontWeight.w600)),
        for (final e in status.entries) Text('${e.key}: ${e.value ?? 'not classified'}'),
        const SizedBox(height: 6),
        const Text('These are soil-status classes only, not fertilizer advice.', style: TextStyle(fontSize: 12)),
        if (!ready) const Padding(padding: EdgeInsets.only(top: 12), child: Text('Some values needed for recommendations are missing or incomplete (e.g. N, P, K or the phosphorus method).', style: TextStyle(color: Colors.orange))),
        const SizedBox(height: 20),
        FilledButton(onPressed: () => onValidatedProfile(profile), child: const Text('Continue to Fertilizer Recommendation')),
      ]),
    );
  }
}
