import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/network/error_handler.dart';
import '../../data/models/history_model.dart';
import '../../data/repositories/bin_repository.dart';
import '../../data/repositories/overview_repository.dart';
import 'overview_state.dart';

class OverviewCubit extends Cubit<OverviewState> {
  OverviewCubit(this._repository, this._binRepository)
      : super(const OverviewInitial());

  final OverviewRepository _repository;
  final BinRepository _binRepository;
  String _period = 'all';
  DateTime? _from;
  DateTime? _to;

  String get period => _period;
  DateTime? get from => _from;
  DateTime? get to => _to;

  Future<void> load({String period = 'all'}) async {
    _period = period;
    _from = null;
    _to = null;
    emit(const OverviewLoading());
    await _fetch();
  }

  Future<void> loadRange({required DateTime from, required DateTime to}) async {
    _period = 'custom';
    _from = DateTime(from.year, from.month, from.day);
    _to = DateTime(to.year, to.month, to.day);
    emit(const OverviewLoading());
    await _fetch();
  }

  Future<void> refresh() async {
    if (state is! OverviewLoaded) {
      emit(const OverviewLoading());
    }
    await _fetch();
  }

  Future<CleanBatchModel?> clean() async {
    try {
      final batch = await _binRepository.clean();
      await _fetch();
      return batch;
    } catch (error) {
      emit(OverviewFailure(ErrorHandler.from(error).message));
      return null;
    }
  }

  Future<void> _fetch() async {
    try {
      final data = await _repository.fetch(
        period: _period,
        from: _from,
        to: _to,
      );
      emit(OverviewLoaded(data, period: _period, from: _from, to: _to));
    } catch (error) {
      emit(OverviewFailure(ErrorHandler.from(error).message));
    }
  }
}
