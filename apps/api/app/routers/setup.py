from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import create_session, hash_password, public_user
from app.services.model_settings import save_model_config


router = APIRouter(prefix="/setup", tags=["setup"])


class FinishSetupPayload(BaseModel):
    admin_name: str
    admin_email: str
    admin_password: str
    company_name: str = "GyuTron Demo Company"
    industry: str = "Cross-border manufacturing"
    default_language: str = "en"
    model: dict | None = None
    create_daily_report: bool = False


@router.get("/status")
def setup_status():
    with get_connection() as connection:
        setup = connection.execute("SELECT * FROM system_setup WHERE id = 1").fetchone()
        user_count = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    return {"is_initialized": bool(setup["is_initialized"]), "company_name": setup["company_name"], "user_count": user_count}


@router.post("/finish")
def finish_setup(payload: FinishSetupPayload):
    with get_connection() as connection:
        setup = connection.execute("SELECT * FROM system_setup WHERE id = 1").fetchone()
        if setup and setup["is_initialized"]:
            raise HTTPException(status_code=409, detail="System is already initialized.")
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'owner')
            """,
            (payload.admin_name, payload.admin_email.lower(), hash_password(payload.admin_password)),
        )
        user_id = cursor.lastrowid
        connection.execute(
            """
            UPDATE system_setup
            SET is_initialized = 1, company_name = ?, industry = ?, default_language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (payload.company_name, payload.industry, payload.default_language),
        )
        connection.commit()
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if payload.model and payload.model.get("provider") != "skip":
        save_model_config(payload.model)
    if payload.create_daily_report:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO automation_rules (name, description, trigger_type, schedule_cron, action_type, action_config_json)
                VALUES ('Daily Owner Report', 'Created during onboarding.', 'schedule', 'daily:09:00', 'generate_report', '{}')
                """
            )
            connection.commit()
    token = create_session(user_id)
    write_audit_log("setup_completed", "system_setup", target_id="1", risk_level="medium", input_summary=payload.company_name)
    return {"token": token, "user": public_user(dict(user))}
