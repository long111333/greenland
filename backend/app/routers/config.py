"""GET /config/hardware|ai|orchestrator — đọc integration_configs/."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])

_FILES = {
    "hardware": "hardware_config.json",
    "ai": "ai_config.json",
    "orchestrator": "orchestrator_config.json",
}


def _read(name: str) -> dict:
    path = get_settings().integration_config_dir / _FILES[name]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Config not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Config file is not valid JSON") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Config file is not a JSON object")
    return data


@router.get("/hardware")
def hardware_config() -> dict:
    return _read("hardware")


@router.get("/ai")
def ai_config() -> dict:
    return _read("ai")


@router.get("/orchestrator")
def orchestrator_config() -> dict:
    return _read("orchestrator")
