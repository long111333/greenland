"""Ingest Hardware / Edge AI. Header: X-Device-Key."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_db, require_device_key
from app.queries import (
    alert_dict,
    dump_json,
    require_device,
    sort_event_dict,
    telemetry_dict,
)
from app.schemas import AlertIn, AlertOut, SortEventIn, SortEventOut, TelemetryIn, TelemetryOut
from app.timeutil import utcnow_iso

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    dependencies=[Depends(require_device_key)],
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@router.post("/sort-event", response_model=SortEventOut)
def ingest_sort_event(
    body: SortEventIn,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> SortEventOut:
    require_device(conn, body.device_id)
    event_id = _new_id("evt")
    timestamp = (body.timestamp or "").strip() or utcnow_iso()
    try:
        conn.execute(
            """
            INSERT INTO sort_events (
                id, device_id, timestamp, predicted_class, confidence,
                decision, latency_ms, weight_g, image_url, raw_ai_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                body.device_id,
                timestamp,
                body.predicted_class,
                body.confidence,
                body.decision,
                body.latency_ms,
                body.weight_g,
                body.image_url or None,
                dump_json(body.raw_ai_payload),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Record violates database constraints") from exc
    row = conn.execute(
        """
        SELECT id, device_id, timestamp, predicted_class, confidence, decision,
               latency_ms, weight_g, image_url, raw_ai_payload
        FROM sort_events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()
    return SortEventOut(**sort_event_dict(row))


@router.post("/alert", response_model=AlertOut)
def ingest_alert(
    body: AlertIn,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> AlertOut:
    require_device(conn, body.device_id)
    alert_id = _new_id("alt")
    created_at = utcnow_iso()
    try:
        conn.execute(
            """
            INSERT INTO alerts (
                id, device_id, type, severity, title, message,
                is_resolved, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL)
            """,
            (
                alert_id,
                body.device_id,
                body.type,
                body.severity,
                body.title,
                body.message,
                created_at,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Record violates database constraints") from exc
    row = conn.execute(
        """
        SELECT id, device_id, type, severity, title, message,
               is_resolved, created_at, resolved_at
        FROM alerts
        WHERE id = ?
        """,
        (alert_id,),
    ).fetchone()
    return AlertOut(**alert_dict(row))


@router.post("/telemetry", response_model=TelemetryOut)
def ingest_telemetry(
    body: TelemetryIn,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> TelemetryOut:
    require_device(conn, body.device_id)
    recorded_at = (body.recorded_at or "").strip() or utcnow_iso()
    try:
        cursor = conn.execute(
            """
            INSERT INTO telemetry_snapshots (
                device_id, recorded_at, cpu_pct, ram_mb, temperature_c, fps,
                serial_status, camera_status,
                bin_plastic_pct, bin_metal_pct, bin_paper_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.device_id,
                recorded_at,
                body.cpu_pct,
                body.ram_mb,
                body.temperature_c,
                body.fps,
                body.serial_status,
                body.camera_status,
                body.bin_plastic_pct,
                body.bin_metal_pct,
                body.bin_paper_pct,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Record violates database constraints") from exc
    row = conn.execute(
        """
        SELECT id, device_id, recorded_at, cpu_pct, ram_mb, temperature_c, fps,
               serial_status, camera_status,
               bin_plastic_pct, bin_metal_pct, bin_paper_pct
        FROM telemetry_snapshots
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return TelemetryOut(**telemetry_dict(row))
