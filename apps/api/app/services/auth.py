from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import Header, HTTPException

from app.database import get_connection


ROLE_ORDER = {"viewer": 0, "operator": 1, "admin": 2, "owner": 3}


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hash_password(password, salt=salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, expected)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO auth_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
        connection.commit()
    return token


def get_user_by_token(token: str | None) -> dict | None:
    if not token:
        return None
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT users.* FROM auth_sessions
            JOIN users ON users.id = auth_sessions.user_id
            WHERE auth_sessions.token = ? AND users.is_active = 1
            """,
            (token,),
        ).fetchone()
    return dict(row) if row else None


def require_user(x_session_token: str | None = Header(default=None)) -> dict:
    user = get_user_by_token(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    return user


def require_role(*allowed: str):
    def dependency(x_session_token: str | None = Header(default=None)) -> dict:
        user = require_user(x_session_token)
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail=f"Role {user['role']} cannot perform this action.")
        return user

    return dependency


def require_min_role(minimum_role: str):
    def dependency(x_session_token: str | None = Header(default=None)) -> dict:
        user = require_user(x_session_token)
        if ROLE_ORDER[user["role"]] < ROLE_ORDER[minimum_role]:
            raise HTTPException(status_code=403, detail=f"Requires {minimum_role} role or higher.")
        return user

    return dependency


def public_user(user: dict) -> dict:
    data = dict(user)
    data.pop("password_hash", None)
    return data
