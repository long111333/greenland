"""Cấu hình dev. JWT secret và device key đọc từ env / backend/.env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DB_PATH = (BACKEND_DIR / "db" / "autubin.db").resolve()
INTEGRATION_CONFIG_DIR = (PROJECT_ROOT / "integration_configs").resolve()

_DEFAULT_JWT_SECRET = "autubin-dev-secret-change-me-32bytes"
_DEFAULT_DEVICE_KEY = "edge-dev-key"


def _load_dotenv() -> None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.lower().startswith("export "):
            key = key[7:].strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_expire_seconds: int
    device_api_key: str
    db_path: Path
    integration_config_dir: Path


def get_settings() -> Settings:
    override = os.environ.get("AUTOBIN_DB_PATH", "").strip()
    db_path = Path(override).expanduser().resolve() if override else DEFAULT_DB_PATH
    try:
        expire = int(os.environ.get("JWT_EXPIRE_SECONDS", "86400"))
    except ValueError:
        expire = 86400
    if expire <= 0:
        expire = 86400
    secret = os.environ.get("JWT_SECRET", "").strip() or _DEFAULT_JWT_SECRET
    device_key = os.environ.get("DEVICE_API_KEY", "").strip() or _DEFAULT_DEVICE_KEY
    return Settings(
        jwt_secret=secret,
        jwt_expire_seconds=expire,
        device_api_key=device_key,
        db_path=db_path,
        integration_config_dir=INTEGRATION_CONFIG_DIR,
    )
