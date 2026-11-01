import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/network/error_handler.dart';
import '../../data/repositories/auth_repository.dart';
import 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthInitial());

  final AuthRepository _repository;

  Future<void> bootstrap() async {
    emit(const AuthChecking());
    try {
      final user = await _repository.restoreSession();
      if (user == null) {
        emit(const AuthUnauthenticated());
      } else {
        emit(AuthAuthenticated(user));
      }
    } catch (_) {
      emit(const AuthUnauthenticated());
    }
  }

  Future<void> login({
    required String username,
    required String password,
  }) async {
    emit(const AuthLoading());
    try {
      final user = await _repository.login(
        username: username.trim(),
        password: password,
      );
      emit(AuthAuthenticated(user));
    } catch (error) {
      emit(AuthFailure(ErrorHandler.from(error).message));
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    emit(const AuthUnauthenticated());
  }

  Future<String?> updateProfile({
    required String username,
    String? phone,
    String? email,
    String? address,
    String? displayName,
  }) async {
    try {
      final user = await _repository.updateProfile(
        username: username.trim(),
        phone: phone,
        email: email,
        address: address,
        displayName: displayName,
      );
      emit(AuthAuthenticated(user));
      return null;
    } catch (error) {
      return ErrorHandler.from(error).message;
    }
  }

  Future<String?> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _repository.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      return null;
    } catch (error) {
      return ErrorHandler.from(error).message;
    }
  }
}
