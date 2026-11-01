import '../../config/app_config.dart';
import '../../core/network/error_handler.dart';
import '../models/alert_model.dart';
import '../models/auth_response.dart';
import '../models/fund_model.dart';
import '../models/history_model.dart';
import '../models/overview_model.dart';
import '../models/user_model.dart';
import 'api_provider.dart';

/// Offline driver that returns the same JSON shape as SHARED_CONTRACT.md.
class MockApiProvider implements AppApi {
  MockApiProvider();

  static const _users = {
    'admin': {
      'password': 'admin123',
      'user': {
        'id': 1,
        'username': 'admin',
        'display_name': 'Quản trị viên',
        'role': 'admin',
      },
    },
    'operator': {
      'password': 'operator123',
      'user': {
        'id': 2,
        'username': 'operator',
        'display_name': 'Vận hành',
        'role': 'operator',
      },
    },
  };

  final List<Map<String, dynamic>> _alerts = [
    {
      'id': 'alt_001',
      'device_id': AppConfig.defaultDeviceId,
      'type': 'BIN_FULL',
      'severity': 'warning',
      'title': 'Thùng nhựa gần đầy',
      'message': 'Ngăn plastic đạt 92% dung tích',
      'is_resolved': false,
      'created_at': '2026-11-01T01:10:00Z',
      'resolved_at': null,
    },
    {
      'id': 'alt_002',
      'device_id': AppConfig.defaultDeviceId,
      'type': 'CAMERA_LOST',
      'severity': 'critical',
      'title': 'Mất tín hiệu camera',
      'message': 'Camera index 0 không trả frame trong 8 giây',
      'is_resolved': false,
      'created_at': '2026-11-01T00:42:00Z',
      'resolved_at': null,
    },
    {
      'id': 'alt_003',
      'device_id': AppConfig.defaultDeviceId,
      'type': 'AI_LOW_CONFIDENCE',
      'severity': 'info',
      'title': 'Độ tin cậy AI thấp',
      'message': 'Nhiều mẫu unknown liên tiếp (confidence < 0.75)',
      'is_resolved': false,
      'created_at': '2026-10-31T22:15:00Z',
      'resolved_at': null,
    },
    {
      'id': 'alt_004',
      'device_id': AppConfig.defaultDeviceId,
      'type': 'SERVO_JAM',
      'severity': 'critical',
      'title': 'Kẹt servo máng xoay',
      'message': 'Servo D10 không đạt góc metal',
      'is_resolved': true,
      'created_at': '2026-10-30T18:00:00Z',
      'resolved_at': '2026-10-30T18:20:00Z',
    },
  ];

  Future<void> _latency() => Future<void>.delayed(const Duration(milliseconds: 420));

  @override
  Future<AuthResponse> login({
    required String username,
    required String password,
  }) async {
    await _latency();
    final record = _users[username];
    if (record == null || record['password'] != password) {
      throw const ApiException('Invalid credentials', statusCode: 401);
    }
    return AuthResponse.fromJson({
      'access_token': 'mock-jwt-$username',
      'token_type': 'bearer',
      'expires_in': 86400,
      'user': record['user'],
    });
  }

  @override
  Future<void> logout() async {
    await _latency();
  }

  final List<Map<String, dynamic>> _history = [];
  Map<String, dynamic> _currentUser = {
    'id': 1,
    'username': 'admin',
    'display_name': 'Quản trị viên',
    'role': 'admin',
    'phone': '',
    'email': '',
    'address': '',
  };
  bool _cleanedOnce = false;

  @override
  Future<UserModel> me() async {
    await _latency();
    return UserModel.fromJson(_currentUser);
  }

  @override
  Future<UserModel> updateProfile({
    required String username,
    String? phone,
    String? email,
    String? address,
    String? displayName,
  }) async {
    await _latency();
    _currentUser = {
      ..._currentUser,
      'username': username,
      'display_name': displayName ?? _currentUser['display_name'],
      'phone': phone,
      'email': email,
      'address': address,
    };
    return UserModel.fromJson(_currentUser);
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _latency();
    if (currentPassword != 'admin123') {
      throw const ApiException('Current password is incorrect', statusCode: 400);
    }
  }

