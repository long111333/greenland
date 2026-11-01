class AlertModel {
  const AlertModel({
    required this.id,
    required this.deviceId,
    required this.type,
    required this.severity,
    required this.title,
    required this.message,
    required this.isResolved,
    required this.createdAt,
    this.resolvedAt,
  });

  final String id;
  final String deviceId;
  final String type;
  final String severity;
  final String title;
  final String message;
  final bool isResolved;
  final DateTime createdAt;
  final DateTime? resolvedAt;

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    return AlertModel(
      id: json['id'] as String,
      deviceId: json['device_id'] as String,
      type: json['type'] as String,
      severity: json['severity'] as String,
      title: json['title'] as String,
      message: json['message'] as String,
      isResolved: json['is_resolved'] == true || json['is_resolved'] == 1,
      createdAt: DateTime.parse(json['created_at'] as String),
      resolvedAt: json['resolved_at'] == null
          ? null
          : DateTime.tryParse(json['resolved_at'] as String),
    );
  }
}

class AlertListModel {
  const AlertListModel({
    required this.items,
    required this.total,
  });

  final List<AlertModel> items;
  final int total;

  factory AlertListModel.fromJson(Map<String, dynamic> json) {
    return AlertListModel(
      items: (json['items'] as List<dynamic>)
          .map((e) => AlertModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num?)?.toInt() ?? 0,
    );
  }
}
