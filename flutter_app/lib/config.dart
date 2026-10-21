import 'package:flutter/foundation.dart';

/// Backend settings. Override at run time:
///   flutter run -d chrome --dart-define=SOIL_API_BASE=http://127.0.0.1:8000 --dart-define=FARMER_ID=farmer_001
class AppConfig {
  static String? _overrideApiBase;

  static void setApiBase(String newUrl) {
    _overrideApiBase = newUrl.trim().replaceAll(RegExp(r'/+$'), '');
  }

  static String get apiBase {
    if (_overrideApiBase != null && _overrideApiBase!.isNotEmpty) {
      return _overrideApiBase!;
    }
    const envUrl = String.fromEnvironment('SOIL_API_BASE');
    if (envUrl.isNotEmpty) return envUrl;
    if (kIsWeb) return 'http://127.0.0.1:8000';
    return 'http://127.0.0.1:8000'; // Works seamlessly with ADB reverse port forwarding (and local testing)
  }

  static const farmerId = String.fromEnvironment('FARMER_ID', defaultValue: 'farmer_001'); // replace with real auth identity
  static const apiKey = String.fromEnvironment('SOIL_API_KEY', defaultValue: '');
  static const maxUploadBytes = 10 * 1024 * 1024;
}
