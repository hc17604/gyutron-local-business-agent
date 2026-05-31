from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import create_session, get_user_by_token, public_user, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginPayload):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (payload.email.lower(),)).fetchone()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_session(row["id"])
    write_audit_log("login", "user", target_id=str(row["id"]), risk_level="low", input_summary=payload.email.lower())
    return {"token": token, "user": public_user(dict(row))}


@router.post("/logout")
def logout(x_session_token: str | None = Header(default=None)):
    if x_session_token:
        with get_connection() as connection:
            connection.execute("DELETE FROM auth_sessions WHERE token = ?", (x_session_token,))
            connection.commit()
    write_audit_log("logout", "auth_session", risk_level="low")
    return {"status": "logged_out"}


@router.get("/me")
def me(x_session_token: str | None = Header(default=None)):
    user = get_user_by_token(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    return {"user": public_user(user)}
