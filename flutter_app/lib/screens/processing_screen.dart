import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/soil_api.dart';
import 'upload_screen.dart';
import 'verify_screen.dart';

/// SCREEN 2 - OCR Processing
class ProcessingScreen extends StatefulWidget {
  final Uint8List bytes;
  final String filename;
  final ProfileCallback onValidatedProfile;
  const ProcessingScreen({super.key, required this.bytes, required this.filename, required this.onValidatedProfile});
  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  final _api = SoilApi();
  String? _error;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    setState(() => _error = null);
    try {
      final up = await _api.upload(widget.bytes, widget.filename);
      final ocr = await _api.ocr(up['document_id'] as String);
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => VerifyScreen(ocr: ocr, onValidatedProfile: widget.onValidatedProfile)));
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Reading report')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: _error == null
                ? const Column(mainAxisSize: MainAxisSize.min, children: [CircularProgressIndicator(), SizedBox(height: 20), Text('Reading your soil report...')])
                : Column(mainAxisSize: MainAxisSize.min, children: [
                    const Icon(Icons.error_outline, size: 48),
                    const SizedBox(height: 12),
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 20),
                    FilledButton(onPressed: _run, child: const Text('Try again')),
                    const SizedBox(height: 8),
                    OutlinedButton(
                      onPressed: () => Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => VerifyScreen(ocr: null, onValidatedProfile: widget.onValidatedProfile))),
                      child: const Text('Enter values manually'),
                    ),
                  ]),
          ),
        ),
      );
}
