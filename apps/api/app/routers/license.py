import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import require_min_role


router = APIRouter(prefix="/license", tags=["license"])


class LicensePayload(BaseModel):
    license_key: str
    customer_name: str
    plan: str = "standard"
    expires_at: str | None = None
    max_users: int = 5
    enabled_features: list[str] = []


@router.get("")
def get_license():
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM licenses WHERE id = 1").fetchone()
    data = dict(row)
    data["enabled_features"] = json.loads(data.pop("enabled_features_json") or "{}")
    return data


@router.post("/activate")
def activate_license(payload: LicensePayload, _: dict = Depends(require_min_role("admin"))):
    expires_at = payload.expires_at or (datetime.utcnow() + timedelta(days=365)).isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE licenses
            SET license_key = ?, customer_name = ?, plan = ?, expires_at = ?, max_users = ?,
                enabled_features_json = ?, status = 'active', updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                payload.license_key,
                payload.customer_name,
                payload.plan,
                expires_at,
                payload.max_users,
                json.dumps(payload.enabled_features, ensure_ascii=False),
            ),
        )
        connection.commit()
    write_audit_log("license_activated", "license", target_id="1", risk_level="medium", input_summary=payload.plan)
    return get_license()


@router.post("/deactivate")
def deactivate_license(_: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        connection.execute("UPDATE licenses SET status = 'deactivated', updated_at = CURRENT_TIMESTAMP WHERE id = 1")
        connection.commit()
    write_audit_log("license_deactivated", "license", target_id="1", risk_level="medium")
    return get_license()
