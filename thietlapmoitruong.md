# Thiết lập môi trường — Greenland / AutoBin

Hướng dẫn pull repo và chạy app giống môi trường phát triển hiện tại  
(Flutter mobile + FastAPI + SQLite mẫu).

**Repo:** https://github.com/long111333/greenland

---

## 1. Yêu cầu hệ thống

| Thành phần | Gợi ý |
|------------|--------|
| Git | Đã cài |
| Python | 3.11+ (đã test trên 3.15) |
| Flutter SDK | 3.19+ / stable (ví dụ 3.47) |
| Visual Studio (Windows desktop) | Workload **Desktop development with C++** |
| Developer Mode (Windows) | Bật nếu build plugin Windows cần symlink |

Không bắt buộc Android SDK nếu chỉ chạy Windows / Edge (web).

---

## 2. Clone dự án

```bash
git clone https://github.com/long111333/greenland.git
cd greenland
```

---

## 3. Cơ sở dữ liệu mẫu (SQLite)

Repo kèm file DB đã seed sẵn:

```text
backend/db/sample/autubin.sample.db
```

### Cách dùng DB mẫu

**Windows (PowerShell):**

```powershell
Copy-Item backend\db\sample\autubin.sample.db backend\db\autubin.db -Force
```

**macOS / Linux:**

```bash
cp backend/db/sample/autubin.sample.db backend/db/autubin.db
```

Backend sẽ đọc `backend/db/autubin.db` khi khởi động.

### Tài khoản demo trong DB mẫu

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `operator` | `operator123` | operator |

DB mẫu gồm khoảng **52** sự kiện phân loại, alerts, telemetry (có ngăn gần đầy ≥ 90% để thử nút Clean đỏ).

### Tạo lại DB từ script (tuỳ chọn)

Nếu muốn regenerate thay vì dùng file mẫu:

```bash
cd backend/db
python -m pip install passlib==1.7.4 bcrypt==4.0.1
python init_db.py
```

Lệnh này ghi đè `backend/db/autubin.db`.

---

## 4. Backend (FastAPI)

```bash
cd backend
python -m pip install -r requirements.txt
```

Tạo file môi trường (tuỳ chọn):

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

Chạy API (khuyến nghị port **8001** nếu máy đã dùng 8000 cho dịch vụ khác):

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Kiểm tra:

- Health: http://127.0.0.1:8001/health  
- Docs: http://127.0.0.1:8001/docs  

### Lưu ý Windows / SQLite

API dùng `check_same_thread=False` để tương thích FastAPI threadpool. Không cần chỉnh thêm.

---

## 5. Mobile (Flutter)

```bash
cd mobile
```

Nếu thiếu folder platform (`android/`, `windows/`, …):

```bash
flutter create . --project-name autobin --org com.autubin
```

Cài package:

```bash
flutter pub get
```

Tạo `.env` (copy từ example):

```bash
copy .env.example .env    # Windows
```

Nội dung gợi ý:

```env
API_BASE_URL=http://127.0.0.1:8001
USE_MOCK=false
```

- **Windows / Chrome / Edge:** `http://127.0.0.1:8001`  
- **Android emulator:** `http://10.0.2.2:8001`

Chạy app:

```bash
# Windows desktop
flutter run -d windows --dart-define=API_BASE_URL=http://127.0.0.1:8001

# Edge (web)
flutter run -d edge --dart-define=API_BASE_URL=http://127.0.0.1:8001
```

Đăng nhập: `admin` / `admin123`.

---

## 6. Luồng kiểm thử nhanh

1. Mở Overview → thấy thống kê 4 loại rác + Summary (Location / Date / Total).  
2. Nếu thùng ≥ 90% → nút **Clean** màu đỏ.  
3. Bấm **Clean** → dữ liệu chuyển sang **History**.  
4. **Your Fund** → tổng tiền (nhựa × 2000, kim loại × 20000, giấy × 3000 ₫/kg).  
5. **Contact to buy** → popup SĐT / email người thu mua.  
6. **Account** → My Profile / Security (đổi mật khẩu).

---

## 7. Cấu trúc thư mục quan trọng

```text
greenland/
├── thietlapmoitruong.md          ← file này
├── SHARED_CONTRACT.md            ← contract API chung
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── db/
│       ├── sample/autubin.sample.db   ← DB mẫu
│       ├── init_db.py
│       ├── schema.sql
│       └── seed.py
├── mobile/                       ← Flutter app
└── integration_configs/          ← hardware / AI / orchestrator JSON
```

---

## 8. Sự cố thường gặp

| Triệu chứng | Cách xử lý |
|-------------|------------|
| `Internal Server Error` + SQLite thread | Đảm bảo đã pull bản mới (`check_same_thread=False` trong `app/db.py`) và restart uvicorn |
| Port 8000 bị chiếm (XAMPP/Laravel) | Chạy API ở **8001**, chỉnh `API_BASE_URL` tương ứng |
| Flutter Windows: symlink / Developer Mode | Bật Developer Mode Windows |
| Flutter Windows: thiếu toolchain | Cài Visual Studio + **Desktop development with C++** |
| Login sai | Dùng `admin` / `admin123` từ DB mẫu |
| Overview trống sau Clean | Bình thường — rác đã sang History; chạy lại `init_db.py` hoặc copy lại `autubin.sample.db` |

---

## 9. Liên hệ demo thu mua (trong app)

- Phone: `0325916822`  
- Email: `truongngoclong.21072005@gmail.com`
