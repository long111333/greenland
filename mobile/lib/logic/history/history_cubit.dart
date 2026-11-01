import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/network/error_handler.dart';
import '../../data/models/history_model.dart';
import '../../data/repositories/bin_repository.dart';

abstract class HistoryState {
  const HistoryState();
}

class HistoryInitial extends HistoryState {
  const HistoryInitial();
}

class HistoryLoading extends HistoryState {
  const HistoryLoading();
}

class HistoryLoaded extends HistoryState {
  const HistoryLoaded(this.data);
  final HistoryListModel data;
}

class HistoryFailure extends HistoryState {
  const HistoryFailure(this.message);
  final String message;
}

class HistoryCubit extends Cubit<HistoryState> {
  HistoryCubit(this._repository) : super(const HistoryInitial());

  final BinRepository _repository;

  Future<void> load() async {
    emit(const HistoryLoading());
    try {
      final data = await _repository.history();
      emit(HistoryLoaded(data));
    } catch (error) {
      emit(HistoryFailure(ErrorHandler.from(error).message));
    }
  }
}
