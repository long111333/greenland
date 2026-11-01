import '../../config/app_config.dart';
import '../models/overview_model.dart';
import '../providers/api_provider.dart';

class OverviewRepository {
  OverviewRepository(this._api);

  final AppApi _api;

  Future<OverviewModel> fetch({
    String deviceId = AppConfig.defaultDeviceId,
    String period = 'all',
    DateTime? from,
    DateTime? to,
  }) {
    return _api.getOverview(
      deviceId: deviceId,
      period: period,
      from: from,
      to: to,
    );
  }
}
