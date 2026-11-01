import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Runtime / compile-time configuration.
///
/// Priority for [baseUrl]:
/// 1. `--dart-define=API_BASE_URL=...`
/// 2. `.env` → `API_BASE_URL`
/// 3. `http://127.0.0.1:8000` (Windows / Chrome / iOS simulator / desktop)
///
/// Android emulator cannot reach the host via 127.0.0.1.
/// Use `http://10.0.2.2:8000` instead (dart-define or .env).
class AppConfig {
  static const defaultDeviceId = 'BIN_EDGE_AI_001';

  static const _defineBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static const _defineUseMock = bool.fromEnvironment(
    'USE_MOCK',
    defaultValue: false,
  );

  static String get baseUrl {
    if (_defineBaseUrl.isNotEmpty) return _stripSlash(_defineBaseUrl);
    final fromDotenv = dotenv.maybeGet('API_BASE_URL');
    if (fromDotenv != null && fromDotenv.isNotEmpty) {
      return _stripSlash(fromDotenv);
    }
    return 'http://127.0.0.1:8000';
  }

  /// Default **false** so the app talks to the real backend.
  /// Flip via `--dart-define=USE_MOCK=true` or `.env` `USE_MOCK=true`.
  static bool get useMockData {
    if (_defineUseMock) return true;
    final raw = dotenv.maybeGet('USE_MOCK');
    if (raw == null) return false;
    return raw.toLowerCase() == 'true' || raw == '1';
  }

  static String _stripSlash(String value) {
    if (value.endsWith('/')) {
      return value.substring(0, value.length - 1);
    }
    return value;
  }
}
