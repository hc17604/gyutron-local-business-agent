import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.database import get_connection
from app.security.redaction import redact_text
from app.services.audit import write_audit_log
from app.services.auth import require_min_role


router = APIRouter(prefix="/security", tags=["security"])


class PolicyPayload(BaseModel):
    key: str
    value_json: dict


class RedactionPayload(BaseModel):
    text: str
    policy: dict | None = None


@router.get("/policies")
def list_policies(_: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM system_policies ORDER BY key ASC").fetchall()
    return {
        "local_mode": {
            "data_dir": str(settings.data_dir),
            "workspace_root": str(settings.workspace_root),
        },
        "policies": [{**dict(row), "value_json": json.loads(row["value_json"] or "{}")} for row in rows],
    }


@router.put("/policies/{key}")
def update_policy(key: str, payload: PolicyPayload, _: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO system_policies (key, value_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(payload.value_json, ensure_ascii=False)),
        )
        connection.commit()
    write_audit_log("security_policy_updated", "system_policy", target_id=key, risk_level="medium")
    return {"key": key, "value_json": payload.value_json}


@router.post("/redaction/preview")
def redaction_preview(payload: RedactionPayload):
    return {"redacted": redact_text(payload.text, payload.policy)}
