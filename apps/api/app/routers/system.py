import shutil

from fastapi import APIRouter

from app.config import settings
from app.database import get_connection


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def system_health():
    disk = shutil.disk_usage(settings.data_dir)
    with get_connection() as connection:
        db_ok = connection.execute("SELECT 1 AS ok").fetchone()["ok"] == 1
        last_backup = connection.execute("SELECT * FROM backup_records ORDER BY created_at DESC LIMIT 1").fetchone()
        last_sync = connection.execute("SELECT * FROM sync_jobs ORDER BY created_at DESC LIMIT 1").fetchone()
        active_automations = connection.execute("SELECT COUNT(*) AS count FROM automation_rules WHERE status = 'active'").fetchone()["count"]
        recent_errors = connection.execute(
            "SELECT * FROM audit_logs WHERE risk_level IN ('high', 'error') ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
    return {
        "backend": "ok",
        "frontend": "served_by_vite_or_container",
        "database": "ok" if db_ok else "error",
        "scheduler": "enabled",
        "last_backup": dict(last_backup) if last_backup else None,
        "last_sync": dict(last_sync) if last_sync else None,
        "disk_usage": {"total": disk.total, "used": disk.used, "free": disk.free},
        "active_automations": active_automations,
        "recent_errors": [dict(row) for row in recent_errors],
    }


@router.get("/info")
def system_info():
    return {
        "service": settings.service_name,
        "data_dir": str(settings.data_dir),
        "database_path": str(settings.database_path),
        "workspace_root": str(settings.workspace_root),
        "api_port": settings.api_port,
        "web_port": settings.web_port,
    }
