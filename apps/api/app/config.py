from pathlib import Path


class Settings:
    service_name = "gyutron-local-agent-api"
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = Path(__import__("os").environ.get("GYUTRON_DATA_DIR", repo_root / "data"))
    uploads_dir = data_dir / "uploads"
    reports_dir = data_dir / "reports"
    db_dir = data_dir / "db"
    database_path = db_dir / "gyutron.sqlite3"
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()

