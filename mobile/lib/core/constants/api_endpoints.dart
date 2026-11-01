/// REST paths from SHARED_CONTRACT.md — prefix `/api/v1`.
class ApiEndpoints {
  static const prefix = '/api/v1';

  static const login = '$prefix/auth/login';
  static const logout = '$prefix/auth/logout';
  static const me = '$prefix/auth/me';

  static String overview({
    required String deviceId,
    String period = 'all',
    DateTime? from,
    DateTime? to,
  }) {
    final params = <String>[
      'device_id=$deviceId',
    ];
    if (from != null && to != null) {
      params.add('from=${_ymd(from)}');
      params.add('to=${_ymd(to)}');
      params.add('period=custom');
    } else {
      params.add('period=$period');
    }
    return '$prefix/statistics/overview?${params.join('&')}';
  }

  static String alerts({
    required String deviceId,
    bool? resolved,
  }) {
    final params = <String>['device_id=$deviceId'];
    if (resolved != null) params.add('resolved=$resolved');
    return '$prefix/alerts?${params.join('&')}';
  }

  static String resolveAlert(String alertId) =>
      '$prefix/alerts/$alertId/resolve';

  static const devices = '$prefix/devices';

  static String device(String deviceId) => '$prefix/devices/$deviceId';

  static String clean({required String deviceId}) =>
      '$prefix/clean?device_id=$deviceId';

  static String history({required String deviceId}) =>
      '$prefix/history?device_id=$deviceId';

  static String fund({required String deviceId}) =>
      '$prefix/fund?device_id=$deviceId';

  static const profile = '$prefix/auth/profile';
  static const changePassword = '$prefix/auth/change-password';

  static String _ymd(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}
