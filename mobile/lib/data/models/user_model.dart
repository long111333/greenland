class UserModel {
  const UserModel({
    required this.id,
    required this.username,
    required this.displayName,
    required this.role,
    this.phone,
    this.email,
    this.address,
  });

  final int id;
  final String username;
  final String displayName;
  final String role;
  final String? phone;
  final String? email;
  final String? address;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as int,
      username: json['username'] as String,
      displayName: (json['display_name'] as String?) ?? json['username'] as String,
      role: (json['role'] as String?) ?? 'viewer',
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      address: json['address'] as String?,
    );
  }

  UserModel copyWith({
    String? username,
    String? displayName,
    String? phone,
    String? email,
    String? address,
  }) {
    return UserModel(
      id: id,
      username: username ?? this.username,
      displayName: displayName ?? this.displayName,
      role: role,
      phone: phone ?? this.phone,
      email: email ?? this.email,
      address: address ?? this.address,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'display_name': displayName,
        'role': role,
        'phone': phone,
        'email': email,
        'address': address,
      };
}
