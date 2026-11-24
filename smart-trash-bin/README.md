# Smart Trash Bin – Arduino Uno và USB client Windows/Raspberry Pi

Firmware điều khiển hai servo của cùng một cửa giữ rác, xoay ống tới bốn dấu màu và giám sát mức đầy của một ngăn. Máy tính Windows có thể đóng vai Raspberry Pi, dùng Python client gửi JSON Lines qua USB tới Arduino và các linh kiện thật. Chưa triển khai AI, camera, server hoặc mobile app.

## Cấu trúc và kiến trúc

```text
firmware/
  platformio.ini
  include/{config.h,pins.h,protocol.h,loadcell_calibration.h}
  src/
    main.cpp
    controllers/{ServoController,StepperController,SortingController}.{h,cpp}
    sensors/{ColorSensor,UltrasonicSensor,LoadCellSensor}.{h,cpp}
    communication/SerialProtocol.{h,cpp}
    safety/SafetyManager.{h,cpp}
  test/{run_host_tests.py,host/}
raspberry/hardware/
  arduino_client.py
  test_serial.py              # Console, probe, dò cổng, kiểm thử có hướng dẫn
  manual_test.py              # Quy trình kiểm thử thật và báo cáo JSON
  test_client.py              # Kiểm thử offline với serial giả
  test_loadcell.py            # Đọc cân / tare / hiệu chuẩn, tự lưu EEPROM và project
  requirements.txt
setup_client.ps1
run_client.ps1
run_client.cmd
```

`main.cpp` tích hợp các module. Servo dùng một tiến trình góc chung theo `millis()`, stepper dùng AccelStepper half-step và gọi `run()` liên tục. GY-33 đọc theo chu kỳ, có timeout I2C. HC-SR04 dùng interrupt D3, median và hysteresis. UART dùng bộ đệm cố định, ArduinoJson 6 và TX không đợi truyền hết; không dùng String hoặc delay trong logic vận hành.

```text
INIT --CLOSE_GATE hoàn tất--> INIT --HOME--> VERIFY_POSITION
HOME bắt đầu VERIFY_POSITION: đang ở đỏ thì COMPLETE --> IDLE
VERIFY_POSITION --chưa ở đỏ--> HOMING --nhận đỏ, dừng, xác minh lại--> COMPLETE --> IDLE
IDLE --SORT--> ROTATING --> VERIFY_POSITION --> OPENING
OPENING --> HOLDING --> CLOSING --> COMPLETE --> IDLE
lỗi / STOP --> ERROR --RESET_ERROR--> INIT
```

INIT/IDLE đợi lệnh; không tự chuyển động. HOME và SORT tìm liên tục theo chiều cấu hình; HOME tối đa 60 s, SORT tối đa 40 s và tổng `SEARCH_STEPS` cho toàn bộ lần tìm hiện là 15.000 half-step. Thấy một mẫu mới nhận diện đúng đích thì dừng tại đó, giữ cuộn dây và xác minh lịch sử màu mới tối đa 1.500 ms. Nếu mẫu đích giả, tiếp tục cùng chiều với ngân sách bước/thời gian còn lại, tối đa 3 lần bắt đích. Không còn vòng dừng–đảo bước nhỏ theo vị trí ước lượng. Cửa có timeout 4 s mỗi hành trình; sai vị trí không mở cửa.

## Thông số đã cập nhật theo sketch người dùng

| Hạng mục | Cấu hình |
|---|---|
| Servo 1 / 2 | D6 / D7 |
| Góc đóng / mở | 0° / 180°, cả hai servo cùng chiều (`SERVO_2_REVERSED=false`) |
| Thời gian servo | Hành trình 2.700 ms + ổn định 400 ms; giữ cửa mở 1.200 ms |
| Stepper | HALF4WIRE; IN1–IN3–IN2–IN4; tối đa 1.200 half-step/s, gia tốc 700 half-step/s² |
| HOME | Xác minh đỏ tại chỗ trước; nếu chưa đúng thì tìm chiều +1 ở 600 half-step/s |
| Dò đích SORT | Chiều +1 (`SORT_DIRECTION`), tốc độ 600 half-step/s (`TARGET_SEARCH_SPEED`), dừng theo màu |
| GY-33 | I2C 0x5A, bắt đầu thanh ghi 0x00, đọc 8 byte |
| Thứ tự byte | R, G, B, Clear; mỗi giá trị 16 bit byte cao trước |
| Chu kỳ màu | Đọc bắt đích khi chạy 50 ms; khi đứng yên và phiếu ổn định 200 ms; log 2.000 ms |
| Chuẩn hóa | R/(R+G+B), G/(R+G+B), B/(R+G+B) |
| Nhận diện | Khoảng cách Euclid tối đa 0,07; chênh với màu gần nhì ít nhất 0,03 |
| Clear tối thiểu | 100; tổng RGB bằng 0 trả UNKNOWN |
| Lọc màu | Đủ 5 mẫu, ít nhất 4/5 cùng màu; reset lịch sử khi lỗi I2C hoặc dữ liệu quá cũ |
| Serial | **115200 baud, JSON Lines** ở cả firmware, monitor và Python |

Giữ JSON/115200 để tương thích client Pi; không đưa lệnh thử độc lập `s1`, `s2`, số bước và log văn bản 9600 của sketch vào kênh này. Hai servo vẫn chuyển động đồng bộ; boot không tự phát góc đóng. HOME_SPEED, thời gian cửa và bước/vòng là cấu hình của dự án vì sketch không cung cấp phép hiệu chuẩn tương ứng.

| Vị trí | Màu | R chuẩn | G chuẩn | B chuẩn |
|---|---|---:|---:|---:|
| 1 / HOME | RED | 0,446627 | 0,265944 | 0,287429 |
| 2 | BLUE | 0,175560 | 0,320092 | 0,504347 |
| 3 | GREEN | 0,189267 | 0,463051 | 0,347682 |
| 4 | BLACK | 0,222644 | 0,390574 | 0,386782 |

