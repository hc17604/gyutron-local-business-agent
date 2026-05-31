import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_type TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  stored_path TEXT NOT NULL,
  file_size INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'uploaded',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS field_mappings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upload_id INTEGER,
  data_type TEXT NOT NULL,
  source_column TEXT NOT NULL,
  target_field TEXT,
  confidence REAL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'auto_mapped',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(upload_id) REFERENCES uploads(id)
);

CREATE TABLE IF NOT EXISTS business_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  data_type TEXT,
  priority INTEGER NOT NULL DEFAULT 100,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_name TEXT NOT NULL DEFAULT 'openai-compatible',
  base_url TEXT NOT NULL,
  api_key TEXT NOT NULL,
  model_name TEXT NOT NULL,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  content_markdown TEXT,
  summary_json TEXT,
  rules_snapshot_json TEXT,
  model_snapshot_json TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def ensure_local_storage() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.db_dir.mkdir(parents=True, exist_ok=True)


def init_database() -> None:
    ensure_local_storage()
    with sqlite3.connect(settings.database_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()

