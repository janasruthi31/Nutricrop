import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart';

class ApiException implements Exception {
  final String code;
  final String message;
  final int statusCode;
  ApiException(this.code, this.message, [this.statusCode = 0]);
  @override
  String toString() => message;
}

class ApiClient {
  static final ApiClient instance = ApiClient._();
  ApiClient._();

  final http.Client _client = http.Client();
  String? _authToken;
  String _farmerId = AppConfig.farmerId;
  Map<String, dynamic>? _currentUser;
  bool _initialized = false;

  String get farmerId => _farmerId;
  String? get authToken => _authToken;
  Map<String, dynamic>? get currentUser => _currentUser;

  Future<void> init() async {
    if (_initialized) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      _authToken = prefs.getString('agri_auth_token');
      _farmerId = prefs.getString('agri_farmer_id') ?? AppConfig.farmerId;
      final userJson = prefs.getString('agri_current_user');
      if (userJson != null) {
        _currentUser = jsonDecode(userJson) as Map<String, dynamic>;
      }
      _initialized = true;
    } catch (_) {}
  }

  void setSession(String token, String farmerId, [Map<String, dynamic>? user]) {
    _authToken = token;
    _farmerId = farmerId;
    _currentUser = user;
    SharedPreferences.getInstance().then((prefs) {
      prefs.setString('agri_auth_token', token);
      prefs.setString('agri_farmer_id', farmerId);
      if (user != null) {
        prefs.setString('agri_current_user', jsonEncode(user));
      }
    }).catchError((_) {});
  }

  void clearSession() {
    _authToken = null;
    _farmerId = 'farmer_001';
    _currentUser = null;
    SharedPreferences.getInstance().then((prefs) {
      prefs.remove('agri_auth_token');
      prefs.remove('agri_farmer_id');
      prefs.remove('agri_current_user');
    }).catchError((_) {});
  }

  // Offline Caching for Saved Recommendations
  Future<void> cacheOfflineRecommendation(Map<String, dynamic> rec) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final list = prefs.getStringList('agri_offline_recommendations') ?? [];
      final recWithMeta = {
        ...rec,
        '_cached_at': DateTime.now().toIso8601String(),
        '_is_offline': true,
      };
      list.insert(0, jsonEncode(recWithMeta));
      if (list.length > 25) list.removeRange(25, list.length);
      await prefs.setStringList('agri_offline_recommendations', list);
    } catch (_) {}
  }

  Future<List<Map<String, dynamic>>> getOfflineRecommendations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final list = prefs.getStringList('agri_offline_recommendations') ?? [];
      return list.map((s) => jsonDecode(s) as Map<String, dynamic>).toList();
    } catch (_) {
      return [];
    }
  }

  Map<String, String> get _headers => {
        'Accept': 'application/json',
        'X-Farmer-Id': _farmerId,
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
        if (AppConfig.apiKey.isNotEmpty) 'X-API-Key': AppConfig.apiKey,
      };

  Map<String, dynamic> _decode(http.Response r) {
    Map<String, dynamic> body;
    try {
      body = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    } catch (_) {
      throw ApiException('SERVER_ERROR', 'The server returned an unexpected response.', r.statusCode);
    }
    if (r.statusCode >= 400) {
      final msg = body['detail'] ?? (body['error'] as Map?)?['message'] ?? 'Something went wrong.';
      final code = (body['error'] as Map?)?['code'] ?? 'ERROR_${r.statusCode}';
      throw ApiException(code.toString(), msg.toString(), r.statusCode);
    }
    return body;
  }

  Future<T> _guard<T>(Future<T> Function() f) async {
    try {
      return await f().timeout(const Duration(seconds: 45));
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('NETWORK', 'Could not reach server. Please check connection and try again.');
    }
  }

  Future<Map<String, dynamic>> checkHealth() =>
      _guard(() async {
        final res = await _client.get(
          Uri.parse('${AppConfig.apiBase}/health'),
          headers: _headers,
        );
        return _decode(res);
      });

  // --------------------------------------------------------------------------
  // Authentication
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
    String? district,
    String preferredLanguage = 'ta',
  }) =>
      _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/auth/register'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode({
            'email': email,
            'password': password,
            'full_name': fullName,
            'phone': phone,
            'district': district,
            'preferred_language': preferredLanguage,
          }),
        );
        final data = _decode(res);
        setSession(data['token'], data['user_id'], data);
        return data;
      });

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) =>
      _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/auth/login'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'password': password}),
        );
        final data = _decode(res);
        setSession(data['token'], data['user_id'], data);
        return data;
      });

  Future<Map<String, dynamic>> forgotPassword(String email) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/auth/forgot-password'),
          headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
          body: jsonEncode({'email': email}),
        );
        return _decode(res);
      });

  Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String resetToken,
    required String newPassword,
  }) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/auth/reset-password'),
          headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
          body: jsonEncode({
            'email': email,
            'reset_token': resetToken,
            'new_password': newPassword,
          }),
        );
        return _decode(res);
      });

  Future<Map<String, dynamic>> getProfile() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/auth/profile'), headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> body) => _guard(() async {
        final res = await _client.put(
          Uri.parse('${AppConfig.apiBase}/api/auth/profile'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(body),
        );
        return _decode(res);
      });

  // --------------------------------------------------------------------------
  // Soil Reports & OCR
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> uploadSoilReport(Uint8List bytes, String filename) => _guard(() async {
        if (bytes.length > AppConfig.maxUploadBytes) {
          throw ApiException('FILE_TOO_LARGE', 'File is larger than 10 MB.', 413);
        }
        final req = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiBase}/api/soil/upload'))
          ..headers.addAll(_headers)
          ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
        return _decode(await http.Response.fromStream(await _client.send(req)));
      });

  Future<Map<String, dynamic>> ocrSoilReport(String documentId) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/soil/ocr'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode({'document_id': documentId}),
        );
        return _decode(res);
      });

  Future<Map<String, dynamic>> validateSoilValues(Map<String, dynamic> body) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/soil/validate'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(body),
        );
        return _decode(res);
      });

  Future<Map<String, dynamic>> confirmSoilValues(Map<String, dynamic> body) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/soil/confirm'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(body),
        );
        return _decode(res);
      });

  // --------------------------------------------------------------------------
  // Farm & Previous Fertilizer Details
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> getFarmDetails() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/farmer/farm'), headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> saveFarmDetails(Map<String, dynamic> farm) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/farmer/farm'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(farm),
        );
        return _decode(res);
      });

  Future<List<dynamic>> getFertilizerHistory() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/farmer/fertilizer-history'), headers: _headers);
        final list = jsonDecode(utf8.decode(res.bodyBytes));
        return list is List ? list : [];
      });

  Future<Map<String, dynamic>> addFertilizerHistory(Map<String, dynamic> item) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/farmer/fertilizer-history'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(item),
        );
        return _decode(res);
      });

  Future<void> deleteFertilizerHistory(String id) => _guard(() async {
        await _client.delete(Uri.parse('${AppConfig.apiBase}/api/farmer/fertilizer-history/$id'), headers: _headers);
      });

  // --------------------------------------------------------------------------
  // Agronomy, NPK, Optimization & Master Recommendation
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> getFullRecommendation(Map<String, dynamic> payload) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/full-recommendation'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        );
        return _decode(res);
      });

  Future<Map<String, dynamic>> saveRecommendation(Map<String, dynamic> payload) => _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/recommendations'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        );
        return _decode(res);
      });

  Future<List<dynamic>> listRecommendations() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/recommendations'), headers: _headers);
        final list = jsonDecode(utf8.decode(res.bodyBytes));
        return list is List ? list : [];
      });

  Future<Map<String, dynamic>> getRecommendationDetails(String id) => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/recommendations/$id'), headers: _headers);
        return _decode(res);
      });

  Future<Uint8List> downloadRecommendationPdf(String id) => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/recommendations/$id/pdf'), headers: _headers);
        if (res.statusCode >= 400) {
          throw ApiException('DOWNLOAD_ERROR', 'Failed to generate PDF report.');
        }
        return res.bodyBytes;
      });

  // --------------------------------------------------------------------------
  // Crop Yield Prediction (ML Benchmark)
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> getYieldMeta() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/yield/meta'), headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> predictYield({
    required String district,
    required String crop,
    String season = 'Kharif',
    int year = 2024,
    double rainSwm = 330.0,
    double rainNem = 640.0,
    double rainWinter = 40.0,
    double rainHot = 150.0,
    double rainAnnual = 1160.0,
  }) =>
      _guard(() async {
        final res = await _client.post(
          Uri.parse('${AppConfig.apiBase}/api/yield/predict'),
          headers: {..._headers, 'Content-Type': 'application/json'},
          body: jsonEncode({
            'district': district,
            'crop': crop,
            'season': season,
            'year': year,
            'rain_swm': rainSwm,
            'rain_nem': rainNem,
            'rain_winter': rainWinter,
            'rain_hot': rainHot,
            'rain_annual': rainAnnual,
          }),
        );
        return _decode(res);
      });

  // --------------------------------------------------------------------------
  // Weather Guidance & Location
  // --------------------------------------------------------------------------
  Future<Map<String, dynamic>> getWeatherGuidance([String? district, double? lat, double? lon]) => _guard(() async {
        final queryParams = <String, String>{};
        if (district != null) queryParams['district'] = district;
        if (lat != null) queryParams['lat'] = lat.toString();
        if (lon != null) queryParams['lon'] = lon.toString();
        final uri = Uri.parse('${AppConfig.apiBase}/api/weather/guidance').replace(
          queryParameters: queryParams.isNotEmpty ? queryParams : null,
        );
        final res = await _client.get(uri, headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> getLiveWeatherCurrent({String? district, double? lat, double? lon}) => _guard(() async {
        final queryParams = <String, String>{};
        if (district != null) queryParams['district'] = district;
        if (lat != null) queryParams['lat'] = lat.toString();
        if (lon != null) queryParams['lon'] = lon.toString();
        final uri = Uri.parse('${AppConfig.apiBase}/api/weather/current').replace(
          queryParameters: queryParams.isNotEmpty ? queryParams : null,
        );
        final res = await _client.get(uri, headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> getLiveWeatherForecast({String? district, double? lat, double? lon}) => _guard(() async {
        final queryParams = <String, String>{};
        if (district != null) queryParams['district'] = district;
        if (lat != null) queryParams['lat'] = lat.toString();
        if (lon != null) queryParams['lon'] = lon.toString();
        final uri = Uri.parse('${AppConfig.apiBase}/api/weather/forecast').replace(
          queryParameters: queryParams.isNotEmpty ? queryParams : null,
        );
        final res = await _client.get(uri, headers: _headers);
        return _decode(res);
      });

  Future<Map<String, dynamic>> reverseGeocode({required double lat, required double lon}) => _guard(() async {
        final uri = Uri.parse('${AppConfig.apiBase}/api/location/reverse-geocode').replace(
          queryParameters: {'lat': lat.toString(), 'lon': lon.toString()},
        );
        final res = await _client.get(uri, headers: _headers);
        return _decode(res);
      });

  Future<List<dynamic>> getFertilizerPrices() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/fertilizer/prices'), headers: _headers);
        final list = jsonDecode(utf8.decode(res.bodyBytes));
        return list is List ? list : [];
      });

  // --------------------------------------------------------------------------
  // Notifications
  // --------------------------------------------------------------------------
  Future<List<dynamic>> getNotifications() => _guard(() async {
        final res = await _client.get(Uri.parse('${AppConfig.apiBase}/api/notifications'), headers: _headers);
        final list = jsonDecode(utf8.decode(res.bodyBytes));
        return list is List ? list : [];
      });

  Future<void> markNotificationRead(String id) => _guard(() async {
        await _client.post(Uri.parse('${AppConfig.apiBase}/api/notifications/$id/read'), headers: _headers);
      });
}
