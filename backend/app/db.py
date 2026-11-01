"""SQLite tới backend/db/autubin.db.

Schema tạo bằng CREATE IF NOT EXISTS — không ghi đè bảng hay seed của DB agent.
"""

from __future__ import annotations

import sqlite3

from app.config import get_settings

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT,
    role          TEXT CHECK (role IN ('admin', 'operator', 'viewer')),
    phone         TEXT,
    email         TEXT,
    address       TEXT,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS devices (
    id               TEXT PRIMARY KEY,
    name             TEXT,
    location         TEXT,
    status           TEXT CHECK (status IN ('ONLINE', 'OFFLINE', 'ERROR')),
    hardware_version TEXT,
    created_at       TEXT
);

CREATE TABLE IF NOT EXISTS sort_events (
    id              TEXT PRIMARY KEY,
    device_id       TEXT NOT NULL,
    timestamp       TEXT,
    predicted_class TEXT CHECK (predicted_class IN ('plastic', 'metal', 'paper', 'unknown')),
    confidence      REAL,
    decision        TEXT CHECK (decision IN ('ACCEPTED', 'REJECTED')),
    latency_ms      INTEGER,
    weight_g        REAL,
    image_url       TEXT,
    raw_ai_payload  TEXT,
    clean_batch_id  TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS clean_batches (
    id           TEXT PRIMARY KEY,
    device_id    TEXT NOT NULL,
    cleaned_at   TEXT NOT NULL,
    cleaned_by   INTEGER,
    note         TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id          TEXT PRIMARY KEY,
    device_id   TEXT NOT NULL,
    type        TEXT CHECK (type IN (
                    'BIN_FULL',
                    'CAMERA_LOST',
                    'SERVO_JAM',
                    'ARDUINO_DISCONNECT',
                    'AI_LOW_CONFIDENCE',
                    'OVERHEAT',
                    'SYSTEM'
                )),
    severity    TEXT CHECK (severity IN ('info', 'warning', 'critical')),
    title       TEXT,
    message     TEXT,
    is_resolved INTEGER CHECK (is_resolved IN (0, 1)),
    created_at  TEXT,
    resolved_at TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS telemetry_snapshots (
    id              INTEGER PRIMARY KEY,
    device_id       TEXT,
    recorded_at     TEXT,
    cpu_pct         REAL,
    ram_mb          REAL,
    temperature_c   REAL,
    fps             REAL,
    serial_status   TEXT,
    camera_status   TEXT,
    bin_plastic_pct REAL,
    bin_metal_pct   REAL,
    bin_paper_pct   REAL,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE INDEX IF NOT EXISTS idx_sort_events_device_ts
    ON sort_events (device_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_sort_events_class
    ON sort_events (predicted_class);

CREATE INDEX IF NOT EXISTS idx_alerts_device_resolved
    ON alerts (device_id, is_resolved);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_ts
    ON telemetry_snapshots (device_id, recorded_at);
"""

# Index phụ thuộc cột mới — tạo sau ALTER TABLE.
_POST_MIGRATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_sort_events_clean
    ON sort_events (device_id, clean_batch_id);

CREATE INDEX IF NOT EXISTS idx_clean_batches_device_ts
    ON clean_batches (device_id, cleaned_at);
"""

# Cột có thể thêm nếu bảng đã tồn tại nhưng thiếu field (không đụng PK).
_ADDABLE_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "users": (
        ("password_hash", "TEXT"),
        ("display_name", "TEXT"),
        ("role", "TEXT"),
        ("phone", "TEXT"),
        ("email", "TEXT"),
        ("address", "TEXT"),
        ("created_at", "TEXT"),
    ),
    "devices": (
        ("name", "TEXT"),
        ("location", "TEXT"),
        ("status", "TEXT"),
        ("hardware_version", "TEXT"),
        ("created_at", "TEXT"),
    ),
    "sort_events": (
        ("device_id", "TEXT"),
        ("timestamp", "TEXT"),
        ("predicted_class", "TEXT"),
        ("confidence", "REAL"),
        ("decision", "TEXT"),
        ("latency_ms", "INTEGER"),
        ("weight_g", "REAL"),
        ("image_url", "TEXT"),
        ("raw_ai_payload", "TEXT"),
        ("clean_batch_id", "TEXT"),
    ),
    "clean_batches": (
        ("device_id", "TEXT"),
        ("cleaned_at", "TEXT"),
        ("cleaned_by", "INTEGER"),
        ("note", "TEXT"),
    ),
    "alerts": (
        ("device_id", "TEXT"),
        ("type", "TEXT"),
        ("severity", "TEXT"),
        ("title", "TEXT"),
        ("message", "TEXT"),
        ("is_resolved", "INTEGER"),
        ("created_at", "TEXT"),
        ("resolved_at", "TEXT"),
    ),
    "telemetry_snapshots": (
        ("device_id", "TEXT"),
        ("recorded_at", "TEXT"),
        ("cpu_pct", "REAL"),
        ("ram_mb", "REAL"),
        ("temperature_c", "REAL"),
        ("fps", "REAL"),
        ("serial_status", "TEXT"),
        ("camera_status", "TEXT"),
        ("bin_plastic_pct", "REAL"),
        ("bin_metal_pct", "REAL"),
        ("bin_paper_pct", "REAL"),
    ),
}


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: FastAPI chạy sync deps trong threadpool,
    # get_db và get_current_user có thể không cùng thread.
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _ensure_columns(conn: sqlite3.Connection) -> None:
    for table, columns in _ADDABLE_COLUMNS.items():
        existing = _existing_columns(conn, table)
        if not existing:
            continue
        for name, decl in columns:
            if name not in existing:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN "{name}" {decl}')


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    _ensure_columns(conn)
    conn.executescript(_POST_MIGRATE_INDEXES)
    conn.commit()
