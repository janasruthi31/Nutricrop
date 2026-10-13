import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiError implements Exception {
  final String code, message;
  final int status;
  final Map<String, dynamic> details;
  ApiError(this.code, this.message, this.status, [this.details = const {}]);
  @override
  String toString() => message;
}

class SoilApi {
  final http.Client _c;
  SoilApi([http.Client? c]) : _c = c ?? http.Client();

  Map<String, String> get _h => {
        'X-Farmer-Id': AppConfig.farmerId,
        if (AppConfig.apiKey.isNotEmpty) 'X-API-Key': AppConfig.apiKey,
      };

  Map<String, dynamic> _decode(http.Response r) {
    Map<String, dynamic> body;
    try {
      body = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    } catch (_) {
      throw ApiError('SERVER_ERROR', 'The server returned an unexpected response. Please try again.', r.statusCode);
    }
    if (r.statusCode >= 400) {
      final e = (body['error'] as Map?)?.cast<String, dynamic>() ?? {};
      throw ApiError(e['code']?.toString() ?? 'SERVER_ERROR', e['message']?.toString() ?? 'Something went wrong. Please try again.',
          r.statusCode, (e['details'] as Map?)?.cast<String, dynamic>() ?? {});
    }
    return body;
  }

  Future<T> _guard<T>(Future<T> Function() f) async {
    try {
      return await f().timeout(const Duration(seconds: 90));
    } on ApiError {
      rethrow;
    } catch (_) {
      throw ApiError('NETWORK', 'Could not reach the server. Check your connection, or enter the values manually.', 0);
    }
  }

  Future<Map<String, dynamic>> upload(Uint8List bytes, String filename) => _guard(() async {
        if (bytes.length > AppConfig.maxUploadBytes) {
          throw ApiError('FILE_TOO_LARGE', 'File is larger than 10 MB.', 413);
        }
        final req = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiBase}/api/soil/upload'))
          ..headers.addAll(_h)
          ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
        return _decode(await http.Response.fromStream(await _c.send(req)));
      });

  Future<Map<String, dynamic>> _postJson(String path, Map<String, dynamic> body) => _guard(() async => _decode(await _c.post(
      Uri.parse('${AppConfig.apiBase}$path'), headers: {..._h, 'Content-Type': 'application/json'}, body: jsonEncode(body))));

  Future<Map<String, dynamic>> ocr(String documentId) => _postJson('/api/soil/ocr', {'document_id': documentId});
  Future<Map<String, dynamic>> validate(Map<String, dynamic> body) => _postJson('/api/soil/validate', body);
  Future<Map<String, dynamic>> confirm(Map<String, dynamic> body) => _postJson('/api/soil/confirm', body);
  Future<Map<String, dynamic>> getProfile(String id) =>
      _guard(() async => _decode(await _c.get(Uri.parse('${AppConfig.apiBase}/api/soil/$id'), headers: _h)));
}
