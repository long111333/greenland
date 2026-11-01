import '../../data/models/overview_model.dart';

abstract class OverviewState {
  const OverviewState();
}

class OverviewInitial extends OverviewState {
  const OverviewInitial();
}

class OverviewLoading extends OverviewState {
  const OverviewLoading();
}

class OverviewLoaded extends OverviewState {
  const OverviewLoaded(
    this.data, {
    this.period = 'all',
    this.from,
    this.to,
  });

  final OverviewModel data;
  final String period;
  final DateTime? from;
  final DateTime? to;

  bool get isCustomRange => from != null && to != null;
}

class OverviewFailure extends OverviewState {
  const OverviewFailure(this.message);

  final String message;
}
