import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const primary = Color(0xFF1B5E3B);
  static const primaryDark = Color(0xFF0F3D26);
  static const mint = Color(0xFFD8F3DC);
  static const mintDeep = Color(0xFFC8E6C9);
  static const mintSoft = Color(0xFFF3FBF5);
  static const background = Color(0xFFFFFFFF);
  static const textPrimary = Color(0xFF1B5E3B);
  static const textSecondary = Color(0xFF7A8B7E);
  static const surface = Color(0xFFF7FBF8);
  static const divider = Color(0xFFE4EEE7);
  static const danger = Color(0xFFC62828);
  static const warning = Color(0xFFF9A825);
  static const info = Color(0xFF0277BD);
  static const critical = Color(0xFFB71C1C);
}

class AppRadii {
  static const card = 20.0;
  static const button = 28.0;
  static const sheet = 28.0;
}

class AppTheme {
  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        primary: AppColors.primary,
        surface: AppColors.background,
      ),
    );

    final textTheme = GoogleFonts.plusJakartaSansTextTheme(base.textTheme).apply(
      bodyColor: AppColors.textPrimary,
      displayColor: AppColors.textPrimary,
    );

    return base.copyWith(
      scaffoldBackgroundColor: AppColors.background,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: AppColors.background,
        foregroundColor: AppColors.textPrimary,
        centerTitle: true,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: AppColors.textPrimary,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.mintSoft,
        hintStyle: GoogleFonts.plusJakartaSans(
          color: AppColors.textSecondary,
          fontWeight: FontWeight.w500,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.4),
        ),
      ),
      dividerColor: AppColors.divider,
    );
  }
}
