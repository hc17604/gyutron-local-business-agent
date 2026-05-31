from fastapi import APIRouter, Depends

from app.database import get_connection
from app.services.auth import require_min_role


router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(_: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 200").fetchall()
    return {"audit_logs": [dict(row) for row in rows]}
