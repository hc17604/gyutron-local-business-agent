from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.database import get_connection


def create_backup(*, include_uploads: bool = False, created_by: str = "local_user") -> dict:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"gyutron-backup-{timestamp}.zip"
    target = settings.backups_dir / filename
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        if settings.database_path.exists():
            archive.write(settings.database_path, "db/gyutron.sqlite3")
        for folder, prefix in [(settings.reports_dir, "reports"), (settings.config_dir, "config")]:
            if folder.exists():
                for path in folder.rglob("*"):
                    if path.is_file():
                        archive.write(path, f"{prefix}/{path.relative_to(folder).as_posix()}")
        if include_uploads and settings.uploads_dir.exists():
            for path in settings.uploads_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, f"uploads/{path.relative_to(settings.uploads_dir).as_posix()}")
    size = target.stat().st_size
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO backup_records (filename, size, include_uploads, created_by) VALUES (?, ?, ?, ?)",
            (filename, size, int(include_uploads), created_by),
        )
        connection.commit()
    return {"id": cursor.lastrowid, "filename": filename, "size": size, "include_uploads": include_uploads}


def restore_backup(filename: str) -> None:
    source = (settings.backups_dir / filename).resolve()
    if settings.backups_dir.resolve() not in source.parents:
        raise ValueError("Backup path is outside backup directory.")
    if not source.exists():
        raise FileNotFoundError(filename)
    create_backup(include_uploads=False, created_by="pre_restore_snapshot")
    with zipfile.ZipFile(source, "r") as archive:
        tmp = settings.data_dir / ".restore_tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        archive.extractall(tmp)
        db = tmp / "db" / "gyutron.sqlite3"
        if db.exists():
            shutil.copy2(db, settings.database_path)
        reports = tmp / "reports"
        if reports.exists():
            settings.reports_dir.mkdir(parents=True, exist_ok=True)
            for path in reports.rglob("*"):
                if path.is_file():
                    dest = settings.reports_dir / path.relative_to(reports)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, dest)
        shutil.rmtree(tmp)
