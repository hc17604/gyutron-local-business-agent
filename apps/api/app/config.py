from pathlib import Path
import os


def _load_dotenv_defaults() -> None:
    """Zero-dependency .env loader (repo-root .env, gitignored).

    Values already present in the process environment ALWAYS win; .env only
    fills the gaps. This makes secrets like GYUTRON_WEBSITE_API_KEY work no
    matter how the backend is launched (new/old terminal, IDE, scheduler) —
    `setx` alone only reaches processes whose parent re-read the registry.
    """
    env_file = Path(__file__).resolve().parents[3] / ".env"
    try:
        for raw_line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


_load_dotenv_defaults()


class Settings:
    service_name = "gyutron-local-agent-api"
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = Path(os.environ.get("GYUTRON_DATA_DIR", repo_root / "data"))
    workspace_root = Path(os.environ.get("GYUTRON_WORKSPACE_ROOT", repo_root)).resolve()
    uploads_dir = data_dir / "uploads"
    imports_dir = data_dir / "imports"
    reports_dir = data_dir / "reports"
    db_dir = data_dir / "db"
    backups_dir = data_dir / "backups"
    config_dir = data_dir / "config"
    database_path = db_dir / "gyutron.sqlite3"
    api_port = int(os.environ.get("GYUTRON_API_PORT", "8000"))
    web_port = int(os.environ.get("GYUTRON_WEB_PORT", "3000"))
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
