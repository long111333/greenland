"""Tạo user + device tối thiểu khi DB chưa có seed.

Không đổi password bcrypt đã có. Không chèn sort_events / alerts
(để nguyên seed đầy đủ của DB agent).
"""

from __future__ import annotations

import sqlite3

from app.constants import DEFAULT_DEVICE_ID
from app.db import get_connection, init_schema
from app.security import hash_password
from app.timeutil import utcnow_iso

_DEMO_USERS = (
    {
        "username": "admin",
        "password": "admin123",
        "display_name": "Quản trị viên",
        "role": "admin",
    },
    {
        "username": "operator",
        "password": "operator123",
        "display_name": "Nhân viên vận hành",
        "role": "operator",
    },
)


def bootstrap_if_empty(conn: sqlite3.Connection) -> None:
    now = utcnow_iso()
    for user in _DEMO_USERS:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (user["username"],),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, display_name, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["username"],
                    hash_password(user["password"]),
                    user["display_name"],
                    user["role"],
                    now,
                ),
            )
        elif row["password_hash"] == user["password"]:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(user["password"]), row["id"]),
            )

    device = conn.execute(
        "SELECT id FROM devices WHERE id = ?",
        (DEFAULT_DEVICE_ID,),
    ).fetchone()
    if device is None:
        conn.execute(
            """
            INSERT INTO devices (id, name, location, status, hardware_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                DEFAULT_DEVICE_ID,
                "Thùng Edge AI #001",
                "Khu A - Sảnh chính",
                "ONLINE",
                "V1.0-ArduinoUno",
                now,
            ),
        )
    conn.commit()


def init_and_bootstrap() -> None:
    conn = get_connection()
    try:
        init_schema(conn)
        bootstrap_if_empty(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_and_bootstrap()
    print("bootstrap complete")
