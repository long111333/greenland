import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/network/error_handler.dart';
import '../../data/repositories/alerts_repository.dart';
import 'alerts_state.dart';

class AlertsCubit extends Cubit<AlertsState> {
  AlertsCubit(this._repository) : super(const AlertsInitial());

  final AlertsRepository _repository;

  Future<void> load({bool resolved = false}) async {
    emit(const AlertsLoading());
    try {
      final data = await _repository.fetch(resolved: resolved);
      emit(AlertsLoaded(data));
    } catch (error) {
      emit(AlertsFailure(ErrorHandler.from(error).message));
    }
  }

  Future<void> resolve(String alertId) async {
    final current = state;
    if (current is AlertsLoaded) {
      emit(AlertsLoaded(current.data, resolvingId: alertId));
    }
    try {
      await _repository.resolve(alertId);
      await load(resolved: false);
    } catch (error) {
      emit(AlertsFailure(ErrorHandler.from(error).message));
    }
  }
}
