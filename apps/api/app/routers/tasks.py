"""Agent tasks — rule-generated follow-up work items (Phase 3 Task Engine v1)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import require_min_role
from app.services.rules_engine import evaluate_rules


router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = ("open", "in_progress", "done", "dismissed")


class TaskPatch(BaseModel):
    status: str


@router.get("")
def list_tasks(status: str | None = None, priority: str | None = None, task_type: str | None = None, limit: int = 200):
    query = "SELECT * FROM agent_tasks"
    clauses, params = [], []
    if status:
        clauses.append("status = ?"); params.append(status)
    if priority:
        clauses.append("priority = ?"); params.append(priority)
    if task_type:
        clauses.append("task_type = ?"); params.append(task_type)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, id DESC LIMIT ?"
    params.append(max(1, min(limit, 500)))
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
        counts = connection.execute("SELECT status, COUNT(*) n FROM agent_tasks GROUP BY status").fetchall()
    return {"tasks": [dict(r) for r in rows], "counts": {r["status"]: r["n"] for r in counts}}


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskPatch, _: dict = Depends(require_min_role("operator"))):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE agent_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.status, task_id),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,)).fetchone()
    if cursor.rowcount == 0 or row is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    write_audit_log("task_updated", "agent_task", target_id=str(task_id), risk_level="low", output_summary=payload.status)
    return dict(row)


@router.post("/evaluate")
def evaluate_now(_: dict = Depends(require_min_role("operator"))):
    """Manually run the rules engine (also runs after every connector sync)."""
    return evaluate_rules()
