import 'overview_model.dart';

class CleanBatchModel {
  const CleanBatchModel({
    required this.id,
    required this.deviceId,
    required this.cleanedAt,
    required this.categories,
    required this.totals,
  });

  final String id;
  final String deviceId;
  final DateTime cleanedAt;
  final List<CategoryStat> categories;
  final OverviewTotals totals;

  factory CleanBatchModel.fromJson(Map<String, dynamic> json) {
    return CleanBatchModel(
      id: json['id'] as String,
      deviceId: json['device_id'] as String,
      cleanedAt: DateTime.parse(json['cleaned_at'] as String),
      categories: (json['categories'] as List<dynamic>)
          .map((e) => CategoryStat.fromJson(e as Map<String, dynamic>))
          .toList(),
      totals: OverviewTotals.fromJson(json['totals'] as Map<String, dynamic>),
    );
  }
}

class HistoryListModel {
  const HistoryListModel({required this.items, required this.total});

  final List<CleanBatchModel> items;
  final int total;

  factory HistoryListModel.fromJson(Map<String, dynamic> json) {
    return HistoryListModel(
      items: (json['items'] as List<dynamic>)
          .map((e) => CleanBatchModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num?)?.toInt() ?? 0,
    );
  }
}
