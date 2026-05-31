from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.services.audit import write_audit_log


router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertPayload(BaseModel):
    title: str
    description: str
    severity: str = "medium"
    status: str = "open"
    source_type: str | None = None
    source_id: str | None = None
    related_report_id: int | None = None
    related_task_id: int | None = None


@router.get("")
def list_alerts():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 100").fetchall()
    return {"alerts": [dict(row) for row in rows]}


@router.post("")
def create_alert(payload: AlertPayload):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (
              title, description, severity, status, source_type, source_id, related_report_id, related_task_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.description,
                payload.severity,
                payload.status,
                payload.source_type,
                payload.source_id,
                payload.related_report_id,
                payload.related_task_id,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM alerts WHERE id = ?", (cursor.lastrowid,)).fetchone()
    write_audit_log("alert_created", "alert", target_id=str(row["id"]), risk_level="low", input_summary=payload.title)
    return dict(row)


@router.put("/{alert_id}")
def update_alert(alert_id: int, payload: AlertPayload):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE alerts
            SET title = ?, description = ?, severity = ?, status = ?, source_type = ?, source_id = ?,
                related_report_id = ?, related_task_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.title,
                payload.description,
                payload.severity,
                payload.status,
                payload.source_type,
                payload.source_id,
                payload.related_report_id,
                payload.related_task_id,
                alert_id,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found.")
    write_audit_log("alert_updated", "alert", target_id=str(alert_id), risk_level="low")
    return dict(row)


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    return _set_alert_status(alert_id, "acknowledged", "alert_acknowledged")


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    return _set_alert_status(alert_id, "resolved", "alert_resolved")


def _set_alert_status(alert_id: int, status: str, audit_action: str):
    with get_connection() as connection:
        connection.execute("UPDATE alerts SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, alert_id))
        connection.commit()
        row = connection.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found.")
    write_audit_log(audit_action, "alert", target_id=str(alert_id), risk_level="low")
    return dict(row)
