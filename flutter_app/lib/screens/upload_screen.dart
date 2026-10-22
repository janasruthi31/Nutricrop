import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../config.dart';
import '../l10n/app_localizations.dart';
import 'processing_screen.dart';
import 'verify_screen.dart';

typedef ProfileCallback = void Function(Map<String, dynamic> validatedProfile);

/// SCREEN 1 - Soil Report Upload
class UploadScreen extends StatelessWidget {
  final ProfileCallback onValidatedProfile;
  const UploadScreen({super.key, required this.onValidatedProfile});

  void _snack(BuildContext c, String m) => ScaffoldMessenger.of(c).showSnackBar(SnackBar(content: Text(m)));

  Future<void> _go(BuildContext context, Uint8List? bytes, String name) async {
    if (bytes == null) return _snack(context, 'Could not read the selected file.');
    if (bytes.length > AppConfig.maxUploadBytes) return _snack(context, 'File is larger than 10 MB.');
    await Navigator.push(context, MaterialPageRoute(builder: (_) => ProcessingScreen(bytes: bytes, filename: name, onValidatedProfile: onValidatedProfile)));
  }

  Future<void> _pickFile(BuildContext context, List<String> ext) async {
    final r = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ext, withData: true);
    if (r == null || r.files.isEmpty || !context.mounted) return;
    final f = r.files.single;
    await _go(context, f.bytes, f.name);
  }

  Future<void> _camera(BuildContext context) async {
    final x = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 92, maxWidth: 3000);
    if (x == null || !context.mounted) return;
    final bytes = await x.readAsBytes();
    if (!context.mounted) return;
    await _go(context, bytes, x.name);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('soil_reports'))),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        Text(l10n.text('upload_soil_title'), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        Text(l10n.text('upload_instruction'), style: const TextStyle(color: Colors.grey)),
        const SizedBox(height: 20),
        FilledButton.icon(onPressed: () => _pickFile(context, ['pdf']), icon: const Icon(Icons.picture_as_pdf), label: Text(l10n.text('upload_pdf'))),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: () => _pickFile(context, ['jpg', 'jpeg', 'png']), icon: const Icon(Icons.image), label: Text(l10n.text('upload_image'))),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: () => _camera(context), icon: const Icon(Icons.photo_camera), label: Text(l10n.text('take_photo'))),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => VerifyScreen(ocr: null, onValidatedProfile: onValidatedProfile))),
          icon: const Icon(Icons.edit_note),
          label: Text(l10n.text('manual_entry')),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () {
            onValidatedProfile({
              'no_soil_test': true,
              'recommendation_type': 'GENERAL_BLANKET',
              'confidence': 'lower',
              'confidence_label': 'General recommendation (lower confidence)',
              'crop': 'Rice',
              'district': 'Thanjavur',
              'warnings': [
                'No soil test card provided. Using official TNAU blanket recommendation. For higher yield and fertilizer savings, we recommend getting your soil tested at your nearest Agricultural Extension Center (AEC).'
              ]
            });
          },
          icon: const Icon(Icons.grass_rounded, color: Color(0xFF00796B)),
          style: OutlinedButton.styleFrom(
            foregroundColor: const Color(0xFF00796B),
            side: const BorderSide(color: Color(0xFF00796B)),
          ),
          label: const Text('No Soil Test Card? (General Blanket Dose)'),
        ),
      ]),
    );
  }
}
