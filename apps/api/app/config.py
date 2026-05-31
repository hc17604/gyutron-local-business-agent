from pathlib import Path
import os


class Settings:
    service_name = "gyutron-local-agent-api"
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = Path(os.environ.get("GYUTRON_DATA_DIR", repo_root / "data"))
    workspace_root = Path(os.environ.get("GYUTRON_WORKSPACE_ROOT", repo_root)).resolve()
    uploads_dir = data_dir / "uploads"
    imports_dir = data_dir / "imports"
    reports_dir = data_dir / "reports"
    db_dir = data_dir / "db"
    database_path = db_dir / "gyutron.sqlite3"
    workspace_file_size_limit = 200 * 1024
    workspace_context_file_limit = 20
    llm_timeout_seconds = 45
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
