import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _tokenKey = 'autobin_access_token';

  final FlutterSecureStorage _storage;
  String? _memoryToken;

  Future<void> saveToken(String token) async {
    _memoryToken = token;
    try {
      await _storage.write(key: _tokenKey, value: token);
    } catch (_) {
      // Desktop/web without platform plugin — keep memory fallback.
    }
  }

  Future<String?> readToken() async {
    if (_memoryToken != null) return _memoryToken;
    try {
      _memoryToken = await _storage.read(key: _tokenKey);
    } catch (_) {
      return _memoryToken;
    }
    return _memoryToken;
  }

  Future<void> clear() async {
    _memoryToken = null;
    try {
      await _storage.delete(key: _tokenKey);
    } catch (_) {}
  }
}
