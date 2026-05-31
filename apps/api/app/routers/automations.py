import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.scheduler.cron import next_run_at
from app.scheduler.runner import run_automation
from app.services.audit import write_audit_log


router = APIRouter(prefix="/automations", tags=["automations"])


class AutomationPayload(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str = "manual"
    schedule_cron: str | None = None
    action_type: str = "generate_report"
    action_config_json: dict = {}
    status: str = "active"


def serialize_rule(row) -> dict:
    data = dict(row)
    data["action_config_json"] = json.loads(data["action_config_json"] or "{}")
    return data


@router.get("")
def list_automations():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM automation_rules ORDER BY updated_at DESC, id DESC").fetchall()
    return {"automations": [serialize_rule(row) for row in rows]}


@router.post("")
def create_automation(payload: AutomationPayload):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO automation_rules (
              name, description, trigger_type, schedule_cron, action_type, action_config_json, status, next_run_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.description,
                payload.trigger_type,
                payload.schedule_cron,
                payload.action_type,
                json.dumps(payload.action_config_json, ensure_ascii=False),
                payload.status,
                next_run_at(payload.schedule_cron) if payload.trigger_type == "schedule" and payload.status == "active" else None,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (cursor.lastrowid,)).fetchone()
    write_audit_log("automation_created", "automation_rule", target_id=str(row["id"]), risk_level="medium", input_summary=payload.action_type)
    return serialize_rule(row)


@router.get("/{automation_id}")
def get_automation(automation_id: int):
    row = _automation_row(automation_id)
    return serialize_rule(row)


@router.put("/{automation_id}")
def update_automation(automation_id: int, payload: AutomationPayload):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE automation_rules
            SET name = ?, description = ?, trigger_type = ?, schedule_cron = ?, action_type = ?,
                action_config_json = ?, status = ?, next_run_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.name,
                payload.description,
                payload.trigger_type,
                payload.schedule_cron,
                payload.action_type,
                json.dumps(payload.action_config_json, ensure_ascii=False),
                payload.status,
                next_run_at(payload.schedule_cron) if payload.trigger_type == "schedule" and payload.status == "active" else None,
                automation_id,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (automation_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Automation not found.")
    write_audit_log("automation_updated", "automation_rule", target_id=str(automation_id), risk_level="medium")
    return serialize_rule(row)


@router.delete("/{automation_id}")
def delete_automation(automation_id: int):
    with get_connection() as connection:
        connection.execute("DELETE FROM automation_rules WHERE id = ?", (automation_id,))
        connection.commit()
    write_audit_log("automation_deleted", "automation_rule", target_id=str(automation_id), risk_level="high")
    return {"status": "deleted"}


@router.post("/{automation_id}/run")
def run_automation_endpoint(automation_id: int):
    _automation_row(automation_id)
    return run_automation(automation_id, trigger_source="manual")


@router.post("/{automation_id}/pause")
def pause_automation(automation_id: int):
    return _set_status(automation_id, "paused", "automation_paused")


@router.post("/{automation_id}/resume")
def resume_automation(automation_id: int):
    row = _automation_row(automation_id)
    with get_connection() as connection:
        connection.execute(
            "UPDATE automation_rules SET status = 'active', next_run_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (next_run_at(row["schedule_cron"]) if row["trigger_type"] == "schedule" else None, automation_id),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (automation_id,)).fetchone()
    write_audit_log("automation_resumed", "automation_rule", target_id=str(automation_id), risk_level="medium")
    return serialize_rule(row)


@router.get("/{automation_id}/runs")
def list_automation_runs(automation_id: int):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM automation_runs WHERE automation_rule_id = ? ORDER BY created_at DESC", (automation_id,)).fetchall()
    return {"runs": [dict(row) for row in rows]}


def _automation_row(automation_id: int):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (automation_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Automation not found.")
    return row


def _set_status(automation_id: int, status: str, audit_action: str):
    with get_connection() as connection:
        connection.execute(
            "UPDATE automation_rules SET status = ?, next_run_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, automation_id),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (automation_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Automation not found.")
    write_audit_log(audit_action, "automation_rule", target_id=str(automation_id), risk_level="medium")
    return serialize_rule(row)
