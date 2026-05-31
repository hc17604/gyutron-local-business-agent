from __future__ import annotations

import difflib
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.llm.adapter import LLMAdapter
from app.services.audit import write_audit_log
from app.services.auth import require_role
from app.services.model_settings import get_active_llm_config
from app.workspace.workspace import read_workspace_file, resolve_workspace_path


router = APIRouter(prefix="/agent", tags=["agent"])


ENGINEERING_SYSTEM_PROMPT = """You are the local engineering optimization agent for GyuTron Local Agent.
Help the user understand, optimize, and modify the current local web project. You may analyze authorized
workspace files and propose plans or diffs, but you must not write files without explicit user confirmation.
Rules:
1. Do not invent file contents.
2. Read relevant files before proposing changes.
3. Output a plan before patch details.
4. High-risk changes require confirmation.
5. Do not access files outside the workspace.
6. Do not read .env, private keys, databases, node_modules, or .git.
7. Do not execute shell commands.
8. Do not install dependencies.
9. Do not commit Git changes.
10. Do not delete files unless explicitly requested and confirmed twice.
11. Prefer small, clear changes.
12. Keep the existing UI style consistent.
13. Explain impact and rollback approach."""

BUSINESS_SYSTEM_PROMPT = """You are GyuTron Local Agent, a local-first business operations agent for
cross-border manufacturing and ecommerce teams. Answer in practical operator language for owners and managers.
Use local business rules, uploaded data summaries, reports, and memories when available. Do not claim to modify
external platforms, send email, or perform risky actions."""


class ChatContext(BaseModel):
    selected_file_ids: list[str] = []
    selected_project_paths: list[str] = []
    use_memory: bool = True
    use_business_rules: bool = True


class ChatPayload(BaseModel):
    message: str
    mode: str = "business"
    conversation_id: str | None = None
    context: ChatContext = ChatContext()


class EngineeringPlanPayload(BaseModel):
    instruction: str
    selected_paths: list[str] = []
    mode: str = "frontend_ui"


class PatchProposalPayload(BaseModel):
    instruction: str
    selected_paths: list[str] = []
    additional_context: str = ""


class ApplyPatchPayload(BaseModel):
    proposal_id: str
    confirmed: bool = False


class RollbackPayload(BaseModel):
    file_change_id: str
    confirmed: bool = False


def now_title(message: str) -> str:
    clean = " ".join(message.strip().split())
    return clean[:60] or "New conversation"


def get_conversation_messages(conversation_id: str) -> list[dict[str, str]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT role, content FROM agent_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    messages = []
    for row in rows[-12:]:
        role = row["role"]
        if role == "tool":
            continue
        messages.append({"role": "assistant" if role == "assistant" else "user", "content": row["content"]})
    return messages


def save_message(conversation_id: str, role: str, content: str, metadata: dict | None = None) -> str:
    message_id = str(uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO agent_messages (id, conversation_id, role, content, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, json.dumps(metadata or {}, ensure_ascii=False)),
        )
        connection.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
        connection.commit()
    return message_id


def ensure_conversation(payload: ChatPayload) -> str:
    if payload.conversation_id:
        return payload.conversation_id
    conversation_id = str(uuid4())
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO conversations (id, title, mode) VALUES (?, ?, ?)",
            (conversation_id, now_title(payload.message), payload.mode),
        )
        connection.commit()
    return conversation_id


def load_selected_project_context(paths: list[str]) -> tuple[list[dict], list[str]]:
    files = []
    used = []
    for path in paths[:8]:
        content = read_workspace_file(path)
        files.append({"path": path, "content": content[:12000]})
        used.append(path)
    return files, used


