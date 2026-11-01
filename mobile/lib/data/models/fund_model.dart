class FundLineModel {
  const FundLineModel({
    required this.classId,
    required this.label,
    required this.weightKg,
    required this.rateVndPerKg,
    required this.amountVnd,
  });

  final String classId;
  final String label;
  final double weightKg;
  final int rateVndPerKg;
  final int amountVnd;

  factory FundLineModel.fromJson(Map<String, dynamic> json) {
    return FundLineModel(
      classId: json['class_id'] as String,
      label: json['label'] as String,
      weightKg: (json['weight_kg'] as num).toDouble(),
      rateVndPerKg: (json['rate_vnd_per_kg'] as num).toInt(),
      amountVnd: (json['amount_vnd'] as num).toInt(),
    );
  }
}

class FundModel {
  const FundModel({
    required this.currentWeightKg,
    required this.historyWeightKg,
    required this.totalWeightKg,
    required this.lines,
    required this.totalVnd,
    required this.contactPhone,
    required this.contactEmail,
  });

  final double currentWeightKg;
  final double historyWeightKg;
  final double totalWeightKg;
  final List<FundLineModel> lines;
  final int totalVnd;
  final String contactPhone;
  final String contactEmail;

  factory FundModel.fromJson(Map<String, dynamic> json) {
    return FundModel(
      currentWeightKg: (json['current_weight_kg'] as num).toDouble(),
      historyWeightKg: (json['history_weight_kg'] as num).toDouble(),
      totalWeightKg: (json['total_weight_kg'] as num).toDouble(),
      lines: (json['lines'] as List<dynamic>)
          .map((e) => FundLineModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalVnd: (json['total_vnd'] as num).toInt(),
      contactPhone: json['contact_phone'] as String? ?? '0325916822',
      contactEmail:
          json['contact_email'] as String? ?? 'truongngoclong.21072005@gmail.com',
    );
  }
}
