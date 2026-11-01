import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';

import 'config/app_config.dart';
import 'config/routes.dart';
import 'config/theme.dart';
import 'core/network/api_client.dart';
import 'core/storage/token_storage.dart';
import 'data/providers/api_provider.dart';
import 'data/providers/mock_api_provider.dart';
import 'data/repositories/alerts_repository.dart';
import 'data/repositories/auth_repository.dart';
import 'data/repositories/bin_repository.dart';
import 'data/repositories/overview_repository.dart';
import 'logic/alerts/alerts_cubit.dart';
import 'logic/auth/auth_cubit.dart';
import 'logic/auth/auth_state.dart';
import 'logic/fund/fund_cubit.dart';
import 'logic/history/history_cubit.dart';
import 'logic/overview/overview_cubit.dart';
import 'presentation/screens/start/start_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await dotenv.load(fileName: '.env');
  } catch (_) {
    try {
      await dotenv.load(fileName: '.env.example');
    } catch (_) {
      // Optional — AppConfig falls back to default BASE_URL
    }
  }

  final tokenStorage = TokenStorage();
  final apiClient = ApiClient(tokenStorage: tokenStorage);
  final AppApi api =
      AppConfig.useMockData ? MockApiProvider() : ApiProvider(apiClient);

  runApp(
    AutoBinApp(
      authRepository: AuthRepository(api: api, tokenStorage: tokenStorage),
      overviewRepository: OverviewRepository(api),
      alertsRepository: AlertsRepository(api),
      binRepository: BinRepository(api),
    ),
  );
}

class AutoBinApp extends StatelessWidget {
  const AutoBinApp({
    super.key,
    required this.authRepository,
    required this.overviewRepository,
    required this.alertsRepository,
    required this.binRepository,
  });

  final AuthRepository authRepository;
  final OverviewRepository overviewRepository;
  final AlertsRepository alertsRepository;
  final BinRepository binRepository;

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider.value(value: authRepository),
        RepositoryProvider.value(value: overviewRepository),
        RepositoryProvider.value(value: alertsRepository),
        RepositoryProvider.value(value: binRepository),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider(create: (_) => AuthCubit(authRepository)..bootstrap()),
          BlocProvider(
            create: (_) => OverviewCubit(overviewRepository, binRepository),
          ),
          BlocProvider(create: (_) => AlertsCubit(alertsRepository)),
          BlocProvider(create: (_) => HistoryCubit(binRepository)),
          BlocProvider(create: (_) => FundCubit(binRepository)),
        ],
        child: MaterialApp(
          title: 'AutoBin',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
          home: const _SessionGate(),
        ),
      ),
    );
  }
}

class _SessionGate extends StatefulWidget {
  const _SessionGate();

  @override
  State<_SessionGate> createState() => _SessionGateState();
}

class _SessionGateState extends State<_SessionGate> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _redirect(context.read<AuthCubit>().state);
    });
  }

  void _redirect(AuthState state) {
    if (!mounted) return;
    if (state is AuthAuthenticated) {
      Navigator.of(context).pushReplacementNamed(AppRoutes.home);
    } else if (state is AuthUnauthenticated) {
      Navigator.of(context).pushReplacementNamed(AppRoutes.start);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthCubit, AuthState>(
      listener: (context, state) => _redirect(state),
      child: const Scaffold(
        backgroundColor: AppColors.background,
        body: Center(
          child: SpinKitPulse(color: AppColors.primary, size: 42),
        ),
      ),
    );
  }
}

class AutoBinPreview extends StatelessWidget {
  const AutoBinPreview({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const StartScreen(),
    );
  }
}
