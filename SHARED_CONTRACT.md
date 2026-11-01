# AutoBin — Shared Contract (Single Source of Truth)

> Mọi nhánh (Backend / DB / Flutter UI) **BẮT BUỘC** tuân thủ file này.
> Mục tiêu: Mobile ↔ Backend ↔ DB khớp 100%; sẵn sàng gắn Hardware + Edge AI sau này
> (Mobile **không** nối Serial/Bluetooth trực tiếp — chỉ REST/WebSocket).

**Version:** `1.0.0`  
**Base URL (dev):** `http://127.0.0.1:8000`  
**API prefix:** `/api/v1`  
**Auth:** Bearer JWT (`Authorization: Bearer <access_token>`)

---

## 1. Domain constants (khớp Hardware + AI)

### Waste classes (lowercase — khớp `ai_config.json`)
| class_id   | display_vi | display_en | estimated_avg_weight_g |
|------------|------------|------------|------------------------|
| `plastic`  | Nhựa       | Plastic    | 25                     |
| `metal`    | Kim loại   | Metal      | 40                     |
| `paper`    | Giấy       | Paper      | 15                     |
| `unknown`  | Không rõ   | Unknown    | 20                     |

### Device
- Default device: `BIN_EDGE_AI_001`
- System modes: `AUTO` | `MANUAL` | `STOP` | `HOME`

### Alert types
`BIN_FULL` | `CAMERA_LOST` | `SERVO_JAM` | `ARDUINO_DISCONNECT` | `AI_LOW_CONFIDENCE` | `OVERHEAT` | `SYSTEM`

### Alert severity
`info` | `warning` | `critical`

### Sort decision
`ACCEPTED` | `REJECTED`

---

## 2. Folder ownership (tránh đụng file)

| Nhánh | Path sở hữu | Không được sửa |
|-------|-------------|----------------|
| **DB** | `backend/db/` (schema SQL, seed, migrations) | `mobile/`, `backend/app/` |
| **Backend** | `backend/app/`, `backend/requirements.txt`, `backend/main.py`, `backend/README.md` | `mobile/lib/presentation/` |
| **UI** | `mobile/` (toàn bộ Flutter app) | `backend/db/` |

Shared reference only: `SHARED_CONTRACT.md`, `huongdantrienkhai.md`, `integration_configs/`

---

## 3. Database schema (SQLite file: `backend/db/autubin.db`)

### `users`
| column | type | notes |
|--------|------|-------|
| id | INTEGER PK | |
| username | TEXT UNIQUE NOT NULL | demo: `admin` |
| password_hash | TEXT NOT NULL | bcrypt |
| display_name | TEXT | |
| role | TEXT | `admin` \| `operator` \| `viewer` |
| created_at | TEXT ISO8601 | |

### `devices`
| column | type | notes |
|--------|------|-------|
| id | TEXT PK | `BIN_EDGE_AI_001` |
| name | TEXT | |
| location | TEXT | địa chỉ hiển thị overview |
| status | TEXT | `ONLINE` \| `OFFLINE` \| `ERROR` |
| hardware_version | TEXT | |
| created_at | TEXT | |

### `sort_events`  ← sự kiện từ Edge AI (ingest sau này)
| column | type | notes |
|--------|------|-------|
| id | TEXT PK | `evt_...` |
| device_id | TEXT FK → devices | |
| timestamp | TEXT ISO8601 | |
| predicted_class | TEXT | plastic/metal/paper/unknown |
| confidence | REAL | 0..1 |
| decision | TEXT | ACCEPTED/REJECTED |
| latency_ms | INTEGER | |
| weight_g | REAL | cân nặng ước tính hoặc cảm biến |
| image_url | TEXT NULL | |
| raw_ai_payload | TEXT NULL | JSON dump để debug AI |

### `alerts`
| column | type | notes |
|--------|------|-------|
| id | TEXT PK | |
| device_id | TEXT FK | |
| type | TEXT | alert types ở trên |
| severity | TEXT | |
| title | TEXT | |
| message | TEXT | |
| is_resolved | INTEGER 0/1 | |
| created_at | TEXT | |
| resolved_at | TEXT NULL | |

