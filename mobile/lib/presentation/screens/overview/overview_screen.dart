import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../logic/overview/overview_cubit.dart';
import '../../../logic/overview/overview_state.dart';
import '../../widgets/category_card.dart';
import '../../widgets/severity_badge.dart';
import '../../widgets/summary_card.dart';

class OverviewScreen extends StatefulWidget {
  const OverviewScreen({super.key, this.onCleaned});

  final VoidCallback? onCleaned;

  @override
  State<OverviewScreen> createState() => _OverviewScreenState();
}

class _OverviewScreenState extends State<OverviewScreen> {
  static const _periods = [
    ('all', 'All'),
    ('day', 'Day'),
    ('week', 'Week'),
    ('month', 'Month'),
  ];

  static final _dateFmt = DateFormat('dd/MM/yyyy');
  bool _cleaning = false;

  @override
  void initState() {
    super.initState();
    context.read<OverviewCubit>().load();
  }

  Future<void> _pickCustomRange(OverviewState state) async {
    final now = DateTime.now();
    DateTimeRange? initial;
    if (state is OverviewLoaded && state.isCustomRange) {
      initial = DateTimeRange(start: state.from!, end: state.to!);
    }
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2024, 1, 1),
      lastDate: DateTime(now.year, now.month, now.day),
      initialDateRange: initial ??
          DateTimeRange(
            start: now.subtract(const Duration(days: 7)),
            end: DateTime(now.year, now.month, now.day),
          ),
      helpText: 'Select date range',
      saveText: 'Apply',
      cancelText: 'Cancel',
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: Theme.of(context).colorScheme.copyWith(
                  primary: AppColors.primary,
                  onPrimary: Colors.white,
                ),
          ),
          child: child!,
        );
      },
    );
    if (picked == null || !mounted) return;
    await context.read<OverviewCubit>().loadRange(
          from: picked.start,
          to: picked.end,
        );
  }

  Future<void> _onClean() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clean bins?'),
        content: const Text(
          'All current waste will move to History by category.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Clean')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _cleaning = true);
    final batch = await context.read<OverviewCubit>().clean();
    if (!mounted) return;
    setState(() => _cleaning = false);
    if (batch == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Clean failed'), backgroundColor: AppColors.danger),
      );
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Cleaned ${batch.totals.count} items → History'),
        backgroundColor: AppColors.primary,
      ),
    );
    widget.onCleaned?.call();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.mintSoft,
      appBar: AppBar(
        backgroundColor: AppColors.mintSoft,
        automaticallyImplyLeading: false,
        title: const Text('Overview'),
        actions: [
          BlocBuilder<OverviewCubit, OverviewState>(
            builder: (context, state) {
              final badge = state is OverviewLoaded ? state.data.unresolvedAlertCount : 0;
              return IconButton(
                tooltip: 'Alerts',
                onPressed: () => Navigator.of(context).pushNamed(AppRoutes.alerts),
                icon: Badge(
                  isLabelVisible: badge > 0,
                  label: Text('$badge'),
                  backgroundColor: AppColors.danger,
                  child: const Icon(Icons.notifications_none_rounded),
                ),
              );
            },
          ),
        ],
      ),
      body: BlocBuilder<OverviewCubit, OverviewState>(
        builder: (context, state) {
          if (state is OverviewLoading || state is OverviewInitial) {
            return const Center(
              child: SpinKitPulse(color: AppColors.primary, size: 42),
            );
          }
          if (state is OverviewFailure) {
            return EmptyState(
              message: state.message,
              icon: Icons.wifi_off_rounded,
              onRetry: () => context.read<OverviewCubit>().refresh(),
            );
          }
          if (state is! OverviewLoaded) {
            return const EmptyState(message: 'No data yet.');
          }

          final data = state.data;
          final custom = state.isCustomRange;

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      ..._periods.map((item) {
                        final selected = !custom && state.period == item.$1;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text(item.$2),
                            selected: selected,
                            onSelected: (_) =>
                                context.read<OverviewCubit>().load(period: item.$1),
                            selectedColor: AppColors.mint,
                            labelStyle: GoogleFonts.plusJakartaSans(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                            side: BorderSide(
                              color: selected
                                  ? AppColors.primary.withOpacity(0.25)
                                  : AppColors.divider,
                            ),
                            backgroundColor: Colors.white,
                            showCheckmark: false,
                            visualDensity: VisualDensity.compact,
                          ),
                        );
                      }),
                      ChoiceChip(
                        label: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.date_range_rounded,
                              size: 16,
                              color: custom ? AppColors.primary : AppColors.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Text(custom ? 'Custom range' : 'Custom'),
                          ],
                        ),
                        selected: custom,
                        onSelected: (_) => _pickCustomRange(state),
                        selectedColor: AppColors.mint,
                        labelStyle: GoogleFonts.plusJakartaSans(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                        side: BorderSide(
                          color: custom
                              ? AppColors.primary.withOpacity(0.25)
                              : AppColors.divider,
                        ),
                        backgroundColor: Colors.white,
                        showCheckmark: false,
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                  ),
                ),
              ),
              if (custom)
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
                  child: Material(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(14),
                      onTap: () => _pickCustomRange(state),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.calendar_month_rounded,
                              size: 18,
                              color: AppColors.primary,
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                '${_dateFmt.format(state.from!)}  →  ${_dateFmt.format(state.to!)}',
                                style: GoogleFonts.plusJakartaSans(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                            ),
                            IconButton(
                              tooltip: 'Xoá khoảng ngày',
                              visualDensity: VisualDensity.compact,
                              onPressed: () =>
                                  context.read<OverviewCubit>().load(period: 'all'),
                              icon: const Icon(Icons.close_rounded, size: 18),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: RefreshIndicator(
                  color: AppColors.primary,
                  onRefresh: () => context.read<OverviewCubit>().refresh(),
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
                    children: [
                      Text(
                        data.deviceName,
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 10),
                      ...data.categories.map((item) => CategoryCard(category: item)),
                    ],
                  ),
                ),
              ),
              OverviewSummaryCard(
                data: data,
                cleaning: _cleaning,
                onClean: _onClean,
              ),
            ],
          );
        },
      ),
    );
  }
}
