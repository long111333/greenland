import '../../config/app_config.dart';
import '../models/fund_model.dart';
import '../models/history_model.dart';
import '../models/overview_model.dart';
import '../providers/api_provider.dart';

class BinRepository {
  BinRepository(this._api);

  final AppApi _api;

  Future<CleanBatchModel> clean({
    String deviceId = AppConfig.defaultDeviceId,
  }) {
    return _api.clean(deviceId: deviceId);
  }

  Future<HistoryListModel> history({
    String deviceId = AppConfig.defaultDeviceId,
  }) {
    return _api.getHistory(deviceId: deviceId);
  }

  Future<FundModel> fund({
    String deviceId = AppConfig.defaultDeviceId,
  }) {
    return _api.getFund(deviceId: deviceId);
  }
}
