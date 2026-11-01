import 'package:dio/dio.dart';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ErrorHandler {
  static ApiException from(Object error) {
    if (error is ApiException) return error;
    if (error is DioException) {
      final status = error.response?.statusCode;
      final data = error.response?.data;
      final detail = _extractDetail(data);
      if (detail != null) {
        return ApiException(detail, statusCode: status);
      }
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
          return ApiException(
            'Hết thời gian chờ máy chủ. Kiểm tra backend tại cổng 8000.',
            statusCode: status,
          );
        case DioExceptionType.connectionError:
          return ApiException(
            'Không kết nối được backend. Kiểm tra BASE_URL hoặc bật mock.',
            statusCode: status,
          );
        default:
          return ApiException(
            error.message ?? 'Lỗi mạng không xác định.',
            statusCode: status,
          );
      }
    }
    return ApiException(error.toString());
  }

  static String? _extractDetail(dynamic data) {
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    if (data is String && data.isNotEmpty) return data;
    return null;
  }
}