Position 0 là UNKNOWN, khác BLACK. Bảng lấy từ dữ liệu thực nghiệm người dùng gửi; cần kiểm tra lại sau khi lắp vào ống. Ánh xạ màu–ngăn phải đúng bảng; các dấu không cần cách đều 90° hoặc xuất hiện theo thứ tự số. Motor tìm màu đích theo một chiều trong giới hạn, không còn dựa vào 4.096 bước/vòng. Driver này dùng **giao tiếp module GY-33 đúng sketch**, không dùng giao tiếp TCS34725 trực tiếp ở 0x29 và không ghi ID/ATIME/gain/AVALID của driver cũ.

Bảng trên cập nhật theo phiên hiệu chuẩn **15/11/2026**, 12 mẫu mỗi màu, lưu tại `firmware/calibration/gy33-2026-11-15.json`. Cả 48 mẫu đều qua kiểm tra nhận diện bằng driver firmware thực trên host; ngưỡng 0,07/0,03 và Clear tối thiểu 100 giữ nguyên. Đây là kiểm tra lại bộ mẫu thu, vẫn cần xác minh với mẫu mới/nền/biên dấu sau khi nạp lại Uno. Build hiện tại đã dùng bảng mới; chưa nạp tự động lên thiết bị trong bước áp dụng hiệu chuẩn.

## Phần cứng, chân nối và nguồn

| Thiết bị | Chân Uno | Ghi chú |
|---|---|---|
| SG90 số 1 | D6 | Tín hiệu |
| SG90 số 2 | D7 | Cùng hành trình logic servo 1 |
| ULN2003 IN1, IN2, IN3, IN4 | D8, D9, D10, D11 | Kết nối 28BYJ-48 vào driver |
| GY-33 SDA, SCL | A4, A5 | Địa chỉ 0x5A |
| HC-SR04 TRIG, ECHO | D2, D3 | ECHO dùng interrupt |
| HX711 DOUT/DT, SCK/CLK | D4, D5 | Kênh A, gain 128; D2/D3 đã dành cho siêu âm |
| PC hoặc Raspberry Pi 4 | USB | Serial 115200 baud |

Hai servo và stepper dùng **nguồn 5 V riêng đủ dòng cho tải thực tế**, kể cả khởi động/kẹt. Nối chung GND nguồn tải, servo, driver, cảm biến và Uno. Không nuôi cả servo và stepper từ chân 5 V Uno. USB có thể cấp logic Uno, nguồn ngoài cấp riêng tải; không nối hai đầu ra 5 V của hai nguồn độc lập tùy tiện với nhau. Dùng dây đủ tiết diện, tụ phù hợp gần tải và cơ cấu/ngắt nguồn khẩn cấp trong tầm tay. Kiểm tra mức điện áp SDA/SCL và nguồn của breakout GY-33 cụ thể trước khi nối vào Uno. Pi chỉ nối USB, không đưa ECHO 5 V vào GPIO Pi.

## Giới hạn vận hành

- Không có cảm biến phản hồi cửa. `isOpen()`, `isClosed()` và `isFinished()` chỉ xác nhận đã phát xong lịch góc và đợi ổn định, không xác nhận vị trí cơ khí.
- Sau boot/STOP/lỗi, cửa UNKNOWN và không phát PWM. CLOSE_GATE tường minh phát góc đóng rồi đợi đủ hành trình + ổn định. Lần đóng từ góc chưa biết không thể nội suy hành trình thực tế; phải kiểm tra vùng cửa trước khi ra lệnh.
- Không xoay khi cửa chưa đóng theo lịch lệnh; không mở nếu chưa HOME/xác minh màu. OPEN_GATE thủ công cũng phải xác minh lại khi đứng yên.
- STOP ngừng phát bước, nhả cuộn stepper, detach servo và bỏ HOME; không tự đóng cửa. Nó không phải ngắt nguồn khẩn cấp; cơ cấu có thể trôi/quán tính khi nhả lực.
- Khi bắt đích, motor giữ cuộn dây trong lúc xác minh, mở/đóng cửa và IDLE để tránh trôi ống. STOP/lỗi mới nhả lực. Kiểm tra dòng nguồn và nhiệt motor/ULN2003 khi giữ lâu. Phần mềm giữ pha điện khi tiếp tục sau mẫu giả, tránh nhảy pha do đặt lại bộ đếm về 0.
- Client gửi heartbeat GET_STATUS mỗi giây. Quá 6 s không có lệnh hợp lệ trong khi hoạt động/đã HOME sẽ chốt LINK_LOST. USB không có chân phát hiện rút cáp riêng.
- Watchdog AVR 2 s có sẵn, mặc định tắt. Chỉ bật `ENABLE_WATCHDOG` sau khi kiểm tra bootloader và cơ cấu chịu được reset; sau reset không tự chạy lại SORT.
- HC-SR04 chỉ đại diện ngăn `MONITORED_BIN=1`. Ngăn này mặc định bị chặn SORT khi FULL hoặc UNKNOWN. Nếu chưa lắp HC-SR04, SORT 1 sẽ trả BIN_UNKNOWN; có thể đặt `REJECT_UNKNOWN_BIN=false` khi chủ động thử bàn, nhưng khi đó không còn chặn trường hợp ngăn này mất dữ liệu. Không suy trạng thái bốn ngăn từ một cảm biến.

## Build, upload và Serial Monitor

Cài VS Code và extension **PlatformIO IDE**, mở thư mục `smart-trash-bin/firmware`, đợi tải toolchain và thư viện. Trong PlatformIO terminal:

```sh
pio run
pio device list
pio run -t upload --upload-port COM3
pio device monitor --port COM3 --baud 115200
```

Linux/Pi thay COM3 bằng `/dev/ttyACM0`. Serial Monitor gửi LF và cần gửi GET_STATUS ít nhất mỗi 1–2 s khi đã HOME/đang chạy; dùng Python sẽ tự heartbeat. Đóng Serial Monitor trước khi mở Python hoặc upload.

