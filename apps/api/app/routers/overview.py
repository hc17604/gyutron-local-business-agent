import json

from fastapi import APIRouter

from app.database import get_connection


router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("")
def get_overview():
    with get_connection() as connection:
        latest_report = connection.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT 1").fetchone()
        automations = connection.execute("SELECT * FROM automation_rules ORDER BY updated_at DESC LIMIT 5").fetchall()
        sync_jobs = connection.execute("SELECT * FROM sync_jobs ORDER BY created_at DESC LIMIT 5").fetchall()
        alerts = connection.execute("SELECT * FROM alerts WHERE status = 'open' ORDER BY created_at DESC LIMIT 5").fetchall()
    report = dict(latest_report) if latest_report else None
    if report and report.get("summary_json"):
        report["summary"] = json.loads(report["summary_json"])
    return {
        "latest_report": report,
        "active_automations": [dict(row) for row in automations],
        "recent_sync_jobs": [dict(row) for row in sync_jobs],
        "open_alerts": [dict(row) for row in alerts],
    }
