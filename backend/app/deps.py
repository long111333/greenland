"""Dependencies: kết nối SQLite, JWT bearer, device API key."""

from __future__ import annotations

import secrets
import sqlite3
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.db import get_connection
from app.security import TokenError, decode_token

_bearer = HTTPBearer(auto_error=False)


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> sqlite3.Row:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (TokenError, TypeError, ValueError) as exc:
        detail = exc.detail if isinstance(exc, TokenError) else "Invalid token"
        raise HTTPException(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    row = conn.execute(
        """
        SELECT id, username, display_name, role, phone, email, address
        FROM users WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return row


def require_device_key(
    x_device_key: Annotated[str | None, Header(alias="X-Device-Key")] = None,
) -> None:
    expected = get_settings().device_api_key
    if x_device_key is None or not secrets.compare_digest(x_device_key, expected):
        raise HTTPException(status_code=401, detail="Invalid device key")
