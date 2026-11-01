# AutoBin Backend

REST API FastAPI khớp `SHARED_CONTRACT.md` v1.0.0.

Base URL dev: `http://127.0.0.1:8000`  
Prefix: `/api/v1`  
DB: `backend/db/autubin.db` (SQLite, đường dẫn resolve tuyệt đối)

## Chạy

Từ thư mục `backend`:

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Tài liệu tương tác: `http://127.0.0.1:8000/docs`  
Health: `GET /health`

Tài khoản demo (bcrypt, đã seed trong DB):

| username | password    | role     |
|----------|-------------|----------|
| admin    | admin123    | admin    |
| operator | operator123 | operator |

Nếu bảng `users` / `devices` trống, startup gọi `app/bootstrap_if_empty.py` và chỉ thêm 2 user + device `BIN_EDGE_AI_001`. Không ghi đè hash bcrypt có sẵn và không chèn `sort_events` / `alerts`.

## Auth

- `POST /api/v1/auth/login` — body `{ "username", "password" }`. Không có đăng ký.
- `POST /api/v1/auth/logout` — Bearer. JWT stateless, response `{ "ok": true }`.
- `GET /api/v1/auth/me` — Bearer.

JWT HS256, hết hạn mặc định 86400 giây. Secret: env `JWT_SECRET` (default dev `autubin-dev-secret-change-me-32bytes`). Xem `.env.example`.

Các route statistics, alerts, devices yêu cầu `Authorization: Bearer <access_token>`.

## Statistics

`GET /api/v1/statistics/overview?device_id=BIN_EDGE_AI_001&period=all`

`period`: `day` | `week` | `month` | `all` (mặc định `all`).

Cửa sổ theo giờ Việt Nam (UTC+7):

- `day` — từ 00:00 hôm nay
- `week` — từ 00:00 thứ Hai tuần này
- `month` — từ 00:00 ngày 1 tháng này
- `all` — mọi `sort_events` của device

Luôn trả 4 class theo thứ tự `plastic`, `metal`, `paper`, `unknown`. `weight_kg` = tổng `weight_g` / 1000. `unresolved_alert_count` là số alert đang mở (không lọc theo period).

## Alerts và devices

- `GET /api/v1/alerts?device_id=BIN_EDGE_AI_001&resolved=false`
- `POST /api/v1/alerts/{alert_id}/resolve`
- `GET /api/v1/devices` — mảng device
- `GET /api/v1/devices/{device_id}`

Alert object có thêm `resolved_at` (null nếu chưa xử lý).

## Ingest (Hardware / Edge AI)

Header: `X-Device-Key: edge-dev-key` (`DEVICE_API_KEY`).

- `POST /api/v1/ingest/sort-event`
- `POST /api/v1/ingest/alert`
- `POST /api/v1/ingest/telemetry`

## Config (public, read-only)

Đọc `integration_configs/` ở thư mục gốc project:

- `GET /api/v1/config/hardware`
- `GET /api/v1/config/ai`
- `GET /api/v1/config/orchestrator`

## Lỗi

Mọi lỗi: `{ "detail": "..." }`.  
400 validation, 401 unauthorized, 404 not found, 500 server.

## Curl

Login:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

Overview (thay `<TOKEN>`):

```bash
curl -s "http://127.0.0.1:8000/api/v1/statistics/overview?device_id=BIN_EDGE_AI_001&period=all" \
  -H "Authorization: Bearer <TOKEN>"
```

Ingest sort event:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/ingest/sort-event \
  -H "Content-Type: application/json" \
  -H "X-Device-Key: edge-dev-key" \
  -d "{\"device_id\":\"BIN_EDGE_AI_001\",\"predicted_class\":\"plastic\",\"confidence\":0.92,\"decision\":\"ACCEPTED\",\"latency_ms\":320,\"weight_g\":28.5,\"image_url\":null,\"raw_ai_payload\":{\"model\":\"MobileNetV3-Small\",\"frames\":7}}"
```

PowerShell dùng `curl.exe` và nhân đôi dấu nháy trong JSON:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{""username"":""admin"",""password"":""admin123""}"
```

## CORS

Dev cho phép mọi origin (`*`), mọi method và header, để Flutter web / emulator gọi được. Bearer token đi trong header, không dùng cookie.
