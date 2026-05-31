import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.connectors.registry import get_connector, list_manifests
from app.database import get_connection
from app.services.audit import write_audit_log


router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorPayload(BaseModel):
    connector_type: str
    name: str
    description: str | None = None
    status: str = "active"
    config_json: dict = {}
    auth_json: dict = {}


def serialize_connector(row) -> dict:
    data = dict(row)
    data["config_json"] = json.loads(data["config_json"] or "{}")
    data["auth_json"] = {}
    return data


@router.get("/catalog")
def connector_catalog():
    return {"connectors": list_manifests()}


@router.get("")
def list_connectors():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM data_connectors ORDER BY updated_at DESC, id DESC").fetchall()
    return {"connectors": [serialize_connector(row) for row in rows], "catalog": list_manifests()}


@router.post("")
def create_connector(payload: ConnectorPayload):
    try:
        get_connector(payload.connector_type)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO data_connectors (connector_type, name, description, status, config_json, auth_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.connector_type,
                payload.name,
                payload.description,
                payload.status,
                json.dumps(payload.config_json, ensure_ascii=False),
                json.dumps(payload.auth_json, ensure_ascii=False),
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM data_connectors WHERE id = ?", (cursor.lastrowid,)).fetchone()
    write_audit_log("connector_created", "data_connector", target_id=str(row["id"]), risk_level="medium", input_summary=payload.connector_type)
    return serialize_connector(row)


@router.post("/local-folder/scan")
def scan_first_local_folder():
    with get_connection() as connection:
        row = connection.execute("SELECT id FROM data_connectors WHERE connector_type = 'local_folder' ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No local folder connector configured.")
    return sync_connector(row["id"])


@router.get("/{connector_id}")
def get_data_connector(connector_id: int):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM data_connectors WHERE id = ?", (connector_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found.")
    return serialize_connector(row)


@router.put("/{connector_id}")
def update_connector(connector_id: int, payload: ConnectorPayload):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE data_connectors
            SET connector_type = ?, name = ?, description = ?, status = ?, config_json = ?,
                auth_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.connector_type,
                payload.name,
                payload.description,
                payload.status,
                json.dumps(payload.config_json, ensure_ascii=False),
                json.dumps(payload.auth_json, ensure_ascii=False),
                connector_id,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM data_connectors WHERE id = ?", (connector_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found.")
    write_audit_log("connector_updated", "data_connector", target_id=str(connector_id), risk_level="medium", input_summary=payload.connector_type)
    return serialize_connector(row)


@router.delete("/{connector_id}")
def delete_connector(connector_id: int):
    with get_connection() as connection:
        connection.execute("DELETE FROM data_connectors WHERE id = ?", (connector_id,))
        connection.commit()
    write_audit_log("connector_deleted", "data_connector", target_id=str(connector_id), risk_level="high")
    return {"status": "deleted"}


@router.post("/{connector_id}/test")
def test_connector(connector_id: int):
    connector_row = _connector_row(connector_id)
    connector = get_connector(connector_row["connector_type"])
    result = connector.test_connection(json.loads(connector_row["config_json"] or "{}"), {})
    write_audit_log("connector_tested", "data_connector", target_id=str(connector_id), input_summary=connector_row["connector_type"], output_summary=result["status"])
    return result


@router.post("/{connector_id}/sync")
def sync_connector(connector_id: int, sync_type: str = "manual"):
    connector_row = _connector_row(connector_id)
    connector = get_connector(connector_row["connector_type"])
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO sync_jobs (connector_id, status, sync_type, started_at) VALUES (?, 'running', ?, CURRENT_TIMESTAMP)",
            (connector_id, sync_type),
        )
        sync_job_id = cursor.lastrowid
        connection.commit()
    try:
        result = connector.sync(connector_id, json.loads(connector_row["config_json"] or "{}"), {}, sync_type=sync_type)
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE sync_jobs
                SET status = 'completed', records_found = ?, records_imported = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (result.records_found, result.records_imported, sync_job_id),
            )
            connection.execute(
                "UPDATE data_connectors SET last_sync_at = CURRENT_TIMESTAMP, last_sync_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (result.summary, connector_id),
            )
            connection.commit()
        status = "completed"
    except Exception as exc:
        with get_connection() as connection:
            connection.execute(
                "UPDATE sync_jobs SET status = 'failed', error_message = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (type(exc).__name__, sync_job_id),
            )
            connection.execute(
                "UPDATE data_connectors SET status = 'error', last_sync_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (type(exc).__name__, connector_id),
            )
            connection.commit()
        raise
    write_audit_log(
        "connector_synced",
        "data_connector",
        target_id=str(connector_id),
        risk_level="medium",
        input_summary=f"sync_type={sync_type}",
        output_summary=f"{status}: {result.summary}",
    )
    return {"sync_job_id": sync_job_id, "status": status, **result.dict()}


@router.get("/{connector_id}/sync-jobs")
def list_sync_jobs(connector_id: int):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM sync_jobs WHERE connector_id = ? ORDER BY created_at DESC", (connector_id,)).fetchall()
    return {"sync_jobs": [dict(row) for row in rows]}


def _connector_row(connector_id: int):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM data_connectors WHERE id = ?", (connector_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found.")
    return row
