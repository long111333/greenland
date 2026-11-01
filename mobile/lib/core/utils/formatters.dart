import 'package:intl/intl.dart';

class Formatters {
  static final _date = DateFormat('dd/MM/yyyy');
  static final _dateTime = DateFormat('dd/MM/yyyy HH:mm');

  static String date(DateTime value) => _date.format(value.toLocal());

  static String dateTime(DateTime value) => _dateTime.format(value.toLocal());

  static DateTime? tryParseIso(String? raw) {
    if (raw == null || raw.isEmpty) return null;
    return DateTime.tryParse(raw);
  }

  static String weightKg(double kg) {
    if (kg == 0) return '0 kg';
    if (kg >= 10) return '${kg.toStringAsFixed(1)} kg';
    final text = kg.toStringAsFixed(3).replaceFirst(RegExp(r'0+$'), '');
    final trimmed = text.endsWith('.') ? text.substring(0, text.length - 1) : text;
    return '$trimmed kg';
  }

  static String count(int value) => NumberFormat.decimalPattern().format(value);

  static String vnd(int value) {
    final formatted = NumberFormat('#,###', 'vi_VN').format(value);
    return '$formatted ₫';
  }
}