  @override
  Future<OverviewModel> getOverview({
    required String deviceId,
    String period = 'all',
    DateTime? from,
    DateTime? to,
  }) async {
    await _latency();
    final effectivePeriod = (from != null && to != null) ? 'custom' : period;
    if (_cleanedOnce) {
      return OverviewModel.fromJson({
        'device_id': deviceId,
        'device_name': 'Thùng Edge AI #001',
        'location': 'Khu A - Sảnh chính',
        'period': effectivePeriod,
        'as_of': DateTime.now().toUtc().toIso8601String(),
        'categories': [
          for (final id in ['plastic', 'metal', 'paper', 'unknown'])
            {
              'class_id': id,
              'label': id,
              'count': 0,
              'weight_kg': 0,
              'weight_g': 0,
              'accepted': 0,
              'rejected': 0,
            },
        ],
        'totals': {'count': 0, 'weight_kg': 0, 'accepted': 0, 'rejected': 0},
        'unresolved_alert_count': 0,
        'bins': {
          'plastic_pct': 0,
          'metal_pct': 0,
          'paper_pct': 0,
          'max_pct': 0,
          'is_over_90': false,
        },
      });
    }
    return OverviewModel.fromJson({
      'device_id': deviceId,
      'device_name': 'Thùng Edge AI #001',
      'location': 'Khu A - Sảnh chính',
      'period': effectivePeriod,
      'as_of': DateTime.now().toUtc().toIso8601String(),
      'categories': [
        {
          'class_id': 'plastic',
          'label': 'Nhựa',
          'count': 42,
          'weight_kg': 1.05,
          'weight_g': 1050,
          'accepted': 40,
          'rejected': 2,
        },
        {
          'class_id': 'metal',
          'label': 'Kim loại',
          'count': 18,
          'weight_kg': 0.72,
          'weight_g': 720,
          'accepted': 17,
          'rejected': 1,
        },
        {
          'class_id': 'paper',
          'label': 'Giấy',
          'count': 31,
          'weight_kg': 0.465,
          'weight_g': 465,
          'accepted': 30,
          'rejected': 1,
        },
        {
          'class_id': 'unknown',
          'label': 'Không rõ',
          'count': 7,
          'weight_kg': 0.14,
          'weight_g': 140,
          'accepted': 0,
          'rejected': 7,
        },
      ],
      'totals': {
        'count': 98,
        'weight_kg': 2.375,
        'accepted': 87,
        'rejected': 11,
      },
      'unresolved_alert_count': _alerts.where((a) => a['is_resolved'] == false).length,
      'bins': {
        'plastic_pct': 92.4,
        'metal_pct': 61.2,
        'paper_pct': 70.1,
        'max_pct': 92.4,
        'is_over_90': true,
      },
    });
  }

  @override
  Future<CleanBatchModel> clean({required String deviceId}) async {
    await _latency();
    final overview = await getOverview(deviceId: deviceId);
    final batch = {
      'id': 'clean_mock_1',
      'device_id': deviceId,
      'cleaned_at': DateTime.now().toUtc().toIso8601String(),
      'categories': overview.categories.map((c) => {
            'class_id': c.classId,
            'label': c.label,
            'count': c.count,
            'weight_kg': c.weightKg,
            'weight_g': c.weightG,
            'accepted': c.accepted,
            'rejected': c.rejected,
          }).toList(),
      'totals': {
        'count': overview.totals.count,
        'weight_kg': overview.totals.weightKg,
        'accepted': overview.totals.accepted,
        'rejected': overview.totals.rejected,
      },
    };
    _history.insert(0, batch);
    _cleanedOnce = true;
    return CleanBatchModel.fromJson(batch);
  }

  @override
  Future<HistoryListModel> getHistory({required String deviceId}) async {
    await _latency();
    return HistoryListModel.fromJson({'items': _history, 'total': _history.length});
  }

  @override
  Future<FundModel> getFund({required String deviceId}) async {
    await _latency();
    return FundModel.fromJson({
      'current_weight_kg': _cleanedOnce ? 0 : 2.235,
      'history_weight_kg': _cleanedOnce ? 2.235 : 0,
      'total_weight_kg': 2.235,
      'lines': [
        {
          'class_id': 'plastic',
          'label': 'Nhựa',
          'weight_kg': 1.05,
          'rate_vnd_per_kg': 2000,
          'amount_vnd': 2100,
        },
        {
          'class_id': 'metal',
          'label': 'Kim loại',
          'weight_kg': 0.72,
          'rate_vnd_per_kg': 20000,
          'amount_vnd': 14400,
        },
        {
          'class_id': 'paper',
          'label': 'Giấy',
          'weight_kg': 0.465,
          'rate_vnd_per_kg': 3000,
          'amount_vnd': 1395,
        },
      ],
      'total_vnd': 17895,
      'contact_phone': '0325916822',
      'contact_email': 'truongngoclong.21072005@gmail.com',
    });
  }

  @override
  Future<AlertListModel> getAlerts({
    required String deviceId,
    bool? resolved,
  }) async {
    await _latency();
    final filtered = _alerts.where((item) {
      if (item['device_id'] != deviceId) return false;
      if (resolved == null) return true;
      return item['is_resolved'] == resolved;
    }).toList();
    return AlertListModel.fromJson({
      'items': filtered,
      'total': filtered.length,
    });
  }

  @override
  Future<AlertModel> resolveAlert(String alertId) async {
    await _latency();
    final index = _alerts.indexWhere((item) => item['id'] == alertId);
    if (index < 0) {
      throw const ApiException('Alert not found', statusCode: 404);
    }
    _alerts[index] = {
      ..._alerts[index],
      'is_resolved': true,
      'resolved_at': DateTime.now().toUtc().toIso8601String(),
    };
    return AlertModel.fromJson(_alerts[index]);
  }
}
