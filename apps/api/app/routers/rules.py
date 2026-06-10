"""Business Rules v1 — list rules with runtime state, toggle, inspect triggers."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.services.auth import require_min_role
from app.services.rules_engine import list_rules_with_state, set_rule_enabled


router = APIRouter(prefix="/business-rules", tags=["business-rules"])


class RuleToggle(BaseModel):
    enabled: bool


@router.get("")
def list_rules():
    return {"rules": list_rules_with_state()}


@router.post("/{rule_id}/toggle")
def toggle_rule(rule_id: str, payload: RuleToggle, _: dict = Depends(require_min_role("admin"))):
    try:
        set_rule_enabled(rule_id, payload.enabled)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"rule_id": rule_id, "enabled": payload.enabled}


@router.get("/{rule_id}/triggers")
def rule_triggers(rule_id: str, limit: int = 50):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM rule_triggers WHERE rule_id = ? ORDER BY id DESC LIMIT ?",
            (rule_id, max(1, min(limit, 200))),
        ).fetchall()
    return {"triggers": [dict(r) for r in rows]}
