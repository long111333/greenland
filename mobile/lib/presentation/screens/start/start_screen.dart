import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/recycle_illustration.dart';

class StartScreen extends StatelessWidget {
  const StartScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(28, 12, 28, 28),
          child: Column(
            children: [
              const Spacer(flex: 2),
              const RecycleIllustration(size: 280),
              const SizedBox(height: 28),
              Text(
                "It's time to recycle!",
                textAlign: TextAlign.center,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Thùng phân loại rác tự động AutoBin — nhựa, kim loại, giấy và vật liệu chưa rõ, giám sát bằng Edge AI.',
                textAlign: TextAlign.center,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 14,
                  height: 1.5,
                  fontWeight: FontWeight.w500,
                  color: AppColors.textSecondary,
                ),
              ),
              const Spacer(flex: 3),
              OutlinedAppButton(
                label: 'Start now',
                onPressed: () => Navigator.of(context).pushNamed(AppRoutes.login),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
