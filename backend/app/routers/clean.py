"""POST /clean — chuyển rác hiện tại sang History (clean batch)."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.constants import DEFAULT_DEVICE_ID
from app.deps import get_current_user, get_db
from app.queries import require_device
from app.schemas import CleanBatchOut
from app.stats_util import aggregate_events, totals_from_categories
from app.timeutil import utcnow_iso

router = APIRouter(
    prefix="/clean",
    tags=["clean"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CleanBatchOut)
def clean_bins(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    user: Annotated[sqlite3.Row, Depends(get_current_user)],
    device_id: str = Query(default=DEFAULT_DEVICE_ID),
) -> CleanBatchOut:
    require_device(conn, device_id)
    pending = conn.execute(
        """
        SELECT COUNT(*) AS n FROM sort_events
        WHERE device_id = ? AND clean_batch_id IS NULL
        """,
        (device_id,),
    ).fetchone()["n"]
    if int(pending) == 0:
        raise HTTPException(status_code=400, detail="Không có rác để dọn (Clean)")

    batch_id = f"clean_{uuid.uuid4().hex[:12]}"
    cleaned_at = utcnow_iso()
    conn.execute(
        """
        INSERT INTO clean_batches (id, device_id, cleaned_at, cleaned_by, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (batch_id, device_id, cleaned_at, int(user["id"]), "manual_clean"),
    )
    conn.execute(
        """
        UPDATE sort_events
        SET clean_batch_id = ?
        WHERE device_id = ? AND clean_batch_id IS NULL
        """,
        (batch_id, device_id),
    )
    # Reset dung tích thùng sau khi clean
    conn.execute(
        """
        INSERT INTO telemetry_snapshots (
            device_id, recorded_at, cpu_pct, ram_mb, temperature_c, fps,
            serial_status, camera_status, bin_plastic_pct, bin_metal_pct, bin_paper_pct
        )
        VALUES (?, ?, 30.0, 500.0, 50.0, 20.0, 'CONNECTED', 'OK', 0.0, 0.0, 0.0)
        """,
        (device_id, cleaned_at),
    )
    # Resolve BIN_FULL alerts
    conn.execute(
        """
        UPDATE alerts
        SET is_resolved = 1, resolved_at = ?
        WHERE device_id = ? AND type = 'BIN_FULL' AND COALESCE(is_resolved, 0) = 0
        """,
        (cleaned_at, device_id),
    )
    conn.commit()

    categories = aggregate_events(conn, device_id=device_id, cleaned=True, batch_id=batch_id)
    return CleanBatchOut(
        id=batch_id,
        device_id=device_id,
        cleaned_at=cleaned_at,
        categories=categories,
        totals=totals_from_categories(categories),
    )
