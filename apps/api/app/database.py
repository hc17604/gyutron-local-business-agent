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
  provider TEXT NOT NULL DEFAULT 'openai_compatible',
  provider_name TEXT NOT NULL DEFAULT 'openai_compatible',
  display_name TEXT NOT NULL DEFAULT 'OpenAI-compatible',
  base_url TEXT NOT NULL,
  api_key TEXT NOT NULL,
  model_name TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 0,
  is_default INTEGER NOT NULL DEFAULT 0,
  supports_streaming INTEGER NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  mode TEXT NOT NULL DEFAULT 'business',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS patch_proposals (
  id TEXT PRIMARY KEY,
  instruction TEXT NOT NULL,
  summary TEXT NOT NULL,
  changes_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  risk_level TEXT NOT NULL DEFAULT 'medium',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  applied_at TEXT
);

CREATE TABLE IF NOT EXISTS file_changes (
  id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  file_path TEXT NOT NULL,
  change_type TEXT NOT NULL,
  before_content TEXT NOT NULL,
  after_content TEXT NOT NULL,
  diff TEXT NOT NULL,
  rolled_back INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  rolled_back_at TEXT,
  FOREIGN KEY(proposal_id) REFERENCES patch_proposals(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL DEFAULT 'local_user',
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  risk_level TEXT NOT NULL DEFAULT 'low',
  input_summary TEXT,
  output_summary TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        _migrate_llm_configs(connection)
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def _migrate_llm_configs(connection: sqlite3.Connection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info(llm_configs)").fetchall()}
    columns = {
        "provider": "TEXT NOT NULL DEFAULT 'openai_compatible'",
        "display_name": "TEXT NOT NULL DEFAULT 'OpenAI-compatible'",
        "is_active": "INTEGER NOT NULL DEFAULT 0",
        "supports_streaming": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, definition in columns.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE llm_configs ADD COLUMN {column} {definition}")
