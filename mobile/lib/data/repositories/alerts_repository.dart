import '../../config/app_config.dart';
import '../models/alert_model.dart';
import '../providers/api_provider.dart';

class AlertsRepository {
  AlertsRepository(this._api);

  final AppApi _api;

  Future<AlertListModel> fetch({
    String deviceId = AppConfig.defaultDeviceId,
    bool? resolved = false,
  }) {
    return _api.getAlerts(deviceId: deviceId, resolved: resolved);
  }

  Future<AlertModel> resolve(String alertId) {
    return _api.resolveAlert(alertId);
  }
}
