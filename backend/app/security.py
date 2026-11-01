"""JWT (PyJWT / HS256) và bcrypt qua passlib — cùng cách seed DB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
_BURN_HASH: str | None = None


class TokenError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def hash_password(plain: str) -> str:
    return PWD_CONTEXT.hash(plain)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or not str(hashed).startswith("$2"):
        _burn(plain)
        return False
    try:
        return PWD_CONTEXT.verify(plain, hashed)
    except Exception:
        return False


def _burn(plain: str) -> None:
    """Giữ chi phí bcrypt khi user không tồn tại hoặc hash không phải bcrypt."""
    global _BURN_HASH
    try:
        if _BURN_HASH is None:
            _BURN_HASH = PWD_CONTEXT.hash("autubin-not-a-real-password")
        PWD_CONTEXT.verify(plain, _BURN_HASH)
    except Exception:
        return


def create_access_token(*, user_id: int, username: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_expire_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc
    if not isinstance(payload, dict) or payload.get("sub") is None:
        raise TokenError("Invalid token")
    return payload