### `telemetry_snapshots` (optional cho dashboard sau)
| column | type | notes |
|--------|------|-------|
| id | INTEGER PK | |
| device_id | TEXT | |
| recorded_at | TEXT | |
| cpu_pct | REAL | |
| ram_mb | REAL | |
| temperature_c | REAL | |
| fps | REAL | |
| serial_status | TEXT | |
| camera_status | TEXT | |
| bin_plastic_pct | REAL | |
| bin_metal_pct | REAL | |
| bin_paper_pct | REAL | |

### Seed accounts
- `admin` / `admin123` (role: admin)
- `operator` / `operator123` (role: operator)

Seed ≥ 40 `sort_events` phân bố 4 class, ≥ 6 `alerts` (một số unresolved).

---

## 4. REST API

### 4.1 Auth — không có đăng ký

#### `POST /api/v1/auth/login`
Request:
```json
{ "username": "admin", "password": "admin123" }
```
Response `200`:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "admin",
    "display_name": "Quản trị viên",
    "role": "admin"
  }
}
```
Errors: `401` `{ "detail": "Invalid credentials" }`

#### `POST /api/v1/auth/logout`
Header: Bearer required. Response `200`: `{ "ok": true }`  
(JWT stateless — client xóa token; endpoint để đồng bộ UX)

#### `GET /api/v1/auth/me`
Header: Bearer. Response user object như trên.

---

### 4.2 Statistics (Overview screen)

#### `GET /api/v1/statistics/overview?device_id=BIN_EDGE_AI_001&period=day`
`period`: `day` | `week` | `month` | `all` (default `all`)

Response `200`:
```json
{
  "device_id": "BIN_EDGE_AI_001",
  "device_name": "Thùng Edge AI #001",
  "location": "Khu A - Sảnh chính",
  "period": "all",
  "as_of": "2026-11-01T02:00:00Z",
  "categories": [
    {
      "class_id": "plastic",
      "label": "Nhựa",
      "count": 42,
      "weight_kg": 1.05,
      "weight_g": 1050,
      "accepted": 40,
      "rejected": 2
    },
    {
      "class_id": "metal",
      "label": "Kim loại",
      "count": 18,
      "weight_kg": 0.72,
      "weight_g": 720,
      "accepted": 17,
      "rejected": 1
    },
    {
      "class_id": "paper",
      "label": "Giấy",
      "count": 31,
      "weight_kg": 0.465,
      "weight_g": 465,
      "accepted": 30,
      "rejected": 1
    },
    {
      "class_id": "unknown",
      "label": "Không rõ",
      "count": 7,
      "weight_kg": 0.14,
      "weight_g": 140,
      "accepted": 0,
      "rejected": 7
    }
  ],
  "totals": {
    "count": 98,
    "weight_kg": 2.375,
    "accepted": 87,
    "rejected": 11
  },
  "unresolved_alert_count": 3
}
```

**UI mapping (Overview):**
- List row: icon + label + `weight_kg` dưới tên + **count** bên phải (thay cho giá $ trong mockup)
- Bottom card: `location`, `as_of` (date), tổng `weight_kg` / `count`, nút xem alerts

---

### 4.3 Alerts

#### `GET /api/v1/alerts?device_id=BIN_EDGE_AI_001&resolved=false`
Response:
```json
{
  "items": [
    {
      "id": "alt_001",
      "device_id": "BIN_EDGE_AI_001",
      "type": "BIN_FULL",
      "severity": "warning",
      "title": "Thùng nhựa gần đầy",
      "message": "Ngăn plastic đạt 92% dung tích",
      "is_resolved": false,
      "created_at": "2026-11-01T01:10:00Z"
    }
  ],
  "total": 1
}
```

#### `POST /api/v1/alerts/{alert_id}/resolve`
Response: alert object với `is_resolved: true`

---

### 4.4 Devices (chuẩn bị HW)

#### `GET /api/v1/devices`
#### `GET /api/v1/devices/{device_id}`

---

### 4.5 Ingest hooks (Hardware / AI — implement stub, sẵn sàng)

#### `POST /api/v1/ingest/sort-event`  (Pi/Edge gọi sau khi AI phân loại)
```json
{
  "device_id": "BIN_EDGE_AI_001",
  "predicted_class": "plastic",
  "confidence": 0.92,
  "decision": "ACCEPTED",
  "latency_ms": 320,
  "weight_g": 28.5,
  "image_url": null,
  "raw_ai_payload": { "model": "MobileNetV3-Small", "frames": 7 }
}
```
Auth: có thể dùng device API key header `X-Device-Key: edge-dev-key` (dev).

#### `POST /api/v1/ingest/alert`
```json
{
  "device_id": "BIN_EDGE_AI_001",
  "type": "SERVO_JAM",
  "severity": "critical",
  "title": "Kẹt servo máng xoay",
  "message": "Servo D10 không đạt góc metal"
}
```

#### `POST /api/v1/ingest/telemetry`
(body khớp `telemetry_snapshots`)

---

### 4.6 Config read-only (từ `integration_configs/`)

#### `GET /api/v1/config/hardware`
#### `GET /api/v1/config/ai`
#### `GET /api/v1/config/orchestrator`

---

## 5. Flutter UI scope (MVP lần này)

### Màn hình bắt buộc
1. **Start / Welcome** — đúng aesthetic ảnh: nền trắng, vòng xanh forest, headline, mô tả, nút "Start now" → Login
2. **Login** — username/password, **không** có đăng ký; gọi `POST /auth/login`; lưu JWT secure storage
3. **Overview (Thống kê)** — layout kiểu "My cart" trong ảnh:
   - Title: `Tổng quan` / `Overview`
   - List 4 category cards mint green: icon + tên + cân nặng (kg) + **số lượng** bên phải
   - Bottom sheet card: địa điểm thiết bị, ngày, tổng cân nặng/số lượng, nút tới Alerts hoặc Refresh
   - Icon logout trên app bar
4. **Alerts** — danh sách lỗi/bất cập từ API; có thể sheet/simple list
5. **Logout** — xóa token, về Start hoặc Login

### Design tokens (khớp ảnh)
```
primary:        #1B5E3B  (forest green)
primaryDark:    #0F3D26
mint:           #D8F3DC  / #C8E6C9
background:     #FFFFFF
textPrimary:    #1B5E3B
textSecondary:  #7A8B7E
cardRadius:     20
buttonRadius:   28
```

### Flutter architecture (rút gọn từ huongdantrienkhai)
```
mobile/lib/
  main.dart
  config/app_config.dart   # BASE_URL, useMockData
  config/theme.dart
  config/routes.dart
  core/network/api_client.dart
  core/constants/api_endpoints.dart
  data/models/...
  data/providers/api_provider.dart
  data/providers/mock_api_provider.dart  # fallback nếu backend tắt
  data/repositories/...
  logic/auth/...
  logic/overview/...
  logic/alerts/...
  presentation/screens/start/...
  presentation/screens/auth/login_screen.dart
  presentation/screens/overview/overview_screen.dart
  presentation/screens/alerts/alerts_screen.dart
  presentation/widgets/...
