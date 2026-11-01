import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../config/theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../logic/alerts/alerts_cubit.dart';
import '../../../logic/alerts/alerts_state.dart';
import '../../../logic/overview/overview_cubit.dart';
import '../../widgets/severity_badge.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<AlertsCubit>().load(resolved: false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.mintSoft,
      appBar: AppBar(
        backgroundColor: AppColors.mintSoft,
        title: const Text('Cảnh báo'),
      ),
      body: BlocBuilder<AlertsCubit, AlertsState>(
        builder: (context, state) {
          if (state is AlertsLoading || state is AlertsInitial) {
            return const Center(child: SpinKitPulse(color: AppColors.primary, size: 42));
          }
          if (state is AlertsFailure) {
            return EmptyState(
              message: state.message,
              icon: Icons.wifi_off_rounded,
              onRetry: () => context.read<AlertsCubit>().load(resolved: false),
            );
          }
          if (state is! AlertsLoaded) {
            return const EmptyState(message: 'Không có cảnh báo.');
          }
          if (state.data.items.isEmpty) {
            return const EmptyState(
              message: 'Không có cảnh báo chưa xử lý.',
              icon: Icons.verified_outlined,
            );
          }

          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () => context.read<AlertsCubit>().load(resolved: false),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
              itemCount: state.data.items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final alert = state.data.items[index];
                final resolving = state.resolvingId == alert.id;
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(AppRadii.card),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          SeverityBadge(severity: alert.severity),
                          const SizedBox(width: 8),
                          Text(
                            alert.type,
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          const Spacer(),
                          Text(
                            Formatters.dateTime(alert.createdAt),
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 11,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(
                        alert.title,
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        alert.message,
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 13,
                          height: 1.45,
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (!alert.isResolved) ...[
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: resolving
                                ? null
                                : () async {
                                    await context.read<AlertsCubit>().resolve(alert.id);
                                    if (context.mounted) {
                                      context.read<OverviewCubit>().refresh();
                                    }
                                  },
                            child: resolving
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Text(
                                    'Đánh dấu đã xử lý',
                                    style: GoogleFonts.plusJakartaSans(
                                      fontWeight: FontWeight.w700,
                                      color: AppColors.primary,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