@router.post("/chat")
async def agent_chat(payload: ChatPayload):
    config = get_active_llm_config()
    if config is None:
        raise HTTPException(status_code=400, detail="No active model settings configured.")

    conversation_id = ensure_conversation(payload)
    save_message(conversation_id, "user", payload.message, payload.context.dict())
    project_files, project_paths = load_selected_project_context(payload.context.selected_project_paths)

    system_prompt = BUSINESS_SYSTEM_PROMPT
    if payload.mode == "engineering":
        system_prompt = ENGINEERING_SYSTEM_PROMPT
    elif payload.mode == "mixed":
        system_prompt = f"{BUSINESS_SYSTEM_PROMPT}\n\n{ENGINEERING_SYSTEM_PROMPT}"

    context_text = ""
    if project_files:
        context_text = "\n\nAuthorized project context:\n" + "\n\n".join(
            f"File: {item['path']}\n```text\n{item['content']}\n```" for item in project_files
        )
    messages = [{"role": "system", "content": system_prompt + context_text}]
    messages.extend(get_conversation_messages(conversation_id))
    messages.append({"role": "user", "content": payload.message})

    try:
        answer = await LLMAdapter(config).chat(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent model call failed: {type(exc).__name__}") from exc

    message_id = save_message(
        conversation_id,
        "assistant",
        answer,
        {"mode": payload.mode, "data_sources_used": project_paths, "tools_called": ["llm.chat"]},
    )
    write_audit_log(
        "agent_chat_message",
        "conversation",
        target_id=conversation_id,
        risk_level="low" if payload.mode == "business" else "medium",
        input_summary=f"mode={payload.mode}, message_length={len(payload.message)}",
        output_summary=f"answer_length={len(answer)}",
    )
    return {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "answer": answer,
        "mode": payload.mode,
        "tools_called": ["llm.chat"],
        "data_sources_used": project_paths,
        "suggested_actions": [],
        "requires_confirmation": False,
    }


@router.get("/conversations")
def list_conversations():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 50").fetchall()
    return {"conversations": [dict(row) for row in rows]}


@router.get("/conversations/{conversation_id}/messages")
def list_conversation_messages(conversation_id: str):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM agent_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    return {"messages": [{**dict(row), "metadata": json.loads(row["metadata_json"] or "{}")} for row in rows]}


@router.post("/engineering/plan")
def engineering_plan(payload: EngineeringPlanPayload):
    files = payload.selected_paths[:8]
    plan = [
        "Read the selected files and identify the smallest safe change.",
        "Preserve the current enterprise UI style and routing structure.",
        "Generate a patch proposal before writing any file.",
        "Apply only after user confirmation and keep rollback data.",
    ]
    write_audit_log(
        "engineering_plan_generated",
        "engineering_plan",
        risk_level="medium",
        input_summary=payload.instruction[:300],
        output_summary=f"{len(files)} files selected.",
    )
    return {
        "plan": "\n".join(f"{index + 1}. {item}" for index, item in enumerate(plan)),
        "files_to_read": files,
        "files_to_modify": files,
        "risk_level": "medium" if files else "low",
        "needs_confirmation": True,
    }


def extract_json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return json.loads(text[start : end + 1])


@router.post("/engineering/propose-patch")
async def propose_patch(payload: PatchProposalPayload):
    config = get_active_llm_config()
    if config is None:
        raise HTTPException(status_code=400, detail="No active model settings configured.")
    if not payload.selected_paths:
        raise HTTPException(status_code=400, detail="Select at least one project file before proposing a patch.")

    files, used_paths = load_selected_project_context(payload.selected_paths)
    prompt = f"""
Instruction: {payload.instruction}
Additional context: {payload.additional_context}

Return only JSON with this shape:
{{
  "summary": "short summary",
  "risk_level": "low|medium|high",
  "changes": [
    {{
      "path": "relative/path",
      "change_type": "modify",
      "after_content": "complete new file content",
      "explanation": "why this change helps"
    }}
  ]
}}
Only modify selected files. Do not delete files. Preserve existing style.

Selected files:
{json.dumps(files, ensure_ascii=False)}
"""
    try:
        raw = await LLMAdapter(config).chat(
            [{"role": "system", "content": ENGINEERING_SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.1,
        )
        parsed = extract_json_object(raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Patch proposal failed: {type(exc).__name__}") from exc

    proposal_id = str(uuid4())
    changes = []
    for change in parsed.get("changes", []):
        path = change.get("path")
        if path not in used_paths:
            continue
        before = read_workspace_file(path)
        after = change.get("after_content") or before
        diff = "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
        changes.append(
            {
                "path": path,
                "change_type": "modify",
                "diff": diff,
                "after_content": after,
                "explanation": change.get("explanation") or "",
            }
        )

    if not changes:
        raise HTTPException(status_code=422, detail="Model did not return valid changes for selected files.")

    summary = parsed.get("summary") or "Patch proposal"
    risk_level = parsed.get("risk_level") or "medium"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO patch_proposals (id, instruction, summary, changes_json, risk_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            (proposal_id, payload.instruction, summary, json.dumps(changes, ensure_ascii=False), risk_level),
        )
        connection.commit()
    write_audit_log(
        "patch_proposal_generated",
        "patch_proposal",
        target_id=proposal_id,
        risk_level=risk_level,
        input_summary=payload.instruction[:300],
        output_summary=f"{len(changes)} file changes proposed.",
    )
    public_changes = [{key: value for key, value in change.items() if key != "after_content"} for change in changes]
    return {
        "proposal_id": proposal_id,
        "summary": summary,
        "changes": public_changes,
        "risk_level": risk_level,
        "requires_confirmation": True,
    }


@router.post("/engineering/apply-patch")
def apply_patch(payload: ApplyPatchPayload, _: dict = Depends(require_role("owner"))):
    if not payload.confirmed:
        raise HTTPException(status_code=400, detail="Patch application requires confirmation.")
    with get_connection() as connection:
        proposal = connection.execute("SELECT * FROM patch_proposals WHERE id = ?", (payload.proposal_id,)).fetchone()
        if proposal is None:
            raise HTTPException(status_code=404, detail="Patch proposal not found.")
        if proposal["status"] != "proposed":
            raise HTTPException(status_code=409, detail="Patch proposal is not in proposed status.")
        changes = json.loads(proposal["changes_json"])
        applied = []
        for change in changes:
            path = resolve_workspace_path(change["path"])
            before = path.read_text(encoding="utf-8", errors="replace")
            after = change["after_content"]
            path.write_text(after, encoding="utf-8")
            change_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO file_changes (
                  id, proposal_id, file_path, change_type, before_content, after_content, diff
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (change_id, payload.proposal_id, change["path"], change["change_type"], before, after, change["diff"]),
            )
            applied.append({"file_change_id": change_id, "path": change["path"]})
        connection.execute(
            "UPDATE patch_proposals SET status = 'applied', applied_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.proposal_id,),
        )
        connection.commit()
    write_audit_log(
        "patch_applied",
        "patch_proposal",
        target_id=payload.proposal_id,
        risk_level="high",
        input_summary="User confirmed patch application.",
        output_summary=f"{len(applied)} files written.",
    )
    return {"status": "applied", "applied": applied}


@router.get("/engineering/changes")
def list_file_changes():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM file_changes ORDER BY created_at DESC LIMIT 50").fetchall()
    return {"changes": [dict(row) for row in rows]}


@router.post("/engineering/rollback")
def rollback_change(payload: RollbackPayload):
    if not payload.confirmed:
        raise HTTPException(status_code=400, detail="Rollback requires confirmation.")
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM file_changes WHERE id = ?", (payload.file_change_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="File change not found.")
        path = resolve_workspace_path(row["file_path"])
        path.write_text(row["before_content"], encoding="utf-8")
        connection.execute(
            "UPDATE file_changes SET rolled_back = 1, rolled_back_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.file_change_id,),
        )
        connection.commit()
    write_audit_log(
        "file_change_rolled_back",
        "file_change",
        target_id=payload.file_change_id,
        risk_level="high",
        input_summary="User confirmed rollback.",
        output_summary=row["file_path"],
    )
    return {"status": "rolled_back", "file_change_id": payload.file_change_id, "path": row["file_path"]}
