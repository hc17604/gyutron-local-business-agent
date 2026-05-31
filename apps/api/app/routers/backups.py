from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.backup.backup_service import create_backup, restore_backup
from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import require_role


router = APIRouter(prefix="/backups", tags=["backups"])


class BackupPayload(BaseModel):
    include_uploads: bool = False


class RestorePayload(BaseModel):
    backup_id: int
    confirmed: bool = False


@router.get("")
def list_backups(_: dict = Depends(require_role("owner"))):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM backup_records ORDER BY created_at DESC").fetchall()
    return {"backups": [dict(row) for row in rows]}


@router.post("/create")
def create_backup_endpoint(payload: BackupPayload, user: dict = Depends(require_role("owner"))):
    result = create_backup(include_uploads=payload.include_uploads, created_by=user["email"])
    write_audit_log("backup_created", "backup", target_id=str(result["id"]), risk_level="medium", input_summary=f"include_uploads={payload.include_uploads}")
    return result


@router.post("/restore")
def restore_backup_endpoint(payload: RestorePayload, _: dict = Depends(require_role("owner"))):
    if not payload.confirmed:
        raise HTTPException(status_code=400, detail="Restore requires confirmation.")
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM backup_records WHERE id = ?", (payload.backup_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Backup not found.")
    restore_backup(row["filename"])
    write_audit_log("backup_restored", "backup", target_id=str(payload.backup_id), risk_level="high")
    return {"status": "restored", "backup_id": payload.backup_id}


@router.delete("/{backup_id}")
def delete_backup(backup_id: int, _: dict = Depends(require_role("owner"))):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM backup_records WHERE id = ?", (backup_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Backup not found.")
        connection.execute("DELETE FROM backup_records WHERE id = ?", (backup_id,))
        connection.commit()
    write_audit_log("backup_deleted", "backup", target_id=str(backup_id), risk_level="medium")
    return {"status": "deleted"}
