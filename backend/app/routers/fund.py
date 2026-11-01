"""GET /fund — tổng kg History + Overview × hệ số VND."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.constants import BUYER_CONTACT, DEFAULT_DEVICE_ID
from app.deps import get_current_user, get_db
from app.queries import require_device
from app.schemas import FundResponse
from app.stats_util import aggregate_events, fund_lines, qty_round

router = APIRouter(
    prefix="/fund",
    tags=["fund"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=FundResponse)
def get_fund(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    device_id: str = Query(default=DEFAULT_DEVICE_ID),
) -> FundResponse:
    require_device(conn, device_id)
    current = aggregate_events(conn, device_id=device_id, cleaned=False)
    history = aggregate_events(conn, device_id=device_id, cleaned=True)

    merged: dict[str, dict] = {}
    for item in current + history:
        key = item["class_id"]
        if key not in merged:
            merged[key] = {
                "class_id": key,
                "label": item["label"],
                "count": 0,
                "weight_kg": 0.0,
                "weight_g": 0.0,
                "accepted": 0,
                "rejected": 0,
            }
        merged[key]["count"] += item["count"]
        merged[key]["weight_g"] = qty_round(merged[key]["weight_g"] + item["weight_g"], 3)
        merged[key]["weight_kg"] = qty_round(merged[key]["weight_g"] / 1000.0, 3)
        merged[key]["accepted"] += item["accepted"]
        merged[key]["rejected"] += item["rejected"]

    order = ["plastic", "metal", "paper", "unknown"]
    categories = [merged[k] for k in order if k in merged]
    lines, total_vnd = fund_lines(categories)

    current_kg = qty_round(sum(i["weight_kg"] for i in current if i["class_id"] != "unknown"), 3)
    history_kg = qty_round(sum(i["weight_kg"] for i in history if i["class_id"] != "unknown"), 3)

    return FundResponse(
        current_weight_kg=current_kg,
        history_weight_kg=history_kg,
        total_weight_kg=qty_round(current_kg + history_kg, 3),
        lines=lines,
        total_vnd=total_vnd,
        contact_phone=BUYER_CONTACT["phone"],
        contact_email=BUYER_CONTACT["email"],
    )
