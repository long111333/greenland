# AutoBin — SQLite database

Schema khớp `SHARED_CONTRACT.md` §3. File DB: `autubin.db`.

## Tables

| Table | Role |
|-------|------|
| `users` | Tài khoản login (bcrypt) |
| `devices` | Thiết bị Edge AI |
| `sort_events` | Sự kiện phân loại (AI ingest) |
| `alerts` | Cảnh báo phần cứng / AI |
| `telemetry_snapshots` | Snapshot dashboard |

## Init (tạo lại sạch)

Từ thư mục này:

```bash
python init_db.py
python init_db.py --force
```

Script sẽ:

1. Xóa `autubin.db` nếu đã có
2. Apply `schema.sql`
3. Seed qua `seed.py` (hash bcrypt bằng passlib — cùng cách FastAPI)
4. Ghi lại `seed.sql` (kèm hash thật) để inspect
5. In count mỗi bảng + verify `admin` / `operator`

## Tài khoản seed

| username | password | role | display_name |
|----------|----------|------|--------------|
| `admin` | `admin123` | admin | Quản trị viên |
| `operator` | `operator123` | operator | Nhân viên vận hành |

Hash `$2b$...` verify được bằng:

```python
from passlib.context import CryptContext
CryptContext(schemes=["bcrypt"], deprecated="auto").verify("admin123", password_hash)
```

Cần `passlib` + `bcrypt==4.0.1` (passlib 1.7.4 **không** tương thích bcrypt 5.x).

```bash
python -m pip install --user "passlib[bcrypt]" "bcrypt==4.0.1"
```

## Seed coverage

- 1 device `BIN_EDGE_AI_001` — ONLINE, Khu A - Sảnh chính
- ≥ 40 `sort_events` (plastic/metal/paper/unknown, ACCEPTED/REJECTED, 2026-10 → 2026-11)
- ≥ 6 `alerts` (BIN_FULL, CAMERA_LOST, SERVO_JAM, ARDUINO_DISCONNECT, AI_LOW_CONFIDENCE; một số `is_resolved=0`)
- ≥ 5 `telemetry_snapshots`
