class CategoryStat {
  const CategoryStat({
    required this.classId,
    required this.label,
    required this.count,
    required this.weightKg,
    required this.weightG,
    required this.accepted,
    required this.rejected,
  });

  final String classId;
  final String label;
  final int count;
  final double weightKg;
  final double weightG;
  final int accepted;
  final int rejected;

  factory CategoryStat.fromJson(Map<String, dynamic> json) {
    return CategoryStat(
      classId: json['class_id'] as String,
      label: json['label'] as String,
      count: (json['count'] as num).toInt(),
      weightKg: (json['weight_kg'] as num).toDouble(),
      weightG: (json['weight_g'] as num).toDouble(),
      accepted: (json['accepted'] as num?)?.toInt() ?? 0,
      rejected: (json['rejected'] as num?)?.toInt() ?? 0,
    );
  }
}

class OverviewTotals {
  const OverviewTotals({
    required this.count,
    required this.weightKg,
    required this.accepted,
    required this.rejected,
  });

  final int count;
  final double weightKg;
  final int accepted;
  final int rejected;

  factory OverviewTotals.fromJson(Map<String, dynamic> json) {
    return OverviewTotals(
      count: (json['count'] as num).toInt(),
      weightKg: (json['weight_kg'] as num).toDouble(),
      accepted: (json['accepted'] as num?)?.toInt() ?? 0,
      rejected: (json['rejected'] as num?)?.toInt() ?? 0,
    );
  }
}

class BinsCapacity {
  const BinsCapacity({
    required this.plasticPct,
    required this.metalPct,
    required this.paperPct,
    required this.maxPct,
    required this.isOver90,
  });

  final double plasticPct;
  final double metalPct;
  final double paperPct;
  final double maxPct;
  final bool isOver90;

  factory BinsCapacity.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const BinsCapacity(
        plasticPct: 0,
        metalPct: 0,
        paperPct: 0,
        maxPct: 0,
        isOver90: false,
      );
    }
    return BinsCapacity(
      plasticPct: (json['plastic_pct'] as num?)?.toDouble() ?? 0,
      metalPct: (json['metal_pct'] as num?)?.toDouble() ?? 0,
      paperPct: (json['paper_pct'] as num?)?.toDouble() ?? 0,
      maxPct: (json['max_pct'] as num?)?.toDouble() ?? 0,
      isOver90: json['is_over_90'] as bool? ?? false,
    );
  }
}

class OverviewModel {
  const OverviewModel({
    required this.deviceId,
    required this.deviceName,
    required this.location,
    required this.period,
    required this.asOf,
    required this.categories,
    required this.totals,
    required this.unresolvedAlertCount,
    required this.bins,
  });

  final String deviceId;
  final String deviceName;
  final String location;
  final String period;
  final DateTime asOf;
  final List<CategoryStat> categories;
  final OverviewTotals totals;
  final int unresolvedAlertCount;
  final BinsCapacity bins;

  factory OverviewModel.fromJson(Map<String, dynamic> json) {
    return OverviewModel(
      deviceId: json['device_id'] as String,
      deviceName: json['device_name'] as String,
      location: json['location'] as String,
      period: json['period'] as String,
      asOf: DateTime.parse(json['as_of'] as String),
      categories: (json['categories'] as List<dynamic>)
          .map((e) => CategoryStat.fromJson(e as Map<String, dynamic>))
          .toList(),
      totals: OverviewTotals.fromJson(json['totals'] as Map<String, dynamic>),
      unresolvedAlertCount: (json['unresolved_alert_count'] as num?)?.toInt() ?? 0,
      bins: BinsCapacity.fromJson(json['bins'] as Map<String, dynamic>?),
    );
  }
}
