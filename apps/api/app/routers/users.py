from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import hash_password, public_user, require_min_role, require_role


router = APIRouter(prefix="/users", tags=["users"])


class UserPayload(BaseModel):
    name: str
    email: str
    password: str | None = None
    role: str = "operator"
    is_active: bool = True


@router.get("")
def list_users(_: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return {"users": [public_user(dict(row)) for row in rows]}


@router.post("")
def create_user(payload: UserPayload, _: dict = Depends(require_role("owner"))):
    if not payload.password:
        raise HTTPException(status_code=400, detail="Password is required.")
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
            (payload.name, payload.email.lower(), hash_password(payload.password), payload.role, int(payload.is_active)),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    write_audit_log("user_created", "user", target_id=str(row["id"]), risk_level="medium", input_summary=payload.email.lower())
    return public_user(dict(row))


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserPayload, _: dict = Depends(require_role("owner"))):
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET name = ?, email = ?, role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.name, payload.email.lower(), payload.role, int(payload.is_active), user_id),
        )
        if payload.password:
            connection.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(payload.password), user_id))
        connection.commit()
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found.")
    write_audit_log("user_updated", "user", target_id=str(user_id), risk_level="medium")
    return public_user(dict(row))


@router.post("/{user_id}/disable")
def disable_user(user_id: int, _: dict = Depends(require_role("owner"))):
    with get_connection() as connection:
        connection.execute("UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
        connection.commit()
    write_audit_log("user_disabled", "user", target_id=str(user_id), risk_level="medium")
    return {"status": "disabled"}


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, payload: UserPayload, _: dict = Depends(require_role("owner"))):
    if not payload.password:
        raise HTTPException(status_code=400, detail="Password is required.")
    with get_connection() as connection:
        connection.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (hash_password(payload.password), user_id))
        connection.commit()
    write_audit_log("user_password_reset", "user", target_id=str(user_id), risk_level="medium")
    return {"status": "password_reset"}
