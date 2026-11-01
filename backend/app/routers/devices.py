"""GET /devices và GET /devices/{device_id}."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_db
from app.queries import device_dict, require_device
from app.schemas import DeviceOut

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[DeviceOut])
def list_devices(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> list[DeviceOut]:
    rows = conn.execute(
        """
        SELECT id, name, location, status, hardware_version, created_at
        FROM devices
        ORDER BY created_at, id
        """
    ).fetchall()
    return [DeviceOut(**device_dict(row)) for row in rows]


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: str,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> DeviceOut:
    return DeviceOut(**device_dict(require_device(conn, device_id)))
