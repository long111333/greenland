import '../../core/network/error_handler.dart';
import '../../core/storage/token_storage.dart';
import '../models/user_model.dart';
import '../providers/api_provider.dart';

class AuthRepository {
  AuthRepository({
    required AppApi api,
    required TokenStorage tokenStorage,
  })  : _api = api,
        _tokenStorage = tokenStorage;

  final AppApi _api;
  final TokenStorage _tokenStorage;

  Future<UserModel> login({
    required String username,
    required String password,
  }) async {
    final result = await _api.login(username: username, password: password);
    await _tokenStorage.saveToken(result.accessToken);
    return result.user;
  }

  Future<UserModel?> restoreSession() async {
    final token = await _tokenStorage.readToken();
    if (token == null || token.isEmpty) return null;
    try {
      return await _api.me();
    } on ApiException catch (error) {
      if (error.statusCode == 401) {
        await _tokenStorage.clear();
        return null;
      }
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      await _api.logout();
    } catch (_) {
      // JWT is stateless — always wipe local token.
    }
    await _tokenStorage.clear();
  }

  Future<UserModel> updateProfile({
    required String username,
    String? phone,
    String? email,
    String? address,
    String? displayName,
  }) {
    return _api.updateProfile(
      username: username,
      phone: phone,
      email: email,
      address: address,
      displayName: displayName,
    );
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) {
    return _api.changePassword(
      currentPassword: currentPassword,
      newPassword: newPassword,
    );
  }
}
