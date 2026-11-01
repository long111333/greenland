"""POST /auth/login, logout, me, profile, change-password."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.deps import get_current_user, get_db
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    OkResponse,
    ProfileUpdateRequest,
    UserOut,
)
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(row: sqlite3.Row) -> UserOut:
    keys = set(row.keys())
    return UserOut(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        role=row["role"],
        phone=row["phone"] if "phone" in keys else None,
        email=row["email"] if "email" in keys else None,
        address=row["address"] if "address" in keys else None,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> LoginResponse:
    username = body.username.strip()
    row = conn.execute(
        """
        SELECT id, username, password_hash, display_name, role, phone, email, address
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()
    hashed = row["password_hash"] if row is not None else None
    if row is None or not verify_password(body.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        user_id=row["id"],
        username=row["username"],
        role=row["role"],
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=get_settings().jwt_expire_seconds,
        user=_user_out(row),
    )


@router.post("/logout", response_model=OkResponse)
def logout(_user: Annotated[sqlite3.Row, Depends(get_current_user)]) -> OkResponse:
    return OkResponse(ok=True)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[sqlite3.Row, Depends(get_current_user)]) -> UserOut:
    return _user_out(user)


@router.put("/profile", response_model=UserOut)
def update_profile(
    body: ProfileUpdateRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    user: Annotated[sqlite3.Row, Depends(get_current_user)],
) -> UserOut:
    new_username = body.username.strip()
    if not new_username:
        raise HTTPException(status_code=400, detail="Username is required")
    clash = conn.execute(
        "SELECT id FROM users WHERE username = ? AND id != ?",
        (new_username, user["id"]),
    ).fetchone()
    if clash is not None:
        raise HTTPException(status_code=400, detail="Username already taken")
    conn.execute(
        """
        UPDATE users
        SET username = ?,
            display_name = COALESCE(?, display_name),
            phone = ?,
            email = ?,
            address = ?
        WHERE id = ?
        """,
        (
            new_username,
            body.display_name,
            (body.phone or "").strip() or None,
            (body.email or "").strip() or None,
            (body.address or "").strip() or None,
            user["id"],
        ),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT id, username, display_name, role, phone, email, address
        FROM users WHERE id = ?
        """,
        (user["id"],),
    ).fetchone()
    return _user_out(row)


@router.post("/change-password", response_model=OkResponse)
def change_password(
    body: ChangePasswordRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    user: Annotated[sqlite3.Row, Depends(get_current_user)],
) -> OkResponse:
    row = conn.execute(
        "SELECT password_hash FROM users WHERE id = ?",
        (user["id"],),
    ).fetchone()
    if row is None or not verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(body.new_password), user["id"]),
    )
    conn.commit()
    return OkResponse(ok=True)
