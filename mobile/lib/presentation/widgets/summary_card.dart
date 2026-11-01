import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../config/theme.dart';
import '../../core/utils/formatters.dart';
import '../../data/models/overview_model.dart';

class OverviewSummaryCard extends StatefulWidget {
  const OverviewSummaryCard({
    super.key,
    required this.data,
    required this.onClean,
    this.cleaning = false,
  });

  final OverviewModel data;
  final VoidCallback onClean;
  final bool cleaning;

  @override
  State<OverviewSummaryCard> createState() => _OverviewSummaryCardState();
}

class _OverviewSummaryCardState extends State<OverviewSummaryCard> {
  bool _expanded = true;

  String _locationLabel(String raw) {
    final key = raw.trim().toLowerCase();
    if (key.contains('khu a') && key.contains('sảnh')) {
      return 'Zone A – Main Lobby';
    }
    if (key.contains('khu a') && key.contains('sanh')) {
      return 'Zone A – Main Lobby';
    }
    return raw.isEmpty ? '—' : raw;
  }

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    final over90 = data.bins.isOver90;
    final buttonColor = over90 ? AppColors.danger : AppColors.primary;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppRadii.sheet),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.08),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        children: [
          Align(
            alignment: Alignment.center,
            child: InkWell(
              onTap: () => setState(() => _expanded = !_expanded),
              borderRadius: BorderRadius.circular(24),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                child: AnimatedRotation(
                  turns: _expanded ? 0.5 : 0,
                  duration: const Duration(milliseconds: 200),
                  child: const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: AppColors.textSecondary,
                    size: 30,
                  ),
                ),
              ),
            ),
          ),
          AnimatedCrossFade(
            firstChild: Column(
              children: [
                const SizedBox(height: 6),
                _row('Location', _locationLabel(data.location)),
                const Divider(height: 22, color: AppColors.divider),
                _row('Date', Formatters.date(data.asOf)),
                const Divider(height: 22, color: AppColors.divider),
                _row(
                  'Total',
                  '${Formatters.weightKg(data.totals.weightKg)}  ·  ${Formatters.count(data.totals.count)} items',
                  emphasize: true,
                ),
                if (over90) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppColors.danger.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.danger.withOpacity(0.35)),
                    ),
                    child: Text(
                      'Bin nearly full (${data.bins.maxPct.toStringAsFixed(0)}%). Please Clean now.',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.danger,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: FilledButton(
                    onPressed: widget.cleaning ? null : widget.onClean,
                    style: FilledButton.styleFrom(
                      backgroundColor: buttonColor,
                      disabledBackgroundColor: buttonColor.withOpacity(0.55),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppRadii.button),
                      ),
                    ),
                    child: widget.cleaning
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.4,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            'Clean',
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                ),
              ],
            ),
            secondChild: const SizedBox(width: double.infinity, height: 0),
            crossFadeState:
                _expanded ? CrossFadeState.showFirst : CrossFadeState.showSecond,
            duration: const Duration(milliseconds: 220),
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value, {bool emphasize = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 92,
          child: Text(
            label,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 14,
              fontWeight: emphasize ? FontWeight.w700 : FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
