# HƯỚNG DẪN TRIỂN KHAI VÀ TÍCH HỢP DỰ ÁN MOBILE (FLUTTER)
**Dự án:** Thùng Phân Loại Rác Tự Động Tích Hợp Edge AI  
**Vai trò:** Lập trình viên Ứng dụng Mobile  
**Phiên bản tài liệu:** 1.0.0

---

## 1. TỔNG QUAN VÀ CHIẾN LƯỢC NGHỆ THUẬT MERGE (TÁCH BIỆT VAI TRÒ)

Để đảm bảo việc phát triển ứng dụng Mobile độc lập, không bị phụ thuộc vào tiến độ phần cứng (Arduino/Pi) hay mô hình AI, kiến trúc dự án sẽ sử dụng **Interface-first Strategy** (Định nghĩa giao tiếp trước, cài đặt chi tiết sau) và **Mock Service Driver**.

### Nguyên tắc phối hợp:
1. **Mobile App KHÔNG kết nối trực tiếp đến Arduino/Pi qua Serial hay Bluetooth.** Mobile chỉ giao tiếp với **Backend REST API** (hoặc WebSocket).
2. Các tệp cấu hình phần cứng, mô hình AI và cấu hình hệ thống sẽ được module hóa dưới dạng các tệp JSON/Env chuẩn hóa.
3. Team Mobile hoàn thiện giao diện và logic dựa trên Mock API / Local Test Server trước. Khi Hardware và AI hoàn tất, chỉ cần đổi `API Base URL` để kết nối toàn hệ thống.

---

## 2. MÔI TRƯỜNG PHÁT TRIỂN VÀ THƯ VIỆN CẦN CÀI ĐẶT

### 2.1. Yêu cầu môi trường
* **Flutter SDK:** `>= 3.19.0` (Dart SDK `>= 3.3.0`)
* **Môi trường build:** 
  * Android Studio / VS Code + Flutter Extension
  * Android SDK (API level 21 trở lên - Android 5.0+)
  * Xcode (Nếu cần build iOS - macOS bắt buộc)
* **Tool test API:** Postman hoặc Bruno

### 2.2. Thư viện Dependencies (`pubspec.yaml`)

Thêm các package sau vào tệp `pubspec.yaml` của dự án Flutter:

```yaml
dependencies:
  flutter:
    sdk: flutter

  # Quản lý Trạng thái (State Management)
  flutter_bloc: ^8.1.3
  
  # Kết nối Mạng & API
  http: ^1.2.0
  dio: ^5.4.1
  web_socket_channel: ^2.4.1 # Dùng cho cập nhật trạng thái thời gian thực
  
  # Lưu trữ cục bộ & Token
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0

  # Biểu đồ & Đồ họa (Thống kê rác)
  fl_chart: ^0.66.2

  # Định dạng ngày tháng, số liệu
  intl: ^0.19.0
  
  # UI & Helpers
  google_fonts: ^6.1.0
  flutter_spinkit: ^5.2.0
  cached_network_image: ^3.3.1
  flutter_dotenv: ^5.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

---

## 3. CẤU TRÚC THƯ MỤC DỰ ÁN FLUTTER

Thư mục `lib/` được thiết kế theo mô hình **Clean Architecture / Layered Architecture**:

```text
lib/
├── main.dart                   # Điểm khởi chạy ứng dụng
├── config/                     # Cấu hình môi trường & hằng số
│   ├── app_config.dart
│   ├── theme.dart
│   └── routes.dart
├── core/                       # Các tiện ích chung, Network Client
│   ├── constants/
│   │   └── api_endpoints.dart
│   ├── network/
│   │   ├── api_client.dart
│   │   └── error_handler.dart
│   └── utils/
│       └── formatters.dart
├── data/                       # Xử lý dữ liệu & Gọi API
│   ├── models/
│   │   ├── device_model.dart
│   │   ├── sort_event_model.dart
│   │   ├── telemetry_model.dart
│   │   └── alert_model.dart
│   ├── providers/              # Mock Data Driver & Real API Driver
│   │   ├── api_provider.dart
│   │   └── mock_api_provider.dart
│   └── repositories/
│       └── trash_bin_repository.dart
├── logic/                      # Quản lý trạng thái (BLoC / Cubit)
│   ├── auth/
│   ├── dashboard/
│   ├── history/
│   └── statistics/
├── presentation/               # Giao diện người dùng (UI)
│   ├── screens/
│   │   ├── auth/
│   │   │   └── login_screen.dart
│   │   ├── dashboard/
│   │   │   └── dashboard_screen.dart
│   │   ├── history/
│   │   │   └── history_screen.dart
│   │   ├── statistics/
│   │   │   └── statistics_screen.dart
│   │   ├── alerts/
│   │   │   └── alerts_screen.dart
│   │   └── settings/
│   │       ├── settings_screen.dart
│   │       └── hardware_ai_config_view.dart # Màn hình xem cấu hình HW & AI
│   └── widgets/
│       ├── status_badge.dart
│       ├── trash_chart.dart
│       └── event_card.dart
└── integration_configs/        # Tệp cấu hình giao tiếp giữa các bên (Tách biệt)
    ├── hardware_config.json    # Team Hardware cập nhật
    ├── ai_config.json          # Team AI cập nhật
    └── orchestrator_config.json # Team System/Pi cập nhật
