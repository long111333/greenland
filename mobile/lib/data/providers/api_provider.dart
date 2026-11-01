import 'package:dio/dio.dart';

import '../../core/constants/api_endpoints.dart';
import '../../core/network/api_client.dart';
import '../../core/network/error_handler.dart';
import '../models/alert_model.dart';
import '../models/auth_response.dart';
import '../models/fund_model.dart';
import '../models/history_model.dart';
import '../models/overview_model.dart';
import '../models/user_model.dart';

/// Contract-shaped API surface used by both real Dio and mock drivers.
abstract class AppApi {
  Future<AuthResponse> login({
    required String username,
    required String password,
  });

  Future<void> logout();

  Future<UserModel> me();

  Future<UserModel> updateProfile({
    required String username,
    String? phone,
    String? email,
    String? address,
    String? displayName,
  });

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });

  Future<OverviewModel> getOverview({
    required String deviceId,
    String period = 'all',
    DateTime? from,
    DateTime? to,
  });

  Future<CleanBatchModel> clean({required String deviceId});

  Future<HistoryListModel> getHistory({required String deviceId});

  Future<FundModel> getFund({required String deviceId});

  Future<AlertListModel> getAlerts({
    required String deviceId,
    bool? resolved,
  });

  Future<AlertModel> resolveAlert(String alertId);
}

class ApiProvider implements AppApi {
  ApiProvider(this._client);

  final ApiClient _client;

  @override
  Future<AuthResponse> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await _client.dio.post(
        ApiEndpoints.login,
        data: {'username': username, 'password': password},
      );
      return AuthResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _client.dio.post(ApiEndpoints.logout);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<UserModel> me() async {
    try {
      final response = await _client.dio.get(ApiEndpoints.me);
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<UserModel> updateProfile({
    required String username,
    String? phone,
    String? email,
    String? address,
    String? displayName,
  }) async {
    try {
      final response = await _client.dio.put(
        ApiEndpoints.profile,
        data: {
          'username': username,
          'phone': phone,
          'email': email,
          'address': address,
          'display_name': displayName,
        },
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _client.dio.post(
        ApiEndpoints.changePassword,
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
      );
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<OverviewModel> getOverview({
    required String deviceId,
    String period = 'all',
    DateTime? from,
    DateTime? to,
  }) async {
    try {
      final response = await _client.dio.get(
        ApiEndpoints.overview(
          deviceId: deviceId,
          period: period,
          from: from,
          to: to,
        ),
      );
      return OverviewModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<CleanBatchModel> clean({required String deviceId}) async {
    try {
      final response = await _client.dio.post(ApiEndpoints.clean(deviceId: deviceId));
      return CleanBatchModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<HistoryListModel> getHistory({required String deviceId}) async {
    try {
      final response = await _client.dio.get(ApiEndpoints.history(deviceId: deviceId));
      return HistoryListModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<FundModel> getFund({required String deviceId}) async {
    try {
      final response = await _client.dio.get(ApiEndpoints.fund(deviceId: deviceId));
      return FundModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<AlertListModel> getAlerts({
    required String deviceId,
    bool? resolved,
  }) async {
    try {
      final response = await _client.dio.get(
        ApiEndpoints.alerts(deviceId: deviceId, resolved: resolved),
      );
      return AlertListModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }

  @override
  Future<AlertModel> resolveAlert(String alertId) async {
    try {
      final response = await _client.dio.post(ApiEndpoints.resolveAlert(alertId));
      return AlertModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ErrorHandler.from(error);
    }
  }
}
