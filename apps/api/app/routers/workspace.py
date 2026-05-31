from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.config import settings
from app.services.audit import write_audit_log
from app.workspace.workspace import is_ignored, is_text_file, read_workspace_file, to_relative, workspace_root


router = APIRouter(prefix="/workspace", tags=["workspace"])


class SearchPayload(BaseModel):
    query: str
    extensions: list[str] = [".tsx", ".ts", ".py", ".css", ".md"]
    limit: int = 20


class ContextPayload(BaseModel):
    paths: list[str]


def build_tree(path: Path, depth: int = 0, max_depth: int = 4) -> dict:
    node = {"name": path.name or path.as_posix(), "path": to_relative(path) if path != workspace_root() else "", "type": "directory"}
    if depth >= max_depth:
        node["children"] = []
        return node
    children = []
    for child in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if is_ignored(child):
            continue
        if child.is_dir():
            children.append(build_tree(child, depth + 1, max_depth))
        elif child.is_file() and is_text_file(child):
            children.append({"name": child.name, "path": to_relative(child), "type": "file", "size": child.stat().st_size})
    node["children"] = children[:80]
    return node


@router.get("/tree")
def get_workspace_tree():
    tree = build_tree(workspace_root())
    write_audit_log("workspace_tree_read", "workspace", input_summary="Read workspace tree.", output_summary="Tree returned.")
    return {"root": str(workspace_root()), "tree": tree}


@router.get("/file")
def get_workspace_file(path: str = Query(...)):
    content = read_workspace_file(path)
    write_audit_log(
        "workspace_file_read",
        "workspace_file",
        target_id=path,
        input_summary=f"Read file {path}",
        output_summary=f"{len(content)} characters returned.",
    )
    return {"path": path, "content": content}


@router.post("/search")
def search_workspace(payload: SearchPayload):
    root = workspace_root()
    query = payload.query.lower().strip()
    results: list[dict] = []
    extensions = {item.lower() for item in payload.extensions}
    for path in root.rglob("*"):
        if len(results) >= min(payload.limit, 50):
            break
        if is_ignored(path) or not path.is_file() or not is_text_file(path):
            continue
        if extensions and path.suffix.lower() not in extensions:
            continue
        rel = to_relative(path)
        haystack = f"{path.name} {rel}".lower()
        matched_line = ""
        if query in haystack:
            results.append({"path": rel, "match": path.name})
            continue
        if path.stat().st_size <= settings.workspace_file_size_limit:
            content = path.read_text(encoding="utf-8", errors="replace")
            for line in content.splitlines():
                if query and query in line.lower():
                    matched_line = line.strip()[:220]
                    break
            if matched_line:
                results.append({"path": rel, "match": matched_line})
    write_audit_log(
        "workspace_search",
        "workspace",
        input_summary=f"query={payload.query}",
        output_summary=f"{len(results)} results returned.",
    )
    return {"results": results}


@router.post("/context")
def get_workspace_context(payload: ContextPayload):
    selected = payload.paths[: settings.workspace_context_file_limit]
    files = [{"path": path, "content": read_workspace_file(path)} for path in selected]
    write_audit_log(
        "workspace_context_read",
        "workspace",
        risk_level="medium",
        input_summary=f"{len(selected)} files requested.",
        output_summary=f"{len(files)} files returned.",
    )
    return {"files": files}
