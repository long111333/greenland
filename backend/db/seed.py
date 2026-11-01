"""Seed dữ liệu thật cho AutoBin — khớp SHARED_CONTRACT.md.

Mật khẩu hash bằng passlib CryptContext(schemes=['bcrypt']) —
cùng cách FastAPI backend sẽ verify.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from passlib.context import CryptContext

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEVICE_ID = "BIN_EDGE_AI_001"
DB_DIR = Path(__file__).resolve().parent
SEED_SQL_PATH = DB_DIR / "seed.sql"


def hash_password(plain: str) -> str:
    return PWD_CONTEXT.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return PWD_CONTEXT.verify(plain, hashed)


def _ai_payload(
    predicted: str,
    confidence: float,
    frames: int = 7,
    extras: dict | None = None,
) -> str:
    alts = {
        "plastic": [("paper", 0.04), ("unknown", 0.02)],
        "metal": [("plastic", 0.03), ("unknown", 0.02)],
        "paper": [("plastic", 0.05), ("unknown", 0.02)],
        "unknown": [("plastic", 0.18), ("paper", 0.14)],
    }
    payload = {
        "model": "MobileNetV3-Small",
        "frames": frames,
        "topk": [[predicted, round(confidence, 4)]]
        + [[name, score] for name, score in alts[predicted]],
    }
    if extras:
        payload.update(extras)
    return json.dumps(payload, ensure_ascii=False)


# timestamp, class, confidence, decision, latency_ms, weight_g, image?
_SORT_SPECS: list[tuple] = [
    ("2026-10-20T07:18:22Z", "plastic", 0.941, "ACCEPTED", 286, 24.5, True),
    ("2026-10-20T08:02:11Z", "paper", 0.903, "ACCEPTED", 241, 14.2, False),
    ("2026-10-20T09:41:05Z", "metal", 0.962, "ACCEPTED", 318, 42.0, True),
    ("2026-10-20T11:15:40Z", "plastic", 0.887, "ACCEPTED", 274, 27.8, False),
    ("2026-10-20T14:22:18Z", "unknown", 0.412, "REJECTED", 355, 19.6, True),
    ("2026-10-21T07:05:33Z", "paper", 0.928, "ACCEPTED", 229, 12.8, False),
    ("2026-10-21T08:44:09Z", "plastic", 0.915, "ACCEPTED", 301, 22.1, False),
    ("2026-10-21T10:12:50Z", "metal", 0.874, "ACCEPTED", 334, 38.4, True),
    ("2026-10-21T13:28:17Z", "paper", 0.791, "ACCEPTED", 268, 16.5, False),
    ("2026-10-21T16:03:44Z", "plastic", 0.536, "REJECTED", 412, 31.2, True),
    ("2026-10-22T07:19:02Z", "metal", 0.949, "ACCEPTED", 297, 45.6, False),
    ("2026-10-22T09:07:28Z", "paper", 0.911, "ACCEPTED", 236, 13.4, False),
    ("2026-10-22T10:55:11Z", "plastic", 0.933, "ACCEPTED", 279, 25.0, True),
    ("2026-10-22T12:41:39Z", "unknown", 0.388, "REJECTED", 448, 22.7, False),
    ("2026-10-22T15:18:55Z", "paper", 0.864, "ACCEPTED", 252, 18.1, False),
    ("2026-10-23T07:33:08Z", "plastic", 0.972, "ACCEPTED", 221, 23.6, True),
    ("2026-10-23T08:48:26Z", "metal", 0.901, "ACCEPTED", 345, 39.8, False),
    ("2026-10-23T11:02:14Z", "paper", 0.548, "REJECTED", 391, 21.3, True),
    ("2026-10-23T13:26:47Z", "plastic", 0.896, "ACCEPTED", 288, 28.9, False),
    ("2026-10-23T17:11:03Z", "metal", 0.818, "ACCEPTED", 367, 51.2, False),
    ("2026-10-24T07:08:19Z", "paper", 0.937, "ACCEPTED", 218, 11.7, False),
    ("2026-10-24T09:29:41Z", "plastic", 0.920, "ACCEPTED", 263, 26.4, True),
    ("2026-10-24T11:46:12Z", "unknown", 0.461, "REJECTED", 429, 17.8, False),
    ("2026-10-24T14:03:58Z", "metal", 0.955, "ACCEPTED", 309, 36.5, True),
    ("2026-10-24T16:40:22Z", "paper", 0.882, "ACCEPTED", 247, 15.9, False),
    ("2026-10-25T07:21:36Z", "plastic", 0.908, "ACCEPTED", 271, 24.8, False),
    ("2026-10-25T08:55:04Z", "paper", 0.914, "ACCEPTED", 233, 14.6, False),
    ("2026-10-25T10:17:49Z", "metal", 0.512, "REJECTED", 488, 33.1, True),
    ("2026-10-25T13:09:27Z", "plastic", 0.861, "ACCEPTED", 312, 29.4, False),
    ("2026-10-26T07:14:15Z", "paper", 0.946, "ACCEPTED", 209, 13.1, True),
    ("2026-10-26T09:38:52Z", "plastic", 0.929, "ACCEPTED", 258, 21.9, False),
    ("2026-10-26T11:22:08Z", "metal", 0.893, "ACCEPTED", 326, 43.7, False),
    ("2026-10-26T14:47:33Z", "unknown", 0.337, "REJECTED", 512, 28.4, True),
    ("2026-10-27T07:06:41Z", "plastic", 0.958, "ACCEPTED", 244, 25.6, False),
    ("2026-10-27T08:31:19Z", "paper", 0.899, "ACCEPTED", 261, 16.8, False),
    ("2026-10-27T10:59:07Z", "metal", 0.927, "ACCEPTED", 301, 40.2, True),
    ("2026-10-27T15:24:46Z", "plastic", 0.847, "ACCEPTED", 339, 32.0, False),
    ("2026-10-28T07:42:13Z", "paper", 0.921, "ACCEPTED", 227, 12.3, False),
    ("2026-10-28T09:16:38Z", "plastic", 0.911, "ACCEPTED", 276, 23.2, True),
    ("2026-10-28T12:05:21Z", "unknown", 0.494, "REJECTED", 401, 20.5, False),
    ("2026-10-29T07:11:54Z", "metal", 0.968, "ACCEPTED", 292, 47.8, False),
    ("2026-10-29T08:49:06Z", "paper", 0.875, "ACCEPTED", 254, 17.4, False),
    ("2026-10-29T11:33:29Z", "plastic", 0.936, "ACCEPTED", 249, 26.1, True),
    ("2026-10-30T07:27:44Z", "paper", 0.952, "ACCEPTED", 215, 14.9, False),
    ("2026-10-30T09:08:17Z", "plastic", 0.889, "ACCEPTED", 294, 30.5, False),
    ("2026-10-30T13:51:02Z", "metal", 0.844, "ACCEPTED", 358, 54.3, True),
    ("2026-10-31T07:19:58Z", "plastic", 0.917, "ACCEPTED", 267, 24.0, False),
    ("2026-10-31T10:04:36Z", "paper", 0.831, "ACCEPTED", 283, 19.2, False),
    ("2026-10-31T16:22:11Z", "unknown", 0.429, "REJECTED", 437, 18.8, True),
    ("2026-11-01T01:04:48Z", "plastic", 0.902, "ACCEPTED", 320, 28.5, False),
    ("2026-11-01T01:36:15Z", "metal", 0.919, "ACCEPTED", 305, 41.1, False),
    ("2026-11-01T02:11:07Z", "paper", 0.888, "ACCEPTED", 239, 15.3, False),
]


def build_sort_events() -> list[dict]:
    events = []
    for i, spec in enumerate(_SORT_SPECS, start=1):
        ts, klass, conf, decision, latency, weight, has_image = spec
        evt_id = f"evt_{ts[:10].replace('-', '')}_{i:03d}"
        events.append(
            {
                "id": evt_id,
                "device_id": DEVICE_ID,
                "timestamp": ts,
                "predicted_class": klass,
                "confidence": conf,
                "decision": decision,
                "latency_ms": latency,
                "weight_g": weight,
                "image_url": f"/media/captures/{evt_id}.jpg" if has_image else None,
                "raw_ai_payload": _ai_payload(
                    klass,
                    conf,
                    frames=5 + (i % 5),
                    extras={"event_id": evt_id, "decision": decision},
                ),
            }
        )
    return events


def build_users(admin_hash: str, operator_hash: str) -> list[dict]:
    return [
        {
            "id": 1,
            "username": "admin",
            "password_hash": admin_hash,
            "display_name": "Quản trị viên",
            "role": "admin",
            "created_at": "2026-09-01T00:00:00Z",
        },
        {
            "id": 2,
            "username": "operator",
            "password_hash": operator_hash,
            "display_name": "Nhân viên vận hành",
            "role": "operator",
            "created_at": "2026-09-15T08:30:00Z",
        },
    ]


def build_devices() -> list[dict]:
    return [
        {
            "id": DEVICE_ID,
            "name": "Thùng Edge AI #001",
            "location": "Khu A - Sảnh chính",
            "status": "ONLINE",
            "hardware_version": "edge-ai-v1.2.0",
            "created_at": "2026-09-20T10:00:00Z",
        }
    ]


def build_alerts() -> list[dict]:
    return [
        {
            "id": "alt_001",
            "device_id": DEVICE_ID,
            "type": "BIN_FULL",
            "severity": "warning",
            "title": "Thùng nhựa gần đầy",
            "message": "Ngăn plastic đạt 92% dung tích",
            "is_resolved": 0,
            "created_at": "2026-11-01T01:10:00Z",
            "resolved_at": None,
        },
        {
            "id": "alt_002",
            "device_id": DEVICE_ID,
            "type": "CAMERA_LOST",
            "severity": "critical",
            "title": "Mất tín hiệu camera",
            "message": "CSI camera không trả frame trong 8 giây — pipeline AI tạm dừng",
            "is_resolved": 1,
            "created_at": "2026-10-28T12:08:00Z",
            "resolved_at": "2026-10-28T12:21:40Z",
        },
        {
            "id": "alt_003",
            "device_id": DEVICE_ID,
            "type": "SERVO_JAM",
            "severity": "critical",
            "title": "Kẹt servo máng xoay",
            "message": "Servo D10 không đạt góc metal sau 3 lần thử",
            "is_resolved": 0,
            "created_at": "2026-10-31T16:28:00Z",
            "resolved_at": None,
        },
        {
            "id": "alt_004",
            "device_id": DEVICE_ID,
            "type": "ARDUINO_DISCONNECT",
            "severity": "critical",
            "title": "Mất kết nối Arduino",
            "message": "Serial /dev/ttyUSB0 timeout — firmware không ACK trong 5s",
            "is_resolved": 1,
            "created_at": "2026-10-25T10:20:00Z",
            "resolved_at": "2026-10-25T10:34:12Z",
        },
        {
            "id": "alt_005",
            "device_id": DEVICE_ID,
            "type": "AI_LOW_CONFIDENCE",
            "severity": "warning",
            "title": "Độ tin cậy AI thấp",
            "message": "3 sự kiện liên tiếp confidence < 0.50, chuyển unknown/REJECTED",
            "is_resolved": 0,
            "created_at": "2026-10-31T16:22:40Z",
            "resolved_at": None,
        },
        {
            "id": "alt_006",
            "device_id": DEVICE_ID,
            "type": "BIN_FULL",
            "severity": "warning",
            "title": "Thùng giấy gần đầy",
            "message": "Ngăn paper đạt 88% dung tích — đã được dọn",
            "is_resolved": 1,
            "created_at": "2026-10-27T18:05:00Z",
            "resolved_at": "2026-10-28T06:40:00Z",
        },
        {
            "id": "alt_007",
            "device_id": DEVICE_ID,
            "type": "OVERHEAT",
            "severity": "warning",
            "title": "Nhiệt độ SoC cao",
            "message": "CPU thermal zone đạt 76.4°C khi infer liên tục",
            "is_resolved": 1,
            "created_at": "2026-10-23T17:18:00Z",
            "resolved_at": "2026-10-23T17:45:00Z",
        },
        {
            "id": "alt_008",
            "device_id": DEVICE_ID,
            "type": "SYSTEM",
            "severity": "info",
            "title": "Khởi động Edge AI",
            "message": "Orchestrator boot xong, mode AUTO, camera + serial OK",
            "is_resolved": 1,
            "created_at": "2026-10-20T06:55:00Z",
            "resolved_at": "2026-10-20T06:55:08Z",
        },
    ]


def build_telemetry() -> list[dict]:
    return [
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-10-28T12:10:00Z",
            "cpu_pct": 71.4,
            "ram_mb": 612.0,
            "temperature_c": 68.2,
            "fps": 0.0,
            "serial_status": "CONNECTED",
            "camera_status": "LOST",
            "bin_plastic_pct": 64.0,
            "bin_metal_pct": 41.0,
            "bin_paper_pct": 73.0,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-10-29T09:00:00Z",
            "cpu_pct": 38.6,
            "ram_mb": 498.5,
            "temperature_c": 54.1,
            "fps": 24.8,
            "serial_status": "CONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 71.0,
            "bin_metal_pct": 48.0,
            "bin_paper_pct": 52.0,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-10-30T14:00:00Z",
            "cpu_pct": 45.2,
            "ram_mb": 521.3,
            "temperature_c": 57.8,
            "fps": 23.1,
            "serial_status": "CONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 79.0,
            "bin_metal_pct": 55.0,
            "bin_paper_pct": 61.0,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-10-31T16:30:00Z",
            "cpu_pct": 58.9,
            "ram_mb": 547.0,
            "temperature_c": 63.5,
            "fps": 19.4,
            "serial_status": "CONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 86.0,
            "bin_metal_pct": 58.0,
            "bin_paper_pct": 67.0,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-11-01T01:00:00Z",
            "cpu_pct": 41.7,
            "ram_mb": 533.8,
            "temperature_c": 56.4,
            "fps": 22.6,
            "serial_status": "CONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 92.0,
            "bin_metal_pct": 60.0,
            "bin_paper_pct": 69.0,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-11-01T02:00:00Z",
            "cpu_pct": 36.2,
            "ram_mb": 510.1,
            "temperature_c": 52.9,
            "fps": 25.3,
            "serial_status": "CONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 92.4,
            "bin_metal_pct": 61.2,
            "bin_paper_pct": 70.1,
        },
        {
            "device_id": DEVICE_ID,
            "recorded_at": "2026-10-25T10:22:00Z",
            "cpu_pct": 22.0,
            "ram_mb": 470.0,
            "temperature_c": 49.8,
            "fps": 0.0,
            "serial_status": "DISCONNECTED",
            "camera_status": "OK",
            "bin_plastic_pct": 48.0,
            "bin_metal_pct": 33.0,
            "bin_paper_pct": 44.0,
        },
    ]


def _sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def write_seed_sql(
    users: list[dict],
    devices: list[dict],
    events: list[dict],
    alerts: list[dict],
    telemetry: list[dict],
    path: Path = SEED_SQL_PATH,
) -> None:
    """Ghi seed.sql (hashes bcrypt thật) để inspect / replay thủ công."""
    lines = [
        "-- AutoBin seed — sinh bởi seed.py (password_hash = passlib bcrypt)",
        "-- Có thể replay: sqlite3 autubin.db < schema.sql && sqlite3 autubin.db < seed.sql",
        "PRAGMA foreign_keys = ON;",
        "",
        "-- users",
    ]
    for u in users:
        lines.append(
            "INSERT INTO users (id, username, password_hash, display_name, role, created_at) VALUES ("
            f"{_sql_literal(u['id'])}, {_sql_literal(u['username'])}, "
            f"{_sql_literal(u['password_hash'])}, {_sql_literal(u['display_name'])}, "
            f"{_sql_literal(u['role'])}, {_sql_literal(u['created_at'])});"
        )
    lines += ["", "-- devices"]
    for d in devices:
        lines.append(
            "INSERT INTO devices (id, name, location, status, hardware_version, created_at) VALUES ("
            f"{_sql_literal(d['id'])}, {_sql_literal(d['name'])}, "
            f"{_sql_literal(d['location'])}, {_sql_literal(d['status'])}, "
            f"{_sql_literal(d['hardware_version'])}, {_sql_literal(d['created_at'])});"
        )
    lines += ["", "-- sort_events"]
    for e in events:
        lines.append(
            "INSERT INTO sort_events (id, device_id, timestamp, predicted_class, confidence, "
            "decision, latency_ms, weight_g, image_url, raw_ai_payload) VALUES ("
            f"{_sql_literal(e['id'])}, {_sql_literal(e['device_id'])}, "
            f"{_sql_literal(e['timestamp'])}, {_sql_literal(e['predicted_class'])}, "
            f"{_sql_literal(e['confidence'])}, {_sql_literal(e['decision'])}, "
            f"{_sql_literal(e['latency_ms'])}, {_sql_literal(e['weight_g'])}, "
            f"{_sql_literal(e['image_url'])}, {_sql_literal(e['raw_ai_payload'])});"
        )
    lines += ["", "-- alerts"]
    for a in alerts:
        lines.append(
            "INSERT INTO alerts (id, device_id, type, severity, title, message, "
            "is_resolved, created_at, resolved_at) VALUES ("
            f"{_sql_literal(a['id'])}, {_sql_literal(a['device_id'])}, "
            f"{_sql_literal(a['type'])}, {_sql_literal(a['severity'])}, "
            f"{_sql_literal(a['title'])}, {_sql_literal(a['message'])}, "
            f"{_sql_literal(a['is_resolved'])}, {_sql_literal(a['created_at'])}, "
            f"{_sql_literal(a['resolved_at'])});"
        )
    lines += ["", "-- telemetry_snapshots"]
    for t in telemetry:
        lines.append(
            "INSERT INTO telemetry_snapshots (device_id, recorded_at, cpu_pct, ram_mb, "
            "temperature_c, fps, serial_status, camera_status, "
            "bin_plastic_pct, bin_metal_pct, bin_paper_pct) VALUES ("
            f"{_sql_literal(t['device_id'])}, {_sql_literal(t['recorded_at'])}, "
            f"{_sql_literal(t['cpu_pct'])}, {_sql_literal(t['ram_mb'])}, "
            f"{_sql_literal(t['temperature_c'])}, {_sql_literal(t['fps'])}, "
            f"{_sql_literal(t['serial_status'])}, {_sql_literal(t['camera_status'])}, "
            f"{_sql_literal(t['bin_plastic_pct'])}, {_sql_literal(t['bin_metal_pct'])}, "
            f"{_sql_literal(t['bin_paper_pct'])});"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def seed_database(conn: sqlite3.Connection) -> dict:
    admin_hash = hash_password("admin123")
    operator_hash = hash_password("operator123")
    users = build_users(admin_hash, operator_hash)
    devices = build_devices()
    events = build_sort_events()
    alerts = build_alerts()
    telemetry = build_telemetry()

    conn.executemany(
        """
        INSERT INTO users (id, username, password_hash, display_name, role, created_at)
        VALUES (:id, :username, :password_hash, :display_name, :role, :created_at)
        """,
        users,
    )
    conn.executemany(
        """
        INSERT INTO devices (id, name, location, status, hardware_version, created_at)
        VALUES (:id, :name, :location, :status, :hardware_version, :created_at)
        """,
        devices,
    )
    conn.executemany(
        """
        INSERT INTO sort_events (
            id, device_id, timestamp, predicted_class, confidence,
            decision, latency_ms, weight_g, image_url, raw_ai_payload
        ) VALUES (
            :id, :device_id, :timestamp, :predicted_class, :confidence,
            :decision, :latency_ms, :weight_g, :image_url, :raw_ai_payload
        )
        """,
        events,
    )
    conn.executemany(
        """
        INSERT INTO alerts (
            id, device_id, type, severity, title, message,
            is_resolved, created_at, resolved_at
        ) VALUES (
            :id, :device_id, :type, :severity, :title, :message,
            :is_resolved, :created_at, :resolved_at
        )
        """,
        alerts,
    )
    conn.executemany(
        """
        INSERT INTO telemetry_snapshots (
            device_id, recorded_at, cpu_pct, ram_mb, temperature_c, fps,
            serial_status, camera_status, bin_plastic_pct, bin_metal_pct, bin_paper_pct
        ) VALUES (
            :device_id, :recorded_at, :cpu_pct, :ram_mb, :temperature_c, :fps,
            :serial_status, :camera_status, :bin_plastic_pct, :bin_metal_pct, :bin_paper_pct
        )
        """,
        telemetry,
    )

    write_seed_sql(users, devices, events, alerts, telemetry)
    return {
        "admin_hash": admin_hash,
        "operator_hash": operator_hash,
        "users": users,
        "events": events,
    }
