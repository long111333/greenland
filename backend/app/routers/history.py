"""GET /history — các lô Clean theo loại rác."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.constants import DEFAULT_DEVICE_ID
from app.deps import get_current_user, get_db
from app.queries import require_device
from app.schemas import CleanBatchOut, HistoryResponse
from app.stats_util import aggregate_events, totals_from_categories

router = APIRouter(
    prefix="/history",
    tags=["history"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=HistoryResponse)
def list_history(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    device_id: str = Query(default=DEFAULT_DEVICE_ID),
) -> HistoryResponse:
    require_device(conn, device_id)
    rows = conn.execute(
        """
        SELECT id, device_id, cleaned_at
        FROM clean_batches
        WHERE device_id = ?
        ORDER BY cleaned_at DESC, id DESC
        """,
        (device_id,),
    ).fetchall()
    items: list[CleanBatchOut] = []
    for row in rows:
        categories = aggregate_events(
            conn,
            device_id=device_id,
            cleaned=True,
            batch_id=row["id"],
        )
        items.append(
            CleanBatchOut(
                id=row["id"],
                device_id=row["device_id"],
                cleaned_at=row["cleaned_at"],
                categories=categories,
                totals=totals_from_categories(categories),
            )
        )
    return HistoryResponse(items=items, total=len(items))