```

---

## 4. BỘ CẤU HÌNH TRUNG GIẢN (CONFIG FILES CHO TEAM PHẦN CỨNG & AI)

Để tránh việc sửa code Flutter khi team AI hay Hardware đổi chân cắm / đổi mô hình, các file cấu hình sau sẽ được đặt ở backend hoặc lưu dạng tệp JSON tĩnh trong ứng dụng để hiển thị/quản lý thông số.

### 4.1. Tệp Cấu Hình Phần Cứng (`hardware_config.json`)
*Dành riêng cho Team Hardware/Arduino điền và kiểm tra:*

```json
{
  "hardware_version": "V1.0-ArduinoUno",
  "pin_mapping": {
    "servo_gate_sg90": {
      "pin": "D9",
      "description": "Servo cửa chặn (Cửa xả rác)",
      "safe_angle_min": 0,
      "safe_angle_max": 90
    },
    "servo_turntable_high_torque": {
      "pin": "D10",
      "description": "Servo máng xoay 3 ngăn",
      "positions": {
        "plastic": 0,
        "metal": 60,
        "paper": 120,
        "home": 180
      }
    },
    "distance_sensor_hopper": {
      "pin": "A0",
      "type": "Ultrasonic/Infrared",
      "description": "Cảm biến khoảng cách kiểm tra rác đầu vào"
    },
    "bin_full_sensors": {
      "plastic_bin": {"pin": "A1", "threshold_cm": 5.0},
      "metal_bin": {"pin": "A2", "threshold_cm": 5.0},
      "paper_bin": {"pin": "A3", "threshold_cm": 5.0}
    }
  },
  "serial_communication": {
    "baud_rate": 115200,
    "port_default": "/dev/ttyACM0",
    "timeout_ms": 3000
  }
}
```

### 4.2. Tệp Cấu Hình Mô Hình AI (`ai_config.json`)
*Dành riêng cho Team AI Model điền và cập nhật:*

```json
{
  "ai_framework": "TFLite / ONNX",
  "active_model": "MobileNetV3-Small",
  "confidence_threshold": 0.75,
  "frame_confirmation_count": 5,
  "total_sample_frames": 7,
  "classes": [
    "plastic",
    "metal",
    "paper",
    "unknown"
  ],
  "models_benchmark": {
    "MobileNetV3-Small": {
      "input_size": "224x224",
      "avg_latency_ms": 45,
      "target_fps": 18,
      "accuracy": 0.88
    },
    "YOLO-Nano": {
      "input_size": "320x320",
      "avg_latency_ms": 110,
      "target_fps": 8,
      "accuracy": 0.91
    }
  }
}
```

### 4.3. Tệp Cấu Hình Hệ Thống Điều Phối (`orchestrator_config.json`)
*Tệp kết nối điều phối toàn bộ hệ thống (Pi 4 Backend Controller):*

```json
{
  "device_id": "BIN_EDGE_AI_001",
  "system_mode": "AUTO",
  "camera": {
    "device_index": 0,
    "resolution": "1280x720",
    "fps": 30
  },
  "sync_interval_seconds": 10,
  "backend_endpoint": "https://api.trashbin-ai.com/v1",
  "offline_sqlite_backup": true
}
```

---

## 5. CÁC MÀN HÌNH NGHỆ THUẬT VÀ TÍNH NĂNG MOBILE CẦN PHÁT TRIỂN

Ứng dụng Mobile gồm **6 Màn hình chính**:

| Màn hình | Chức năng chính | Giao tiếp API |
| :--- | :--- | :--- |
| **1. Đăng nhập (Auth)** | Đăng nhập tài khoản quản trị/giám sát. | `POST /api/v1/auth/login` |
| **2. Tổng quan (Dashboard)** | Xem trạng thái realtime của thùng rác (Online/Offline, RAM/CPU/Nhiệt độ Pi, trạng thái servo, kết nối camera/Arduino). | `GET /api/v1/devices/telemetry`<br>`GET /api/v1/devices` |
| **3. Thống kê (Statistics)** | Biểu đồ tỉ lệ phân loại theo loại rác (Nhựa, Kim loại, Giấy, UNKNOWN) theo Ngày/Tuần/Tháng. | `GET /api/v1/statistics` |
| **4. Lịch sử (History)** | Danh sách các lượt phân loại rác, thời gian xử lý, độ tin cậy (confidence), hình ảnh cắt từ camera (nếu có). | `GET /api/v1/events` |
| **5. Cảnh báo (Alerts)** | Danh sách cảnh báo (Thùng rác đầy, mất camera, kẹt servo, mất kết nối Arduino, lỗi AI confidence thấp). | `GET /api/v1/alerts` |
| **6. Cấu hình (Settings & Specs)**| Xem thông số phần cứng (`hardware_config`), thông số AI (`ai_config`) và kiểm tra lệnh khẩn cấp (HOME/STOP). | `POST /api/v1/commands` |

---

## 6. MOCK DATA DRIVER (ĐỂ MOBILE CHẠY ĐỘC LẬP TẠI THỜI ĐIỂM NÀY)

Tạo một tệp `lib/data/providers/mock_api_provider.dart` để trả về dữ liệu giả định ngay cả khi backend hoặc hardware chưa xong.

```dart
// lib/data/providers/mock_api_provider.dart

