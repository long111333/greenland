class DeviceModel {
  const DeviceModel({
    required this.id,
    required this.name,
    required this.location,
    required this.status,
    this.hardwareVersion,
  });

  final String id;
  final String name;
  final String location;
  final String status;
  final String? hardwareVersion;

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      id: json['id'] as String,
      name: json['name'] as String,
      location: json['location'] as String? ?? '',
      status: json['status'] as String? ?? 'OFFLINE',
      hardwareVersion: json['hardware_version'] as String?,
    );
  }
}
