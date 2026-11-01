"""Request / response models — SHARED_CONTRACT.md §4."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

WasteClass = Literal["plastic", "metal", "paper", "unknown"]
SortDecision = Literal["ACCEPTED", "REJECTED"]
AlertType = Literal[
    "BIN_FULL",
    "CAMERA_LOST",
    "SERVO_JAM",
    "ARDUINO_DISCONNECT",
    "AI_LOW_CONFIDENCE",
    "OVERHEAT",
    "SYSTEM",
]
AlertSeverity = Literal["info", "warning", "critical"]
Period = Literal["day", "week", "month", "all", "custom"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    role: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserOut


class OkResponse(BaseModel):
    ok: bool


class ProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    display_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)


class CategoryStat(BaseModel):
    class_id: str
    label: str
    count: int
    weight_kg: float
    weight_g: float
    accepted: int
    rejected: int


class OverviewTotals(BaseModel):
    count: int
    weight_kg: float
    accepted: int
    rejected: int


class BinsCapacity(BaseModel):
    plastic_pct: float
    metal_pct: float
    paper_pct: float
    max_pct: float
    is_over_90: bool


class OverviewResponse(BaseModel):
    device_id: str
    device_name: str
    location: str
    period: str
    as_of: str
    categories: list[CategoryStat]
    totals: OverviewTotals
    unresolved_alert_count: int
    bins: BinsCapacity | None = None


class CleanBatchOut(BaseModel):
    id: str
    device_id: str
    cleaned_at: str
    categories: list[CategoryStat]
    totals: OverviewTotals


class HistoryResponse(BaseModel):
    items: list[CleanBatchOut]
    total: int


class FundLine(BaseModel):
    class_id: str
    label: str
    weight_kg: float
    rate_vnd_per_kg: int
    amount_vnd: int


class FundResponse(BaseModel):
    current_weight_kg: float
    history_weight_kg: float
    total_weight_kg: float
    lines: list[FundLine]
    total_vnd: int
    contact_phone: str
    contact_email: str


class AlertOut(BaseModel):
    id: str
    device_id: str
    type: str
    severity: str
    title: str | None = None
    message: str | None = None
    is_resolved: bool
    created_at: str | None = None
    resolved_at: str | None = None


class AlertListResponse(BaseModel):
    items: list[AlertOut]
    total: int


class DeviceOut(BaseModel):
    id: str
    name: str | None = None
    location: str | None = None
    status: str | None = None
    hardware_version: str | None = None
    created_at: str | None = None


class SortEventIn(BaseModel):
    device_id: str = Field(min_length=1)
    predicted_class: WasteClass
    confidence: float = Field(ge=0, le=1)
    decision: SortDecision
    latency_ms: int = Field(ge=0)
    weight_g: float | None = None
    image_url: str | None = None
    raw_ai_payload: Any = None
    timestamp: str | None = None

    @field_validator("device_id", mode="before")
    @classmethod
    def _strip_device(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("predicted_class", mode="before")
    @classmethod
    def _lower_class(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("decision", mode="before")
    @classmethod
    def _upper_decision(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class SortEventOut(BaseModel):
    id: str
    device_id: str
    timestamp: str | None = None
    predicted_class: str
    confidence: float | None = None
    decision: str
    latency_ms: int | None = None
    weight_g: float | None = None
    image_url: str | None = None
    raw_ai_payload: Any = None


class AlertIn(BaseModel):
    device_id: str = Field(min_length=1)
    type: AlertType
    severity: AlertSeverity
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)

    @field_validator("device_id", mode="before")
    @classmethod
    def _strip_device(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("type", mode="before")
    @classmethod
    def _upper_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("severity", mode="before")
    @classmethod
    def _lower_severity(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class TelemetryIn(BaseModel):
    device_id: str = Field(min_length=1)
    recorded_at: str | None = None
    cpu_pct: float | None = None
    ram_mb: float | None = None
    temperature_c: float | None = None
    fps: float | None = None
    serial_status: str | None = None
    camera_status: str | None = None
    bin_plastic_pct: float | None = None
    bin_metal_pct: float | None = None
    bin_paper_pct: float | None = None

    @field_validator("device_id", mode="before")
    @classmethod
    def _strip_device(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class TelemetryOut(BaseModel):
    id: int
    device_id: str
    recorded_at: str | None = None
    cpu_pct: float | None = None
    ram_mb: float | None = None
    temperature_c: float | None = None
    fps: float | None = None
    serial_status: str | None = None
    camera_status: str | None = None
    bin_plastic_pct: float | None = None
    bin_metal_pct: float | None = None
    bin_paper_pct: float | None = None
