# AutoBin Mobile

Flutter UI cho thùng phân loại rác Edge AI. Khớp `SHARED_CONTRACT.md`: Start / Login / Overview / Alerts, JWT Bearer, không có đăng ký.

## Cây `lib/`

```text
lib/
├── main.dart
├── config/
│   ├── app_config.dart          # BASE_URL, useMockData, device_id
│   ├── theme.dart               # forest green / mint / Plus Jakarta Sans
│   └── routes.dart
├── core/
│   ├── constants/api_endpoints.dart
│   ├── network/api_client.dart  # Dio + Bearer interceptor
│   ├── network/error_handler.dart
│   ├── storage/token_storage.dart
│   └── utils/formatters.dart
├── data/
│   ├── models/
│   │   ├── user_model.dart
│   │   ├── auth_response.dart
│   │   ├── overview_model.dart
│   │   ├── alert_model.dart
│   │   └── device_model.dart
│   ├── providers/
│   │   ├── api_provider.dart        # AppApi + Dio real driver
│   │   └── mock_api_provider.dart   # cùng JSON shape contract
│   └── repositories/
│       ├── auth_repository.dart
│       ├── overview_repository.dart
│       └── alerts_repository.dart
├── logic/
│   ├── auth/auth_cubit.dart + auth_state.dart
│   ├── overview/overview_cubit.dart + overview_state.dart
│   └── alerts/alerts_cubit.dart + alerts_state.dart
└── presentation/
    ├── screens/
    │   ├── start/start_screen.dart
    │   ├── auth/login_screen.dart
    │   ├── overview/overview_screen.dart
    │   └── alerts/alerts_screen.dart
    └── widgets/
        ├── recycle_illustration.dart
        ├── category_card.dart
        ├── summary_card.dart
        ├── app_buttons.dart
        └── severity_badge.dart
```

## Cách chạy

Flutter SDK **có thể chưa có** trên máy. Cài [Flutter ≥ 3.19](https://docs.flutter.dev/get-started/install) rồi:

```bash
cd D:\AutoBin\mobile

# Tạo android/ ios/ windows/ web/ nếu chưa có (project được scaffold thủ công)
flutter create . --project-name autobin

flutter pub get

# Backend thật (mặc định) — chạy backend :8000 trước
flutter run -d windows
# hoặc Chrome
flutter run -d chrome
```

### Android emulator

`127.0.0.1` trong emulator là chính máy ảo, không phải host. Đổi `.env`:

```env
API_BASE_URL=http://10.0.2.2:8000
```

hoặc:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### Chạy không cần backend (mock)

```bash
flutter run --dart-define=USE_MOCK=true
```

hoặc trong `.env`: `USE_MOCK=true`.

Demo login: **admin / admin123** (hoặc `operator / operator123` khi mock).

## Endpoints (khớp contract)

| Màn hình | Method | Path |
|----------|--------|------|
| Login | `POST` | `/api/v1/auth/login` body `{username, password}` |
| Logout | `POST` | `/api/v1/auth/logout` Bearer |
| Session restore | `GET` | `/api/v1/auth/me` Bearer |
| Overview | `GET` | `/api/v1/statistics/overview?device_id=BIN_EDGE_AI_001&period=all\|day\|week\|month` |
| Alerts | `GET` | `/api/v1/alerts?device_id=BIN_EDGE_AI_001&resolved=false` |
| Resolve | `POST` | `/api/v1/alerts/{alert_id}/resolve` |

`ApiClient` gắn `Authorization: Bearer <access_token>` cho mọi request sau login. Token lưu `flutter_secure_storage`, xóa khi logout.

## Mock vs real

| | Real (`useMockData = false`, mặc định) | Mock (`USE_MOCK=true`) |
|--|----------------------------------------|------------------------|
| Driver | `ApiProvider` + Dio → `AppConfig.baseUrl` | `MockApiProvider` |
| Login | Backend JWT | `mock-jwt-admin` |
| Overview / Alerts | JSON DB thật | Cùng shape contract (4 class + 3 unresolved) |
| Khi nào dùng | Backend đã chạy `:8000` | UI/dev khi API tắt |

Đổi URL: `.env` `API_BASE_URL` hoặc `--dart-define=API_BASE_URL=...`. Default `http://127.0.0.1:8000`.

## Design tokens

- Primary `#1B5E3B`, mint `#D8F3DC`, text secondary `#7A8B7E`
- Card radius 20, button radius 28
- Font: Plus Jakarta Sans (`google_fonts`)
- Overview: icon + label + `weight_kg` + **count** bên phải (không dùng $)
- Nút đáy: `Xem cảnh báo` nếu `unresolved_alert_count > 0`, không thì `Làm mới`
