#!/usr/bin/env python3
"""Tạo lại autubin.db sạch từ schema.sql + seed.py.

Chạy từ backend/db/:
    python init_db.py
    python init_db.py --force
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "autubin.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
TABLES = ("users", "devices", "sort_events", "alerts", "telemetry_snapshots")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Init AutoBin SQLite (schema + seed)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Xóa autubin.db nếu đã tồn tại (mặc định cũng tạo lại sạch)",
    )
    return parser.parse_args()


def recreate_db() -> sqlite3.Connection:
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing {DB_PATH}")
    if not SCHEMA_PATH.exists():
        sys.exit(f"Missing schema: {SCHEMA_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {}
    for table in TABLES:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def main() -> int:
    parse_args()  # --force accepted; always recreate a clean DB
    sys.path.insert(0, str(DB_DIR))
    from seed import verify_password

    conn = recreate_db()
    try:
        from seed import seed_database

        seed_database(conn)
        conn.commit()
        counts = table_counts(conn)

        stored_admin = conn.execute(
            "SELECT password_hash FROM users WHERE username = 'admin'"
        ).fetchone()["password_hash"]
        stored_operator = conn.execute(
            "SELECT password_hash FROM users WHERE username = 'operator'"
        ).fetchone()["password_hash"]
        admin_ok = verify_password("admin123", stored_admin)
        operator_ok = verify_password("operator123", stored_operator)

        samples = conn.execute(
            """
            SELECT id, device_id, timestamp, predicted_class, confidence,
                   decision, latency_ms, weight_g, image_url, raw_ai_payload
            FROM sort_events
            ORDER BY timestamp
            LIMIT 3
            """
        ).fetchall()
    finally:
        conn.close()

    print(f"Created {DB_PATH}")
    print("Row counts:")
    for table in TABLES:
        print(f"  {table}: {counts[table]}")
    print(
        "passlib bcrypt verify: "
        f"admin/admin123={'OK' if admin_ok else 'FAIL'} "
        f"operator/operator123={'OK' if operator_ok else 'FAIL'}"
    )
    print("Sample sort_events:")
    for row in samples:
        item = dict(row)
        if item.get("raw_ai_payload"):
            item["raw_ai_payload"] = json.loads(item["raw_ai_payload"])
        print(json.dumps(item, ensure_ascii=False, indent=2))

    if not admin_ok or not operator_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