class MockApiProvider {
  static Future<Map<String, dynamic>> getTelemetry() async {
    await Future.delayed(const Duration(milliseconds: 500)); // Giả lập độ trễ mạng
    return {
      "device_id": "BIN_EDGE_AI_001",
      "status": "ONLINE",
      "cpu_pct": 34.5,
      "ram_mb": 1240,
      "temperature_c": 48.2,
      "fps": 17.5,
      "serial_status": "CONNECTED",
      "camera_status": "OK",
      "bins_capacity": {
        "plastic": 65, // %
        "metal": 20,
        "paper": 45
      }
    };
  }

  static Future<List<Map<String, dynamic>>> getSortEvents() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      {
        "event_id": "evt_101",
        "timestamp": DateTime.now().subtract(const Duration(minutes: 2)).toIso8601String(),
        "predicted_class": "plastic",
        "confidence": 0.92,
        "decision": "ACCEPTED",
        "latency_ms": 320,
        "image_url": "https://via.placeholder.com/150"
      },
      {
        "event_id": "evt_102",
        "timestamp": DateTime.now().subtract(const Duration(minutes: 10)).toIso8601String(),
        "predicted_class": "metal",
        "confidence": 0.87,
        "decision": "ACCEPTED",
        "latency_ms": 290,
        "image_url": null
      },
      {
        "event_id": "evt_103",
        "timestamp": DateTime.now().subtract(const Duration(minutes: 25)).toIso8601String(),
        "predicted_class": "unknown",
        "confidence": 0.45,
        "decision": "REJECTED",
        "latency_ms": 410,
        "image_url": null
      }
    ];
  }
}
```

---

## 7. QUY TRÌNH HỢP NHẤT (MERGE CHECKLIST)

Khi Team Hardware, Team AI và Team Backend bàn giao sản phẩm:

1. **Bước 1:** Kiểm tra kết nối API thật bằng cách cập nhật `BASE_URL` trong tệp `lib/config/app_config.dart`.
2. **Bước 2:** Chuyển đổi cờ `useMockData = false` trong repository layer.
3. **Bước 3:** Nhập các tệp JSON cấu hình thực tế (`hardware_config.json`, `ai_config.json`) vào backend/assets để ứng dụng Mobile tải về hiển thị chính xác các thông số chân cắm và tham số AI.
4. **Bước 4:** Test luồng hiển thị thông báo thời gian thực (Push Notification hoặc WebSocket) khi hệ thống báo thùng đầy hoặc kẹt kẹt servo.

---

## 8. DANH SÁCH LẦN CẦN XÁC NHẬN VỚI TỪNG TEAM

* **Với Team Hardware:**
  * Đã thống nhất địa chỉ chân cắm servo `D9`, `D10` chưa?
  * Trạng thái đầy thùng báo theo % hay báo nhị phân (Full / Not Full)?
* **Với Team AI:**
  * Ngưỡng Confidence mặc định chốt ở mức bao nhiêu (hiện tại: 0.75)?
  * Tên các lớp xuất ra chuẩn định dạng chữ thường (`plastic`, `metal`, `paper`, `unknown`).
* **Với Team Backend:**
  * Định dạng Auth token (Bearer JWT).
  * Chuẩn hóa API theo tài liệu mục 8.3 của dự án.
```

eof