Đã khóa Atmel AVR 5.1.0, Servo 1.2.2, AccelStepper 1.64.0 và ArduinoJson 6.21.5; Wire đi kèm framework. Không cần thêm thư viện GY-33 vì đã triển khai giao tiếp module bằng Wire.

Máy hiện tại có PlatformIO nhưng chưa có `pio` trong PATH. Từ workspace `hardware` có thể chạy:

```powershell
$env:PLATFORMIO_CORE_DIR = Join-Path (Get-Location) '.pio-core'
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -d smart-trash-bin/firmware
```

Thêm `-t upload --upload-port COM3` để upload sau khi kết nối Uno và kiểm tra cơ cấu. `.pio-core/` và `firmware/.pio/` là cache/build, không phải mã nguồn.

## Python client Windows đóng vai Raspberry Pi

Đã tạo `.venv` trong dự án bằng Python 3.11 và cài **pyserial 3.5**. Không cần Python nằm trong PATH hoặc kích hoạt venv. Từ thư mục `smart-trash-bin`:

```powershell
.\run_client.cmd --list-ports
.\run_client.cmd --port COM3 --probe
.\run_client.cmd --port COM3 --log-file test-reports/serial.log
```

`--list-ports` chỉ liệt kê, không mở cổng. `--probe` mở USB, chờ reset Uno 2 s và chỉ đọc status/color, không gửi lệnh chuyển động. Mở USB có thể reset Uno. Console có heartbeat, reader riêng và các lệnh:

```text
status
color
close
home
sort 3
open
close
stop
reset
heartbeat off
heartbeat on
quit
```

Mỗi lệnh chuyển động phải đợi COMPLETE/ERROR; Ctrl+C khi đang chờ sẽ gửi STOP. Client không tự retry lệnh chuyển động, không cho nhiều SORT đồng thời. Khi timeout, kết quả có thể chưa biết: STOP, kiểm tra cơ cấu rồi RESET_ERROR → CLOSE_GATE → HOME. Chỉ kết quả HOME thành công trong kết nối hiện tại mới cho phép SORT.

Có launcher PowerShell với chế độ `console`, `probe`, `guided`, `ports`, `self-test`. Trên máy đang chặn script PowerShell, dùng `.cmd` bên trên hoặc chỉ cho phép script trong tiến trình này:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_client.ps1 -Mode ports
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_client.ps1 -Mode guided -Port COM3
```

Để cài lại venv/thư viện trên Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_client.ps1
```

Không thay execution policy toàn máy. Script setup dùng Python trong PATH hoặc Python của PlatformIO nếu có. Client cần Python 3.10 trở lên. Chỉ mở một ứng dụng giữ cổng serial.

## Khi COM5 đã kết nối nhưng thử màu thất bại

