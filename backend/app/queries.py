"""Đọc ghi dòng SQLite thành dict khớp contract."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import HTTPException


def require_device(conn: sqlite3.Connection, device_id: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT id, name, location, status, hardware_version, created_at
        FROM devices
        WHERE id = ?
        """,
        (device_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return row


def device_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "location": row["location"],
        "status": row["status"],
        "hardware_version": row["hardware_version"],
        "created_at": row["created_at"],
    }


def alert_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "type": row["type"],
        "severity": row["severity"],
        "title": row["title"],
        "message": row["message"],
        "is_resolved": bool(row["is_resolved"]),
        "created_at": row["created_at"],
        "resolved_at": row["resolved_at"],
    }


def dump_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def load_json(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def sort_event_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "timestamp": row["timestamp"],
        "predicted_class": row["predicted_class"],
        "confidence": row["confidence"],
        "decision": row["decision"],
        "latency_ms": row["latency_ms"],
        "weight_g": row["weight_g"],
        "image_url": row["image_url"],
        "raw_ai_payload": load_json(row["raw_ai_payload"]),
    }


def telemetry_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "recorded_at": row["recorded_at"],
        "cpu_pct": row["cpu_pct"],
        "ram_mb": row["ram_mb"],
        "temperature_c": row["temperature_c"],
        "fps": row["fps"],
        "serial_status": row["serial_status"],
        "camera_status": row["camera_status"],
        "bin_plastic_pct": row["bin_plastic_pct"],
        "bin_metal_pct": row["bin_metal_pct"],
        "bin_paper_pct": row["bin_paper_pct"],
    }
