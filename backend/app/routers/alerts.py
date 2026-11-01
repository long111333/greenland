"""GET /alerts và POST /alerts/{id}/resolve."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_current_user, get_db
from app.queries import alert_dict, require_device
from app.schemas import AlertListResponse, AlertOut
from app.timeutil import utcnow_iso

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)],
)

_ALERT_COLUMNS = """
    id, device_id, type, severity, title, message, is_resolved, created_at, resolved_at
"""


@router.get("", response_model=AlertListResponse)
def list_alerts(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    device_id: str | None = Query(default=None),
    resolved: bool | None = Query(default=None),
) -> AlertListResponse:
    if device_id is not None:
        require_device(conn, device_id)
    clauses: list[str] = []
    params: list[Any] = []
    if device_id is not None:
        clauses.append("device_id = ?")
        params.append(device_id)
    if resolved is not None:
        clauses.append("COALESCE(is_resolved, 0) = ?")
        params.append(1 if resolved else 0)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        f"""
        SELECT {_ALERT_COLUMNS}
        FROM alerts
        {where}
        ORDER BY created_at DESC, id DESC
        """,
        params,
    ).fetchall()
    items = [AlertOut(**alert_dict(row)) for row in rows]
    return AlertListResponse(items=items, total=len(items))


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: str,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> AlertOut:
    row = conn.execute(
        f"SELECT {_ALERT_COLUMNS} FROM alerts WHERE id = ?",
        (alert_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not row["is_resolved"]:
        conn.execute(
            "UPDATE alerts SET is_resolved = 1, resolved_at = ? WHERE id = ?",
            (utcnow_iso(), alert_id),
        )
        conn.commit()
        row = conn.execute(
            f"SELECT {_ALERT_COLUMNS} FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()
    return AlertOut(**alert_dict(row))