Nếu mất serial lúc OPENING/servo chạy, hai cổng USB khác nhau trên cùng PC chưa đủ để kết luận nguồn tải độc lập hoặc đủ dòng khởi động. Cấp riêng khỏi chân 5 V Uno là đúng, nhưng vẫn cần phân biệt nguồn USB/driver/cáp và tải servo. Thử thay riêng nguồn servo bằng nguồn 5 V ổn định độc lập với PC, giữ USB Uno để giao tiếp, nối chung GND; không nối +5 V nguồn servo vào +5 V Uno. Dây dòng tải servo về trực tiếp cực âm nguồn tải, nhánh GND Arduino chỉ làm tham chiếu chung. Xem [hướng dẫn nguồn servo của Arduino](https://docs.arduino.cc/learn/electronics/servo-motors/). Đây là phép thử phân lập, không khẳng định nguyên nhân chỉ từ Write timeout.

Client hiện có `reconnect` ngay trong console khi cổng đã lỗi. Nó đóng handle cũ, mở lại USB (có thể reset Uno) và chỉ truy vấn trạng thái, không replay SORT/HOME và không khôi phục cờ ready của client. Sau khi kiểm tra cơ cấu, dùng `reconnect`, xem trạng thái; chỉ RESET_ERROR nếu đang ERROR, rồi CLOSE_GATE và HOME lại tường minh. Không gửi lại SORT cũ khi chưa biết kết quả. STOP không thể truyền qua một liên kết đã mất; cơ cấu còn chuyển động cần ngắt vật lý phù hợp. Write timeout nay đánh dấu mất kết nối ngay và giải phóng các lệnh đang chờ bằng lỗi; chưa có bằng chứng đổi client sẽ chữa được lỗi điện/USB.

Từ workspace `hardware` cần `cd smart-trash-bin` trước khi dùng `.\run_client.cmd`, hoặc gọi `.\smart-trash-bin\run_client.cmd`. Tên tùy chọn có khoảng trắng: `--port COM5`, không phải `--portCOM5`. Nếu cổng báo Access is denied, đóng Serial Monitor/console Python khác đang giữ cổng; không chạy hai client cùng lúc.

`healthy=true` chỉ xác nhận đọc được GY-33, không đảm bảo màu khớp bảng. Trong log trước hiệu chuẩn, R=315/G=262/B=272 cho tỉ lệ khoảng (0,371; 0,309; 0,320), cách RED của bảng cũ khoảng 0,166 > ngưỡng 0,07, nên khi đó UNKNOWN là kết quả đúng theo cấu hình. Kiểm tra dấu thật, hướng mắt đọc, ánh sáng và khoảng cách trước khi hiệu chuẩn; không lấy một mẫu để nới ngưỡng hoặc tự gán màu.

Công cụ lấy mẫu bốn màu, chỉ gửi GET_STATUS/GET_COLOR, không di chuyển hoặc sửa firmware:

```powershell
.\run_client.cmd --port COM5 --calibrate-color --samples 12 --calibration-report test-reports/color-calibration.json --log-file test-reports/calibration.log
```

Đặt từng dấu RED, BLUE, GREEN, BLACK khi cơ cấu đứng yên và xác nhận tại terminal. Công cụ lưu RGB thô/tỉ lệ, sinh bảng COLOR_REFERENCE đề xuất và kiểm tra lại khoảng cách/margin trên mẫu thu. Nếu các màu chồng lấn hoặc Clear dưới 100, công cụ báo không hợp lệ. Bảng này chưa tự áp dụng: cần kiểm tra mẫu mới/nền, cập nhật config và build/upload sau khi chấp nhận dữ liệu thực nghiệm.

Một lần đọc thực tế sau reconnect ghi nhận nhiều đoạn cuối JSON lặp rồi dữ liệu hợp lệ trở lại; chưa xác định chắc nguồn nằm ở adapter/driver hay đường truyền. Client hiện xả RX trong thời gian chờ boot, chỉ retry truy vấn trạng thái và giới hạn cảnh báo JSON lỗi mỗi giây; log DEBUG giữ mẫu byte thô để chẩn đoán. Nếu lỗi tiếp diễn, chạy `--probe --log-file test-reports/probe.log`, kiểm tra cổng/baud/firmware và adapter. Timeout truy vấn đọc không còn báo nhầm rằng đã gửi lệnh chuyển động.

## Kiểm thử thủ công toàn bộ luồng

```powershell
.\run_client.cmd --port COM3 --guided --report test-reports/manual-test.json --log-file test-reports/serial.log
```

Chế độ guided chỉ bắt đầu chuyển động sau xác nhận ở terminal, hỏi quan sát cơ khí riêng với kết quả phần mềm. Chuẩn bị nguồn tải, cảm biến và vùng cơ cấu thông thoáng; lần đầu thử không có rác.

1. Kiểm tra INIT, chưa HOME; xác nhận không tự chuyển động khi kết nối.
2. Khi cơ cấu đứng yên và cuộn motor được nhả, đưa lần lượt RED, BLUE, GREEN, BLACK vào vùng đọc. Chờ 1,2 s mỗi dấu và kiểm tra dữ liệu/position.
3. Cho phép CLOSE_GATE, quan sát hai servo đóng đồng bộ đúng chiều.
4. Cho phép HOME, quan sát motor dừng tại đỏ; kiểm tra IDLE, homed=true, position=1.
5. Lần lượt SORT theo `1→2→3→4→1` và `1→3→2→4→1`. Trước mỗi SORT đều có xác nhận, sau mỗi lần kiểm tra marker/ngăn, motor dừng trước mở, hai servo mở–giữ–đóng rồi IDLE.
6. Lưu báo cáo kết quả từng bước, thời gian, phản hồi, xác nhận cơ khí và TX/RX. Nếu hủy/lỗi, gửi STOP rồi kết thúc; không tự retry/đóng cửa.

Firmware gửi sự kiện STATE_CHANGE khi đổi trạng thái (`TRACE_STATES=true`), client hiển thị và ghi log. Báo cáo kiểm tra có quan sát đủ chuỗi ROTATING→VERIFY_POSITION→OPENING→HOLDING→CLOSING→COMPLETE cho mỗi SORT hay không. Nếu đã đứng ở màu đích, SORT bắt đầu bằng VERIFY_POSITION, không quay thêm một vòng. Sự kiện chẩn đoán có thể bị bỏ khi UART bận; `trace_complete=false` không tự biến thành lỗi cơ khí. Các trường phần mềm, quan sát cơ khí và độ đầy đủ trace được lưu riêng.

Các bài lỗi thực hiện riêng trong console, không tự làm hàng loạt:

| Bài thử | Mong đợi |
|---|---|
| HOME trước CLOSE_GATE | GATE_UNSAFE, không quay |
| SORT trước HOME | NOT_READY |
| SORT khi cửa mở | GATE_UNSAFE |
| Sai màu/không thấy HOME | Tìm trong giới hạn rồi ERROR, không mở cửa |
| STOP lúc HOME/quay/mở/giữ/đóng | Dừng điều khiển, bỏ HOME, không tự tiếp tục |
| `heartbeat off` sau HOME, không gửi thêm lệnh | Sau khoảng 6 s ERROR/LINK_LOST; RX vẫn chạy; sau đó `heartbeat on` để phục hồi |
| Reset giữa chu trình | INIT, không tự chạy lại SORT |
| Ngăn giám sát đầy | FULL và từ chối SORT đúng ngăn đó |
| Echo không hợp lệ | UNKNOWN và distance_cm=null, không coi là FULL |
| Trùng ID / lệnh khi BUSY | Không chạy lặp / BUSY; STOP luôn được xử lý |

Các lệnh `status` cũng làm mới heartbeat, vì vậy khi thử LINK_LOST chỉ quan sát telemetry tự phát. Lỗi I2C không dùng dữ liệu cũ; các bài thay đổi phần cứng thực hiện trong điều kiện cơ cấu kiểm soát được và có ngắt nguồn vật lý.

## Chẩn đoán stepper chạy riêng được nhưng tích hợp bị giật

`TEST_STEPPER` là bài thử hữu hạn +1.000 half-step, max 1.000 half-step/s và gia tốc 700, dùng cùng driver như HOME/SORT. Tất cả tác vụ GY-33, siêu âm, UART và servo vẫn hoạt động, nhưng màu không quyết định điểm dừng và lỗi màu không hủy riêng bài baseline này. Cửa phải được đóng theo lịch lệnh trước khi thử, không BUSY/ERROR. Bài thử bỏ HOME, không mở cửa, có timeout 6 s và vẫn chịu STOP/heartbeat/interlock cửa.

Sau khi nạp firmware mới, mở console, chạy lần lượt và chờ từng lệnh:

```text
close
test_stepper
diag
```

Console hỏi xác nhận trước khi test_stepper quay. Nếu đang ERROR, dùng reset rồi close trước. Sau bài thử, muốn phân loại cần HOME lại. Không tự động nạp/chạy chuyển động khi cập nhật mã nguồn.

`diag` gửi GET_MOTION_DIAG, phản hồi có:

| Trường | Diễn giải |
|---|---|
| emitted_steps | Số bước phần mềm thực sự tăng trong AccelStepper ở lượt di chuyển gần nhất; baseline hoàn tất phải bằng 1.000, không phải phản hồi encoder cơ khí |
| run_calls | Số lần gọi run() khi đang chạy |
| max_run_gap_us | Khoảng cách lớn nhất giữa hai lần phục vụ run(); so với nominal_interval_us để tìm tình trạng vòng lặp không phục vụ kịp |
| nominal_interval_us | Chu kỳ bước ở tốc độ trần của lượt đó; baseline 1.000 µs, HOME khoảng 6.666 µs |
| moving | Phần mềm còn lịch di chuyển hay không |
| min_free_stack | Số byte vùng RAM đánh dấu chưa bị stack dùng kể từ boot; phép đo xấp xỉ trên AVR, không phải bảo đảm an toàn stack tuyệt đối |

Nếu emitted_steps đủ 1.000 nhưng trục không quay tương ứng thì bộ đếm không chứng minh cơ khí đã theo kịp. Nếu khoảng phục vụ lớn so với chu kỳ bước, cần xử lý lịch chạy; nếu JSON vẫn hỏng hoặc stack còn rất ít, cần tiếp tục kiểm tra RAM/nguồn/đường truyền. Chưa kết luận chỉ từ nguồn ngoài hoặc một max-gap đơn lẻ.

Phần phát JSON đã đổi sang ghi trực tiếp từng trường vào TX ring bằng chuỗi Flash, không tạo mảng frame tạm 128–240 byte trên stack và không dùng snprintf cho bản tin. Phản hồi vẫn là một JSON hoàn chỉnh mỗi dòng; có kiểm thử giá trị số lớn nhất và nhiều vòng quấn bộ đệm. Stack marker khởi tạo một lần sau setup; ứng dụng không cấp phát heap.

HOME/SORT hiện tìm ở 600 bước/s, giới hạn 15.000 bước tương đương khoảng 25 s chạy ở tốc độ trần, còn deadline toàn bộ là 40 s (gồm xác minh và tăng tốc). Bản cũ ở 150 bước/s chỉ phát khoảng 6.000 bước trong 40 s nên không dùng hết được quãng tìm 15.000 đã cấu hình. Hai giới hạn vẫn độc lập: giới hạn nào tới trước sẽ dừng. Nếu tăng timeout cần tăng command_timeout của Python tương ứng.

## Hiệu chuẩn và kiểm tra chuyển động

GY-33 dùng bảng thực nghiệm đã cung cấp. Với từng dấu, đọc GET_COLOR nhiều lần, cách nhau ít nhất 200 ms, tính từng kênh chia tổng RGB và so với bảng. Chỉnh `COLOR_REFERENCE`, `COLOR_MIN_CLEAR`, `COLOR_MAX_DISTANCE`, `COLOR_MARGIN` theo môi trường lắp thật. Thu cả mẫu nền, biên dấu và vùng tối. Không dùng công thức RGB/Clear cũ.

Bộ lọc chỉ xác nhận khi đủ 5 mẫu và có 4 mẫu cùng màu; một mẫu lẻ UNKNOWN vẫn có thể giữ màu theo đa số, hai mẫu có thể làm mất xác nhận. Lỗi I2C reset toàn bộ lịch sử. Nếu dấu BLACK có Clear thấp hơn 100 thì trả UNKNOWN đúng ngưỡng; cần điều chỉnh ánh sáng/ngưỡng sau đo thực tế, không tự gộp BLACK với UNKNOWN.

Khi chạy, đọc I2C mỗi 50 ms để bắt mẫu đúng màu đích và dừng motor; ở 600 bước/s là khoảng 30 half-step giữa hai lần đọc. Poll bus nhanh hơn không đảm bảo module tạo mẫu quang học mới mỗi 50 ms; vì vậy phiếu ổn định vẫn cách nhau ít nhất 200 ms và phải lấy lịch sử mới khi đã đứng yên. Chưa xác minh module cung cấp dữ liệu mới nhanh tới đâu. Sau dừng, VERIFY_MS=1.500 ms cho phép thu lại 5 mẫu. Nếu dấu quá hẹp hoặc module có độ trễ gây vượt dấu thì xác minh sẽ thất bại thay vì mở cửa; cần giảm tốc/tăng bề rộng dấu theo thử thực tế.

HOME mới trước hết xác minh tại chỗ tối đa 1.500 ms, không tự quay khỏi một dấu đỏ đang nhìn thấy. Đặt sẵn đỏ, CLOSE_GATE rồi HOME: khoảng một giây sau nên có COMPLETE, position=1, homed=true mà không cần quay. Nếu hiện đang ở đen/màu khác thì sau lần xác minh ban đầu mới chuyển HOMING và quay tìm. Toàn bộ vẫn chịu deadline và giới hạn bước chung.

Kiểm tra ULN2003 đúng IN1–IN4; nếu chỉ rung, kiểm tra dây/nguồn và giảm tốc. Đổi HOME_DIRECTION/SORT_DIRECTION nếu cần. Bộ đếm bước chỉ giới hạn quãng tìm, không quyết định vị trí ngăn. Lần bắt đích cần dừng trong vùng màu đủ rộng để xác minh khi đứng yên. Việc giữ cuộn dây giảm trôi nhưng không phải phản hồi cơ khí hay bằng chứng motor không mất bước.

Sau HOME, OPEN_GATE/CLOSE_GATE cho hai servo cùng góc 0→180→0. Kiểm tra chiều lắp, hành trình cơ khí và tránh ép servo tại giới hạn. PWM hai kênh được thư viện phát nối tiếp; lịch góc chung không chứng minh hai trục cơ khí đạt đích đồng thời. Có thể đổi SERVO_2_REVERSED nếu cơ cấu đối xứng thực tế yêu cầu.

Nhận diện BLACK được siết riêng ngày 24/11/2026: mẫu thật R=130, G=235, B=234, Clear=630; tham chiếu RGB chuẩn hóa `(0.217028, 0.392321, 0.390651)`, khoảng cách tối đa `0.018` và Clear trong `[450,850]`. Đây là ngưỡng thử nghiệm theo dữ liệu hiện có, cần kiểm tra mép dấu và ánh sáng/khoảng cách lắp thực tế. Hai bộ RGB từng bị nhận nhầm `270/445/420` và `244/402/380` bị loại bởi điều kiện RGB, kể cả khi Clear nằm trong khoảng cho phép. Clear của dòng log thứ hai bị mất ký tự nên không dùng để hiệu chuẩn. BLACK không đạt trả UNKNOWN, không gán sang màu khác; điều kiện áp dụng cả khi tìm dấu và xác minh đứng yên. Các mẫu hiệu chuẩn cũ vẫn được kiểm thử cùng mẫu mới.

## Load cell qua HX711: kết nối và hiệu chuẩn tự lưu

HX711 dùng **DOUT/DT → D4**, **SCK/CLK → D5**, VCC và GND theo breakout phù hợp mức logic Uno (thường module dùng 5 V), nối chung GND. Load cell nối E+/E− và A+/A− theo nhãn/cấu hình cầu của nhà sản xuất; không suy dây chỉ theo màu. Không dùng D2/D3 của sketch cân mẫu vì đã nối HC-SR04. LCD I2C trong sketch mẫu không cần cho công cụ cân qua USB này.

Driver đọc khi DOUT báo sẵn sàng, không wait_ready_timeout, không delay chờ chuyển đổi, không dùng String. Mỗi mẫu chỉ có 24 xung dữ liệu và xung thứ 25 chọn A/128 cho lần tiếp theo. Chỉ khóa ngắt trong từng khoảng SCK HIGH ngắn; ngắt Servo/UART được phục vụ giữa các bit khi SCK LOW. HX711 có mức SCK HIGH kéo dài dẫn tới power-down, nên không để ISR kéo dài mức HIGH ngoài ý muốn. Tham khảo [datasheet HX711 của AVIA Semiconductor](https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf). RATE của module quyết định 10/80 SPS; driver hỗ trợ cả hai, ưu tiên nguồn sạch và RATE=10 SPS khi hiệu chuẩn.

Đơn vị giao tiếp là **kg**, factor là **ADC counts/kg**. Offset là số ADC thô lúc cân trống. Công thức `(raw - offset) / factor`; factor âm là hợp lệ nếu cầu cân lắp chiều ngược. Dữ liệu hiển thị lọc nhẹ; raw đưa ra nguyên bản để hiệu chuẩn. Ngưỡng 3 g đưa kết quả gần zero về 0. Cân thiếu mẫu/quá cũ/bão hòa trả `healthy:false`, `weight_kg:null`; chưa hiệu chuẩn trả `calibrated:false`. Chưa áp dụng policy phân loại theo khối lượng hoặc giới hạn tải vì chưa có thông số sức chứa load cell.

Không tự tare lúc boot: nếu còn vật trên mặt cân, khối lượng không bị âm thầm coi là 0. Cần trừ bì tường minh khi mặt cân trống. Mất HX711 chỉ làm số cân UNKNOWN, không tự dừng quy trình SORT. Tare/đổi hệ số chỉ nhận khi không có hoạt động khác, không ERROR và các actuator đã dừng; có trạng thái CALIBRATING, không tự mở/đóng cửa hay chạy HOME.

**Lần đầu phải nạp firmware có HX711 trước.** Từ thư mục `smart-trash-bin`, đóng console đang giữ COM5 và chạy:

```powershell
$env:PLATFORMIO_CORE_DIR = (Resolve-Path ..\.pio-core).Path
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -d firmware -t upload --upload-port COM5
.\.venv\Scripts\python.exe raspberry\hardware\test_loadcell.py --port COM5 --known-grams 200
```

Upload chạy `firmware/scripts/prepare_upload.py` để đọc bỏ dữ liệu Serial tồn, tạo xung reset DTR rồi chuyển cho avrdude. Script không gửi lệnh cơ cấu. Nếu `GET_WEIGHT` báo `INVALID_COMMAND`, cần nạp firmware hỗ trợ cân trước; công cụ kiểm tra lệnh này trước khi yêu cầu đặt vật cân.

Thay `200` bằng khối lượng quả cân thật, tính bằng gram và trong định mức load cell. Có thể bỏ `--known-grams` để nhập khi chạy. Script sẽ:

1. Kết nối USB, chỉ dùng truy vấn cân/cấu hình cân; không gửi lệnh motor/servo.
2. Hỏi mặt cân trống rồi lấy 20 mẫu raw có sequence mới.
3. Hỏi đặt quả cân biết trước rồi lấy 20 mẫu; tính offset và hệ số binary32 như AVR.
4. Từ chối tín hiệu span quá nhỏ, ADC bão hòa hoặc độ nhiễu quá 0,5% span. Lấy thêm ít nhất 5 mẫu mới độc lập; kiểm tra sai số từng mẫu không vượt `max(3 g, 2% quả cân)`.
5. Gửi SET_SCALE, chờ EEPROM lưu xong và đọc lại thông số để đối chiếu. Không tự retry lệnh ghi nếu mất liên lạc.
6. **Tự ghi** `firmware/include/loadcell_calibration.h`, `firmware/calibration/loadcell-calibration.json` và bản lịch sử `firmware/calibration/loadcell-<timestamp>.json`. Không sửa các tham số motor/màu trong config.h.

Thông số có hiệu lực ngay sau SET_SCALE; không cần nạp lần nữa để dùng hệ số vừa hiệu chuẩn. File header sinh ra là cấu hình mặc định cho các lần build tiếp theo. EEPROM hợp lệ được ưu tiên khi boot, nếu mất/hỏng cả hai bản ghi thì dùng header. EEPROM có hai slot, version/generation và CRC, bắt đầu địa chỉ 32; không đè vùng 0…7 mà sketch cân cũ từng dùng. Không tự nhập hệ số CAN2 cũ vì không có offset trừ bì đã lưu; hãy hiệu chuẩn lại bằng script. EEPROM chỉ ghi khi có lệnh cấu hình/tare, từng byte lúc sẵn sàng, không ghi theo mỗi lần đo.

Nếu lưu EEPROM thành công nhưng ghi file trên PC lỗi, script báo rõ trạng thái và in factor/offset; không được hiểu là đã lưu cả hai. Hai file cấu hình hiện hành được thay bằng file tạm, có khôi phục khi cập nhật file thất bại. Nếu dữ liệu đo không đạt kiểm tra, script không đổi EEPROM/header. File header mặc định ban đầu là CALIBRATED=false, không có hệ số thực nào được giả định.

Đọc cân liên tục và tare sau này:

```powershell
.\.venv\Scripts\python.exe raspberry\hardware\test_loadcell.py --port COM5 --read
.\.venv\Scripts\python.exe raspberry\hardware\test_loadcell.py --port COM5 --tare
```

`--tare` yêu cầu mặt cân trống, lưu offset mới vào EEPROM và cập nhật file dự án; giữ nguyên factor. Trong console chung `.\run_client.cmd --port COM5`, có lệnh `weight` và `tare`; lệnh tare của console lưu trên Uno, còn muốn đồng bộ cả file dự án thì dùng script `--tare` ở trên. Cổng chỉ được mở bởi một chương trình tại một thời điểm. Python client mặc định chờ tối đa 75 s để bao phủ HOME_TIMEOUT_MS hiện là 60 s; đọc cân vẫn timeout riêng 3 s.

Ví dụ JSON:

```json
{"id":201,"cmd":"GET_WEIGHT"}
{"id":202,"cmd":"TARE_WEIGHT"}
{"id":203,"cmd":"SET_SCALE","factor":500000.0,"offset":100000}
```

SET_SCALE ở trên chỉ minh họa, không phải hệ số cho load cell của bạn. GET_WEIGHT trả trực tiếp `type:WEIGHT`, gồm raw, sample_seq, weight_kg, healthy, calibrated, factor, offset, busy. TARE_WEIGHT/SET_SCALE trả ACCEPTED rồi COMPLETE khi mẫu/EEPROM đã xong hoặc ERROR. SCALE_TIMEOUT là thiếu mẫu tare; INVALID_SCALE là hệ số/offset không hợp lệ; EEPROM_ERROR là lỗi đọc lại/timeout lưu. Không cần thêm thư viện HX711/LiquidCrystal vì driver HX711 đã triển khai trực tiếp; EEPROM đi kèm Arduino framework.

Chưa hiệu chuẩn trên bộ cân thật trong bước tạo mã này. Sau hiệu chuẩn, bỏ quả cân kiểm tra zero, đặt lại và thử một khối lượng khác trong định mức; kiểm tra cả lúc motor/servo chạy để đánh giá nhiễu cơ khí/nguồn. Bộ lọc không thay thế việc lắp cơ khí load cell đúng.

## Raspberry Pi 4

Nối USB có dữ liệu. Nếu thiếu quyền cổng, cấu hình nhóm `dialout` cho tài khoản Pi rồi đăng nhập lại. Từ thư mục dự án:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r raspberry/hardware/requirements.txt
python raspberry/hardware/test_serial.py --list-ports
python raspberry/hardware/test_serial.py --port /dev/ttyACM0 --probe
python raspberry/hardware/test_serial.py --port /dev/ttyACM0 --guided
```

Không chỉ định cổng thì dò VID Uno/CH340; nhiều cổng phải chọn rõ. Sau reconnect/reset phải xác minh trạng thái và HOME lại. Tiến trình client mới dùng ID từ 1; nếu Uno chưa reset và trả STALE_ID, reset Uno trong điều kiện an toàn rồi kết nối lại, không retry mù lệnh cũ.

## JSON Lines và lỗi

Mỗi dòng tối đa 127 byte trước LF; ID nguyên dương 1…2.147.483.647, tăng dần trong phiên boot. Dòng dở timeout 500 ms. Ví dụ:

```json
{"id":101,"cmd":"GET_STATUS"}
{"id":102,"cmd":"GET_COLOR"}
{"id":103,"cmd":"CLOSE_GATE"}
{"id":104,"cmd":"HOME"}
{"id":105,"cmd":"SORT","target":3}
{"id":106,"cmd":"OPEN_GATE"}
{"id":107,"cmd":"CLOSE_GATE"}
{"id":108,"cmd":"STOP"}
{"id":109,"cmd":"RESET_ERROR"}
```

Chờ kết quả từng lệnh, duy trì heartbeat; không dán cả khối thành chuỗi chuyển động. Lệnh chuyển động trả ACCEPTED rồi COMPLETE hoặc ERROR. GET_STATUS trả TELEMETRY, GET_COLOR trả COLOR với ID yêu cầu; telemetry tự phát mỗi giây có ID 0. COLOR tự phát mỗi 2 s khi DEBUG_COLOR=true; log không phá kênh JSON.

```json
{"id":105,"status":"ACCEPTED","position":0}
{"type":"STATE_CHANGE","id":105,"from":"ROTATING","to":"VERIFY_POSITION"}
{"id":105,"status":"COMPLETE","position":3}
{"id":105,"status":"ERROR","error":"POSITION_TIMEOUT"}
```

COMPLETE và ERROR ở trên là hai kết quả thay thế nhau. FULL trong telemetry là cảnh báo; Python ghi WARNING. Distance không hợp lệ là null. Các bản tin debug/state/telemetry tùy chọn có thể bỏ khi TX bận để dành chỗ cho phản hồi. Tràn TX của phản hồi bắt buộc gây dừng TX_OVERFLOW.

Cache cố định lưu lệnh chuyển động được chấp nhận gần nhất: cùng ID/cmd/target trả trạng thái/kết quả đã lưu, không chạy lại. Cùng ID khác payload trả ID_CONFLICT, ID cũ ngoài cache trả STALE_ID. Truy vấn, RESET_ERROR và lệnh bị từ chối cũng tiêu thụ ID. STOP luôn thực hiện dừng kể cả ID cũ, nên không gửi STOP cũ sau khi đã bắt đầu thao tác khác. Cache mất khi reset; client không tự retry chuyển động.

| Lỗi | Xử lý |
|---|---|
| INVALID_JSON / INVALID_COMMAND / INVALID_ID / INVALID_TARGET | Sửa JSON, tên lệnh, ID hoặc target 1…4 |
| LINE_TOO_LONG / RX_TIMEOUT | Gửi lại dòng mới đầy đủ trong giới hạn, không flood UART |
| BUSY | Chờ kết quả lệnh hiện tại hoặc STOP |
| NOT_READY / GATE_UNSAFE | Kiểm tra ERROR, CLOSE_GATE và HOME đúng thứ tự |
| BIN_FULL / BIN_UNKNOWN | Kiểm tra/làm trống ngăn giám sát, sửa siêu âm hoặc chọn policy thử bàn phù hợp |
| HOME_TIMEOUT / POSITION_TIMEOUT | Kiểm tra dấu/độ rộng, ánh sáng, tốc độ tìm, chiều, lực giữ, ngân sách quãng tìm |
| COLOR_SENSOR | Kiểm tra GY-33 0x5A, nguồn/bus, RESET_ERROR rồi đọc lại trước HOME |
| LINK_LOST / STOPPED | Kiểm tra cơ cấu, khôi phục heartbeat, RESET_ERROR → CLOSE_GATE → HOME |
| STATE_TIMEOUT | Kiểm tra thời gian cửa/cấu hình và độ trễ vòng lặp |
| STALE_ID / ID_CONFLICT | Kiểm tra quản lý phiên, không retry chuyển động chưa biết kết quả |
| TX_OVERFLOW | Ngừng flood, đọc dữ liệu và phục hồi sau kiểm tra cơ cấu |

RESET_ERROR chỉ nhận khi ERROR và actuator đã dừng; xóa latch, khởi tạo lại driver, về INIT, không khôi phục HOME hay chuyển động. I2C lỗi tiếp thì HOME bị từ chối. Siêu âm lỗi trả UNKNOWN; sau ba lần lỗi healthy() false, cần ba mẫu mới để khôi phục median.

## Kết quả kiểm thử

Build AVR ngày **24/11/2026**, `pio run` thành công:

| Tài nguyên | Sử dụng | Giới hạn |
|---|---:|---:|
| Flash | 30.328 byte (94,0%) | 32.256 byte |
| SRAM tĩnh | 1.509 byte (73,7%) | 2.048 byte |

Còn 539 byte cho stack/trạng thái chạy; dùng diag để quan sát stack marker sau bài thử. Đã bỏ các mảng frame JSON tạm để giảm độ sâu stack; RAM tĩnh tăng do bộ đếm chẩn đoán không đồng nghĩa stack tăng. Không cấp phát heap trong firmware ứng dụng. Cần đo timing/stack trên Uno khi thay cấu hình/thêm module.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s raspberry/hardware -p "test_*.py" -v
.\.venv\Scripts\python.exe firmware/test/run_host_tests.py
```

Kiểm thử gồm 29 unit tests Python, 29 kịch bản state machine C++ và I/O. Các bài tìm đích xác nhận: không dừng theo góc ước lượng, bắt bằng mẫu mới rồi giữ để xác minh, không dùng lại mẫu cũ, giữ pha khi tiếp tục, giới hạn tổng bước/thời gian không bị reset, giới hạn mẫu đích giả, không mở bằng một mẫu, cùng đích không quay thêm, STOP nhả lực. Driver màu cũng nhận đúng cả 48 mẫu hiệu chuẩn thực. I/O kiểm tra writer JSON trực tiếp qua 100 vòng quấn/numeric limits, chẩn đoán và baseline interlock; GY-33/siêu âm như trên. Thêm bài dùng AccelStepper 1.64 thật trên host với thời gian giả lập, tải I2C ngắt quãng 2 ms và lượt đọc HX711 giả lập 350 µs: +1.000 bước, HOME, tiếp tục chiều ngược, chuỗi pha và nhả cuộn đều qua. Đây không mô phỏng điện/cơ khí/ISR Uno. Bài C++ cần g++ và thư viện đã được pio tải về.

**Bản sửa dò màu liên tục chưa upload hoặc kiểm thử chuyển động trên phần cứng thật.** Phiên bản trước đã giao tiếp COM5 và có dữ liệu cảm biến thật từ người dùng. Các kiểm thử offline không mô phỏng lực, nguồn, backlash, timing ngắt AVR hoặc độ rộng dấu khi motor đang chạy. Nạp lại bản sửa rồi thử không tải; kết quả quan sát thật được ghi riêng, không suy ra từ mocks.

Kiểm thử HX711 bổ sung: giải mã ADC có dấu/25 xung, SCK HIGH ngắn, timeout/stale/bão hòa, factor âm, tare 20 mẫu, journal EEPROM/phục hồi sau gián đoạn/CRC hỏng và interlock hiệu chuẩn. Kiểm thử Python xác nhận kiểm tra nhiễu/độc lập, loại mẫu trùng sequence, cập nhật EEPROM và tự sinh file dự án trong thư mục tạm. Build hiện dùng stub chưa hiệu chuẩn; cần chạy test_loadcell.py trên phần cứng để có hệ số thật.
