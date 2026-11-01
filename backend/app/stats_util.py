"""Aggregate helpers for overview / history / fund."""

from __future__ import annotations

import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.constants import (
    BIN_FULL_THRESHOLD_PCT,
    FUND_RATES_VND_PER_KG,
    WASTE_CLASSES,
)


def money_round(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def qty_round(value: float, places: int = 3) -> float:
    quant = Decimal("1") if places == 0 else Decimal("0." + ("0" * (places - 1)) + "1")
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))


def bucket(class_id: str, label: str, row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        count = accepted = rejected = 0
        grams = 0.0
    else:
        count = int(row["cnt"])
        accepted = int(row["accepted"])
        rejected = int(row["rejected"])
        grams = float(row["weight_g"] or 0)
    weight_g = qty_round(grams, 3)
    return {
        "class_id": class_id,
        "label": label,
        "count": count,
        "weight_kg": qty_round(weight_g / 1000.0, 3),
        "weight_g": weight_g,
        "accepted": accepted,
        "rejected": rejected,
    }


def categories_from_grouped(grouped: dict[str, sqlite3.Row]) -> list[dict[str, Any]]:
    leftover = dict(grouped)
    categories: list[dict[str, Any]] = []
    for spec in WASTE_CLASSES:
        class_id = str(spec["class_id"])
        categories.append(bucket(class_id, str(spec["label"]), leftover.pop(class_id, None)))
    for class_id in sorted(key for key in leftover if key is not None):
        categories.append(bucket(str(class_id), str(class_id), leftover[class_id]))
    return categories


def totals_from_categories(categories: list[dict[str, Any]]) -> dict[str, Any]:
    total_g = qty_round(sum(item["weight_g"] for item in categories), 3)
    return {
        "count": sum(item["count"] for item in categories),
        "weight_kg": qty_round(total_g / 1000.0, 3),
        "accepted": sum(item["accepted"] for item in categories),
        "rejected": sum(item["rejected"] for item in categories),
    }


def aggregate_events(
    conn: sqlite3.Connection,
    *,
    device_id: str,
    cleaned: bool | None,
    batch_id: str | None = None,
    extra_sql: str = "",
    extra_params: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """cleaned=False → clean_batch_id IS NULL; True → NOT NULL; None → all."""
    sql = """
        SELECT predicted_class AS class_id,
               COUNT(*) AS cnt,
               COALESCE(SUM(weight_g), 0) AS weight_g,
               COALESCE(SUM(CASE WHEN decision = 'ACCEPTED' THEN 1 ELSE 0 END), 0) AS accepted,
               COALESCE(SUM(CASE WHEN decision = 'REJECTED' THEN 1 ELSE 0 END), 0) AS rejected
        FROM sort_events
        WHERE device_id = ?
    """
    params: list[Any] = [device_id]
    if batch_id is not None:
        sql += " AND clean_batch_id = ?"
        params.append(batch_id)
    elif cleaned is False:
        sql += " AND clean_batch_id IS NULL"
    elif cleaned is True:
        sql += " AND clean_batch_id IS NOT NULL"
    if extra_sql:
        sql += " " + extra_sql
        params.extend(extra_params or [])
    sql += " GROUP BY predicted_class"
    grouped = {row["class_id"]: row for row in conn.execute(sql, params).fetchall()}
    return categories_from_grouped(grouped)


def latest_bins(conn: sqlite3.Connection, device_id: str) -> dict[str, float]:
    row = conn.execute(
        """
        SELECT bin_plastic_pct, bin_metal_pct, bin_paper_pct
        FROM telemetry_snapshots
        WHERE device_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (device_id,),
    ).fetchone()
    if row is None:
        return {"plastic": 0.0, "metal": 0.0, "paper": 0.0}
    return {
        "plastic": float(row["bin_plastic_pct"] or 0),
        "metal": float(row["bin_metal_pct"] or 0),
        "paper": float(row["bin_paper_pct"] or 0),
    }


def bins_payload(bins: dict[str, float]) -> dict[str, Any]:
    values = [bins.get("plastic", 0.0), bins.get("metal", 0.0), bins.get("paper", 0.0)]
    max_pct = max(values) if values else 0.0
    return {
        "plastic_pct": qty_round(bins.get("plastic", 0.0), 1),
        "metal_pct": qty_round(bins.get("metal", 0.0), 1),
        "paper_pct": qty_round(bins.get("paper", 0.0), 1),
        "max_pct": qty_round(max_pct, 1),
        "is_over_90": max_pct >= BIN_FULL_THRESHOLD_PCT,
    }


def fund_lines(categories: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    lines: list[dict[str, Any]] = []
    total = 0
    for item in categories:
        class_id = item["class_id"]
        if class_id == "unknown":
            continue
        rate = FUND_RATES_VND_PER_KG.get(class_id, 0)
        amount = money_round(float(item["weight_kg"]) * rate)
        total += amount
        lines.append(
            {
                "class_id": class_id,
                "label": item["label"],
                "weight_kg": item["weight_kg"],
                "rate_vnd_per_kg": rate,
                "amount_vnd": amount,
            }
        )
    return lines, total
