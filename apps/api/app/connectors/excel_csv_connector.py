from pathlib import Path

import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector
from app.connectors.schemas import DATA_TYPES, ConnectorSyncResult
from app.database import get_connection
from app.workspace.workspace import is_ignored


class ExcelCsvConnector(BaseConnector):
    connector_id = "excel_csv"
    name = "Excel / CSV"
    type = "excel_csv"
    description = "Imports customer-exported Excel and CSV files from local storage."
    status = "available"
    auth_type = "none"
    supported_data_types = DATA_TYPES

    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        file_path = config.get("file_path")
        if not file_path:
            return ConnectorSyncResult(summary="No file_path configured.")
        path = Path(file_path).resolve()
        return import_files(connector_id, [path], config.get("data_type", "inquiry"))


def import_files(connector_id: int, paths: list[Path], data_type: str) -> ConnectorSyncResult:
    allowed_suffixes = {".csv", ".xlsx", ".xls"}
    found = 0
    imported = 0
    imported_files: list[str] = []
    with get_connection() as connection:
        for path in paths:
            if path.suffix.lower() not in allowed_suffixes or is_ignored(path) or not path.is_file():
                continue
            found += 1
            stored_path = str(path)
            existing = connection.execute("SELECT id FROM uploads WHERE stored_path = ?", (stored_path,)).fetchone()
            if existing:
                continue
            rows = count_rows(path)
            connection.execute(
                """
                INSERT INTO uploads (data_type, original_filename, stored_path, file_size, status)
                VALUES (?, ?, ?, ?, 'imported')
                """,
                (data_type, path.name, stored_path, path.stat().st_size),
            )
            imported += rows
            imported_files.append(path.name)
        connection.commit()
    return ConnectorSyncResult(
        records_found=found,
        records_imported=imported,
        imported_files=imported_files,
        summary=f"Found {found} file(s), imported {len(imported_files)} new file(s).",
    )


def count_rows(path: Path) -> int:
    try:
        if path.suffix.lower() == ".csv":
            return len(pd.read_csv(path))
        return len(pd.read_excel(path))
    except Exception:
        return 0


def default_import_dir() -> str:
    settings.imports_dir.mkdir(parents=True, exist_ok=True)
    return str(settings.imports_dir)
