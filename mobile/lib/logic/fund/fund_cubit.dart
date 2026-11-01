import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/network/error_handler.dart';
import '../../data/models/fund_model.dart';
import '../../data/repositories/bin_repository.dart';

abstract class FundState {
  const FundState();
}

class FundInitial extends FundState {
  const FundInitial();
}

class FundLoading extends FundState {
  const FundLoading();
}

class FundLoaded extends FundState {
  const FundLoaded(this.data);
  final FundModel data;
}

class FundFailure extends FundState {
  const FundFailure(this.message);
  final String message;
}

class FundCubit extends Cubit<FundState> {
  FundCubit(this._repository) : super(const FundInitial());

  final BinRepository _repository;

  Future<void> load() async {
    emit(const FundLoading());
    try {
      final data = await _repository.fund();
      emit(FundLoaded(data));
    } catch (error) {
      emit(FundFailure(ErrorHandler.from(error).message));
    }
  }
}
