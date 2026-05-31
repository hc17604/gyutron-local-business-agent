from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.connectors.base import BaseConnector
from app.connectors.excel_csv_connector import import_files
from app.connectors.schemas import DATA_TYPES, ConnectorSyncResult


class LocalFolderConnector(BaseConnector):
    connector_id = "local_folder"
    name = "Local Folder"
    type = "local_folder"
    description = "Scans a local folder for CSV, XLSX, and XLS files."
    status = "available"
    auth_type = "none"
    supported_data_types = DATA_TYPES

    def test_connection(self, config: dict, auth: dict | None = None) -> dict:
        folder = resolve_allowed_folder(config.get("folder_path") or str(settings.imports_dir))
        return {"status": "connected", "message": f"Folder is readable: {folder}"}

    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        folder = resolve_allowed_folder(config.get("folder_path") or str(settings.imports_dir))
        paths = sorted(path for path in folder.iterdir() if path.suffix.lower() in {".csv", ".xlsx", ".xls"})
        return import_files(connector_id, paths, config.get("data_type", "inquiry"))


def resolve_allowed_folder(folder_path: str) -> Path:
    path = Path(folder_path).resolve()
    allowed_roots = [settings.workspace_root.resolve(), settings.data_dir.resolve()]
    if not any(path == root or root in path.parents for root in allowed_roots):
        raise HTTPException(status_code=403, detail="Folder path must be inside workspace root or data directory.")
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="Folder path is not a directory.")
    return path
