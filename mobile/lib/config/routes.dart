import 'package:flutter/material.dart';

import '../presentation/screens/alerts/alerts_screen.dart';
import '../presentation/screens/auth/login_screen.dart';
import '../presentation/screens/shell/main_shell.dart';
import '../presentation/screens/start/start_screen.dart';

class AppRoutes {
  static const start = '/start';
  static const login = '/login';
  static const home = '/home';
  static const overview = '/home'; // backward-compatible alias → main shell
  static const alerts = '/alerts';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case start:
        return _fade(const StartScreen(), settings);
      case login:
        return _slide(const LoginScreen(), settings);
      case home:
        return _fade(const MainShell(), settings);
      case alerts:
        return _slide(const AlertsScreen(), settings);
      default:
        return _fade(const StartScreen(), settings);
    }
  }

  static PageRoute<T> _fade<T>(Widget page, RouteSettings settings) {
    return PageRouteBuilder<T>(
      settings: settings,
      pageBuilder: (_, __, ___) => page,
      transitionsBuilder: (_, animation, __, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    );
  }

  static PageRoute<T> _slide<T>(Widget page, RouteSettings settings) {
    return PageRouteBuilder<T>(
      settings: settings,
      pageBuilder: (_, __, ___) => page,
      transitionsBuilder: (_, animation, __, child) {
        final offset = Tween<Offset>(
          begin: const Offset(0, 0.06),
          end: Offset.zero,
        ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOutCubic));
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(position: offset, child: child),
        );
      },
    );
  }
}