```

`app_config.dart`:
```dart
class AppConfig {
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator → host
  );
  static const useMockData = bool.fromEnvironment('USE_MOCK', defaultValue: false);
  static const defaultDeviceId = 'BIN_EDGE_AI_001';
}
```

Windows desktop/chrome: dùng `http://127.0.0.1:8000`.

---

## 6. integration_configs (copy từ tài liệu dự án)

Giữ tại `integration_configs/hardware_config.json`, `ai_config.json`, `orchestrator_config.json`  
Backend serve read-only; UI có thể hiển thị sau (không bắt buộc MVP này).

---

## 7. Error envelope

Mọi lỗi API:
```json
{ "detail": "Human readable message" }
```
HTTP: 400 validation, 401 unauthorized, 404 not found, 500 server.

---

## 8. Acceptance checklist (cả 3 nhánh)

- [ ] Login `admin`/`admin123` trả JWT
- [ ] Overview hiển thị 4 class + count + weight_kg từ DB thật
- [ ] Alerts hiển thị unresolved từ DB
- [ ] Logout về màn Start/Login
- [ ] `POST /ingest/sort-event` ghi DB → Overview tăng số liệu
- [ ] Đổi `BASE_URL` / tắt mock là nối backend thật
- [ ] Không có màn đăng ký
- [ ] Class names lowercase khớp AI config
