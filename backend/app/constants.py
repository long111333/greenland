"""Hằng số domain — SHARED_CONTRACT.md §1."""

DEFAULT_DEVICE_ID = "BIN_EDGE_AI_001"

# Hệ số quy đổi quỹ (VND / kg)
FUND_RATES_VND_PER_KG: dict[str, int] = {
    "plastic": 2000,
    "metal": 20000,
    "paper": 3000,
    "unknown": 0,
}

BIN_FULL_THRESHOLD_PCT = 90.0

BUYER_CONTACT = {
    "phone": "0325916822",
    "email": "truongngoclong.21072005@gmail.com",
}

WASTE_CLASSES: tuple[dict[str, str | int], ...] = (
    {"class_id": "plastic", "label": "Nhựa", "estimated_avg_weight_g": 25},
    {"class_id": "metal", "label": "Kim loại", "estimated_avg_weight_g": 40},
    {"class_id": "paper", "label": "Giấy", "estimated_avg_weight_g": 15},
    {"class_id": "unknown", "label": "Không rõ", "estimated_avg_weight_g": 20},
)

ALERT_TYPES = (
    "BIN_FULL",
    "CAMERA_LOST",
    "SERVO_JAM",
    "ARDUINO_DISCONNECT",
    "AI_LOW_CONFIDENCE",
    "OVERHEAT",
    "SYSTEM",
)

ALERT_SEVERITIES = ("info", "warning", "critical")
SORT_DECISIONS = ("ACCEPTED", "REJECTED")
DEVICE_STATUSES = ("ONLINE", "OFFLINE", "ERROR")
SYSTEM_MODES = ("AUTO", "MANUAL", "STOP", "HOME")
PERIODS = ("day", "week", "month", "all")
