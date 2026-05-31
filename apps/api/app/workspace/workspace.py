from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.config import settings


IGNORED_NAMES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "secrets",
}
IGNORED_EXACT = {".env"}
IGNORED_PREFIXES = (".env.",)
SENSITIVE_PARTS = {("data", "db"), ("data", "uploads")}


def workspace_root() -> Path:
    return settings.workspace_root.resolve()


def to_relative(path: Path) -> str:
    return path.resolve().relative_to(workspace_root()).as_posix()


def resolve_workspace_path(relative_path: str) -> Path:
    root = workspace_root()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Path is outside workspace root.") from exc
    if is_ignored(candidate):
        raise HTTPException(status_code=403, detail="Path is ignored or sensitive.")
    return candidate


def is_ignored(path: Path) -> bool:
    root = workspace_root()
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return True
    parts = rel.parts
    if any(part in IGNORED_NAMES for part in parts):
        return True
    if path.name in IGNORED_EXACT or any(path.name.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return True
    lower_parts = tuple(part.lower() for part in parts)
    return any(all(item in lower_parts for item in sensitive) for sensitive in SENSITIVE_PARTS)


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".sqlite3"}:
        return False
    return True


def read_workspace_file(relative_path: str) -> str:
    path = resolve_workspace_path(relative_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    if not is_text_file(path):
        raise HTTPException(status_code=415, detail="Only text files can be read.")
    if path.stat().st_size > settings.workspace_file_size_limit:
        raise HTTPException(status_code=413, detail="File exceeds workspace read limit.")
    return path.read_text(encoding="utf-8", errors="replace")
