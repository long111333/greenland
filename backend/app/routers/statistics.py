"""GET /statistics/overview — chỉ sự kiện chưa clean (+ dung tích thùng)."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.constants import DEFAULT_DEVICE_ID
from app.deps import get_current_user, get_db
from app.queries import require_device
from app.schemas import OverviewResponse, Period
from app.stats_util import (
    aggregate_events,
    bins_payload,
    latest_bins,
    totals_from_categories,
)
from app.timeutil import parse_vn_date, period_cutoff, utcnow_iso

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/overview", response_model=OverviewResponse)
def overview(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    device_id: str = Query(default=DEFAULT_DEVICE_ID),
    period: Period = Query(default="all"),
    date_from: str | None = Query(default=None, alias="from", description="YYYY-MM-DD (VN)"),
    date_to: str | None = Query(default=None, alias="to", description="YYYY-MM-DD (VN)"),
) -> OverviewResponse:
    device = require_device(conn, device_id)
    extra_sql = ""
    extra_params: list[Any] = []
    effective_period: str = period

    if date_from or date_to:
        if not date_from or not date_to:
            raise HTTPException(
                status_code=400,
                detail="Both 'from' and 'to' (YYYY-MM-DD) are required for a custom range",
            )
        try:
            start_utc = parse_vn_date(date_from, end_of_day=False)
            end_utc = parse_vn_date(date_to, end_of_day=True)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format; use YYYY-MM-DD",
            ) from exc
        if start_utc > end_utc:
            raise HTTPException(status_code=400, detail="'from' must be on or before 'to'")
        extra_sql = """
          AND substr(replace(replace("timestamp", ' ', 'T'), 'Z', ''), 1, 19) >= ?
          AND substr(replace(replace("timestamp", ' ', 'T'), 'Z', ''), 1, 19) <= ?
        """
        extra_params = [start_utc, end_utc]
        effective_period = "custom"
    else:
        cutoff = period_cutoff(period)
        if cutoff is not None:
            extra_sql = """
              AND substr(replace(replace("timestamp", ' ', 'T'), 'Z', ''), 1, 19) >= ?
            """
            extra_params = [cutoff]

    categories = aggregate_events(
        conn,
        device_id=device_id,
        cleaned=False,
        extra_sql=extra_sql,
        extra_params=extra_params,
    )
    unresolved = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM alerts
        WHERE device_id = ? AND COALESCE(is_resolved, 0) = 0
        """,
        (device_id,),
    ).fetchone()["n"]
    bins = bins_payload(latest_bins(conn, device_id))

    return OverviewResponse(
        device_id=device["id"],
        device_name=device["name"] or device["id"],
        location=device["location"] or "",
        period=effective_period,
        as_of=utcnow_iso(),
        categories=categories,
        totals=totals_from_categories(categories),
        unresolved_alert_count=int(unresolved),
        bins=bins,
    )
