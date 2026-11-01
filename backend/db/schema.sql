-- AutoBin SQLite schema — khớp 100% SHARED_CONTRACT.md §3
-- File DB: backend/db/autubin.db
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT,
    role          TEXT CHECK (role IN ('admin', 'operator', 'viewer')),
    created_at    TEXT
);

CREATE TABLE devices (
    id               TEXT PRIMARY KEY,
    name             TEXT,
    location         TEXT,
    status           TEXT CHECK (status IN ('ONLINE', 'OFFLINE', 'ERROR')),
    hardware_version TEXT,
    created_at       TEXT
);

CREATE TABLE sort_events (
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
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE alerts (
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

CREATE TABLE telemetry_snapshots (
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

CREATE INDEX idx_sort_events_device_ts
    ON sort_events (device_id, timestamp);

CREATE INDEX idx_sort_events_class
    ON sort_events (predicted_class);

CREATE INDEX idx_alerts_device_resolved
    ON alerts (device_id, is_resolved);

CREATE INDEX idx_telemetry_device_ts
    ON telemetry_snapshots (device_id, recorded_at);
