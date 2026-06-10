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

CREATE TABLE IF NOT EXISTS data_connectors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connector_type TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  config_json TEXT NOT NULL DEFAULT '{}',
  auth_json TEXT NOT NULL DEFAULT '{}',
  last_sync_at TEXT,
  last_sync_status TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connector_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  sync_type TEXT NOT NULL DEFAULT 'manual',
  records_found INTEGER NOT NULL DEFAULT 0,
  records_imported INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(connector_id) REFERENCES data_connectors(id)
);

CREATE TABLE IF NOT EXISTS website_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connector_id INTEGER NOT NULL,
  source TEXT NOT NULL DEFAULT 'gyutron-website',
  data_type TEXT NOT NULL,
  external_id TEXT NOT NULL,
  status TEXT,
  created_at_source TEXT,
  data_json TEXT NOT NULL DEFAULT '{}',
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(connector_id, data_type, external_id),
  FOREIGN KEY(connector_id) REFERENCES data_connectors(id)
);

CREATE TABLE IF NOT EXISTS connector_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connector_id INTEGER NOT NULL,
  state_key TEXT NOT NULL,
  state_value TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(connector_id, state_key),
  FOREIGN KEY(connector_id) REFERENCES data_connectors(id)
);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  task_type TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'open',
  source TEXT NOT NULL DEFAULT 'gyutron-website',
  entity_type TEXT,
  entity_id TEXT,
  rule_id TEXT,
  recommendation_text TEXT,
  due_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(rule_id, entity_id)
);

CREATE TABLE IF NOT EXISTS rule_state (
  rule_id TEXT PRIMARY KEY,
  enabled INTEGER NOT NULL DEFAULT 1,
  config_json TEXT NOT NULL DEFAULT '{}',
  last_triggered_at TEXT,
  triggered_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_triggers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_id TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  output_type TEXT NOT NULL DEFAULT 'task',
  output_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================ Phase 4: commerce ============================ --
-- Registry of every data source feeding the workspace (website API, shop
-- behavior events, CSV commerce imports, future SaaS). Source filters in
-- reports/tasks/dashboard key off THIS table, not ad-hoc strings.
CREATE TABLE IF NOT EXISTS data_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  kind TEXT NOT NULL,
  connector_id INTEGER,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Unified commerce model. Every table: (source, external_id) unique, SANITIZED
-- raw_payload (see services/commerce_sanitize.py), schema_version, base-currency
-- triple, canonical status + raw_status, UTC source timestamps. GDPR path:
-- cascade delete by (source, external_id).
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  order_number TEXT,
  customer_external_id TEXT,
  customer_email TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  raw_status TEXT,
  total_amount REAL,
  currency TEXT,
  amount_base REAL,
  item_count INTEGER,
  country TEXT,
  created_at_source TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  order_external_id TEXT,
  product_external_id TEXT,
  sku TEXT,
  title TEXT,
  quantity INTEGER,
  unit_amount REAL,
  currency TEXT,
  amount_base REAL,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  email TEXT,
  name TEXT,
  company TEXT,
  country TEXT,
  first_seen_at TEXT,
  last_seen_at TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS commerce_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  sku TEXT,
  title TEXT,
  category TEXT,
  price_amount REAL,
  currency TEXT,
  amount_base REAL,
  status TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  order_ref TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  raw_status TEXT,
  amount REAL,
  currency TEXT,
  amount_base REAL,
  method TEXT,
  created_at_source TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS shipments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  order_ref TEXT,
  status TEXT,
  raw_status TEXT,
  carrier TEXT,
  tracking_ref TEXT,
  country TEXT,
  created_at_source TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

-- Shop BEHAVIOR events (product.viewed / cart.added / quote.requested) — this is
-- a behavior-events feed, NOT an order connector. Anonymous by design: no IP,
-- no fingerprint, no session id, no PII.
CREATE TABLE IF NOT EXISTS cart_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  product_handle TEXT,
  locale TEXT,
  occurred_at TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

-- Placeholders (schema only in Phase 4).
CREATE TABLE IF NOT EXISTS refunds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  order_ref TEXT,
  status TEXT,
  amount REAL,
  currency TEXT,
  amount_base REAL,
  created_at_source TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  sku TEXT,
  quantity INTEGER,
  snapshot_at TEXT,
  raw_payload TEXT NOT NULL DEFAULT '{}',
  schema_version INTEGER NOT NULL DEFAULT 1,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS automation_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  trigger_type TEXT NOT NULL DEFAULT 'manual',
  schedule_cron TEXT,
  action_type TEXT NOT NULL,
  action_config_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active',
  last_run_at TEXT,
  next_run_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automation_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  automation_rule_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  trigger_source TEXT NOT NULL DEFAULT 'manual',
  result_summary TEXT,
  result_json TEXT NOT NULL DEFAULT '{}',
  error_message TEXT,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(automation_rule_id) REFERENCES automation_rules(id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'open',
  source_type TEXT,
  source_id TEXT,
  related_report_id INTEGER,
  related_task_id INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_setup (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  is_initialized INTEGER NOT NULL DEFAULT 0,
  company_name TEXT,
  industry TEXT,
  default_language TEXT NOT NULL DEFAULT 'en',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'owner',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS system_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL UNIQUE,
  value_json TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  size INTEGER NOT NULL DEFAULT 0,
  include_uploads INTEGER NOT NULL DEFAULT 0,
  created_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'ready'
);

CREATE TABLE IF NOT EXISTS licenses (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  license_key TEXT,
  customer_name TEXT,
  plan TEXT NOT NULL DEFAULT 'trial',
  expires_at TEXT,
  max_users INTEGER NOT NULL DEFAULT 3,
  enabled_features_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'trial',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def ensure_local_storage() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.imports_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.db_dir.mkdir(parents=True, exist_ok=True)
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)


def init_database() -> None:
    ensure_local_storage()
    with sqlite3.connect(settings.database_path) as connection:
        connection.executescript(SCHEMA)
        _migrate_llm_configs(connection)
        _seed_singletons(connection)
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


def _seed_singletons(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT OR IGNORE INTO system_setup (id, is_initialized) VALUES (1, 0)")
    connection.execute(
        """
        INSERT OR IGNORE INTO licenses (
          id, plan, status, expires_at, enabled_features_json
        ) VALUES (1, 'trial', 'trial', datetime('now', '+14 days'), '{"core": true}')
        """
    )
    default_policies = {
        "model_data_policy": {
            "allow_send_business_data_to_llm": False,
            "allow_send_raw_rows_to_llm": False,
            "max_rows_sent_to_llm": 20,
            "mask_customer_email": True,
            "mask_phone_number": True,
            "mask_amount": False,
            "mask_customer_name": False,
        },
        "engineering_agent_policy": {
            "allow_file_read": True,
            "allow_patch_proposal": True,
            "allow_patch_apply": True,
            "require_owner_confirmation": True,
            "blocked_paths": [".env", ".git", "node_modules", "data/db", "data/uploads"],
        },
        "automation_policy": {
            "enable_scheduler": True,
            "allow_scheduled_reports": True,
            "allow_connector_sync": True,
            "allow_external_actions": False,
        },
        "audit_settings": {
            "audit_retention_days": 180,
            "log_tool_calls": True,
            "log_file_reads": True,
            "log_model_calls_summary": True,
        },
    }
    for key, value in default_policies.items():
        connection.execute(
            "INSERT OR IGNORE INTO system_policies (key, value_json) VALUES (?, ?)",
            (key, __import__("json").dumps(value)),
        )
