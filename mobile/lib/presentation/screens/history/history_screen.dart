import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../config/theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/history_model.dart';
import '../../../logic/history/history_cubit.dart';
import '../../widgets/severity_badge.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    context.read<HistoryCubit>().load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.mintSoft,
      appBar: AppBar(
        backgroundColor: AppColors.mintSoft,
        automaticallyImplyLeading: false,
        title: const Text('History'),
      ),
      body: BlocBuilder<HistoryCubit, HistoryState>(
        builder: (context, state) {
          if (state is HistoryLoading || state is HistoryInitial) {
            return const Center(child: SpinKitPulse(color: AppColors.primary, size: 42));
          }
          if (state is HistoryFailure) {
            return EmptyState(
              message: state.message,
              onRetry: () => context.read<HistoryCubit>().load(),
            );
          }
          if (state is! HistoryLoaded) {
            return const EmptyState(message: 'Chưa có lịch sử.');
          }
          if (state.data.items.isEmpty) {
            return EmptyState(
              message: 'Chưa có lượt Clean nào.\nBấm Clean ở Overview để chuyển rác vào đây.',
              icon: Icons.history_rounded,
              onRetry: () => context.read<HistoryCubit>().load(),
            );
          }
          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () => context.read<HistoryCubit>().load(),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
              itemCount: state.data.items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                return _BatchCard(batch: state.data.items[index]);
              },
            ),
          );
        },
      ),
    );
  }
}

class _BatchCard extends StatelessWidget {
  const _BatchCard({required this.batch});

  final CleanBatchModel batch;

  @override
  Widget build(BuildContext context) {
    final visible = batch.categories.where((c) => c.count > 0 || c.weightKg > 0).toList();
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppRadii.card),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.05),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.cleaning_services_rounded, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Clean · ${Formatters.dateTime(batch.cleanedAt)}',
                  style: GoogleFonts.plusJakartaSans(
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
              ),
              Text(
                '${batch.totals.count} món',
                style: GoogleFonts.plusJakartaSans(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...visible.map(
            (c) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      c.label,
                      style: GoogleFonts.plusJakartaSans(
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  Text(
                    '${Formatters.weightKg(c.weightKg)} · ${c.count}',
                    style: GoogleFonts.plusJakartaSans(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 18),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              'Tổng ${Formatters.weightKg(batch.totals.weightKg)}',
              style: GoogleFonts.plusJakartaSans(
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
