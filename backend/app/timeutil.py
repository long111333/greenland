"""Mốc thời gian UTC và cửa sổ thống kê theo giờ Việt Nam (UTC+7, không DST)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def period_cutoff(period: str) -> str | None:
    """Trả về mốc UTC `YYYY-MM-DDTHH:MM:SS` (không hậu tố Z) hoặc None nếu `all`.

    - day: 00:00 hôm nay theo Asia/Ho_Chi_Minh
    - week: 00:00 thứ Hai tuần này
    - month: 00:00 ngày 1 tháng này
    - all / custom: không lọc (custom dùng from/to riêng)
    """
    if period in ("all", "custom"):
        return None
    now = datetime.now(VN_TZ)
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Invalid period: {period}")
    return start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def parse_vn_date(value: str, *, end_of_day: bool = False) -> str:
    """Parse `YYYY-MM-DD` (ngày VN) → UTC `YYYY-MM-DDTHH:MM:SS` (không Z).

    end_of_day=True → 23:59:59 ngày đó (lọc inclusive tới hết ngày).
    """
    day = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    if end_of_day:
        local = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=VN_TZ)
    else:
        local = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=VN_TZ)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
