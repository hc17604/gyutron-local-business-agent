"""Phase 4 — commerce model, CSV connector, sanitizer, cross-source metrics."""
import json

import pytest

from app.config import settings
from app.connectors.csv_commerce_connector import CsvCommerceConnector
from app.database import get_connection, init_database
from app.services.commerce_metrics import commerce_summary, paid_not_fulfilled, revenue_reconciliation
from app.services.commerce_sanitize import sanitize_payload
from app.services.commerce_store import canonical_order_status, delete_entity, list_sources
from app.services.rules_engine import evaluate_rules


SAMPLES = settings.repo_root / "samples" / "acme-industrial"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    for attr in ("uploads_dir", "imports_dir", "reports_dir", "backups_dir", "config_dir"):
        monkeypatch.setattr(settings, attr, data_dir / attr)
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "db_dir", data_dir / "db")
    monkeypatch.setattr(settings, "database_path", data_dir / "db" / "test.sqlite3")
    init_database()
    return data_dir


ACME_CONFIG = {"source_key": "acme-industrial-csv", "display_name": "ACME Industrial (CSV, mock)", "folder_path": str(SAMPLES), "mapping": "generic"}


def test_sanitizer_strips_sensitive_fields():
    dirty = {
        "card_number": "4111 1111 1111 1111",
        "shipping_address1": "1 Secret Street",
        "phone": "+86 13800000000",
        "access_token": "abc",
        "note": "pay with 4111111111111111 please",
        "api_key_value": "x" * 50,
        "email": "ok@example.com",
        "nested": {"cvv": "123", "country": "Germany"},
    }
    clean = sanitize_payload(dirty)
    assert "card_number" not in clean and "shipping_address1" not in clean
    assert "phone" not in clean and "access_token" not in clean and "api_key_value" not in clean
    assert "[redacted-number]" in clean["note"]
    assert clean["email"] == "ok@example.com"
    assert clean["nested"] == {"country": "Germany"}


def test_csv_import_idempotent_and_isolated(isolated_db):
    connector = CsvCommerceConnector()
    assert connector.test_connection(ACME_CONFIG)["status"] == "connected"
    first = connector.sync(1, ACME_CONFIG)
    assert first.records_imported == first.records_found == 16  # 4+6+3+3 rows

    with get_connection() as connection:
        n1 = connection.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"]
    second = connector.sync(1, ACME_CONFIG)  # re-import: no duplicates
    with get_connection() as connection:
        n2 = connection.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"]
        sample = connection.execute("SELECT * FROM orders WHERE external_id = 'ACME-1001'").fetchone()
    assert n1 == n2 == 4
    assert second.records_imported == 16
    # canonical status + base currency + sanitized payload
    assert sample["status"] == "paid"
    assert sample["amount_base"] == 2450.0
    assert "email" in json.loads(sample["raw_payload"])
    # source registry + isolation
    assert any(s["source_key"] == "acme-industrial-csv" for s in list_sources())
    assert commerce_summary(source="gyutron-shop")["orders"] == 0  # no cross-pollution


def test_no_revenue_double_count(isolated_db):
    connector = CsvCommerceConnector()
    connector.sync(1, ACME_CONFIG)
    summary = commerce_summary(source="acme-industrial-csv")
    # revenue = paid/fulfilled ORDERS only: 2450(USD) + 890.5 EUR*1.08 + 1300(USD); pending 5120 excluded
    assert summary["orders"] == 4
    assert summary["revenue_base"] == round(2450 + 890.5 * 1.08 + 1300, 2)
    rec = revenue_reconciliation(source="acme-industrial-csv")
    assert rec["paid_payments"] == 3 and rec["matched_to_orders"] == 3 and rec["unmatched"] == 0


def test_paid_not_fulfilled_rule_creates_task(isolated_db):
    connector = CsvCommerceConnector()
    connector.sync(1, ACME_CONFIG)
    stale = paid_not_fulfilled(threshold_days=0)  # accelerated threshold for the test
    assert {o["external_id"] for o in stale} == {"ACME-1001", "ACME-1004"}  # paid, not fulfilled
    from app.services.rules_engine import rule_runtime, ensure_rule_state
    ensure_rule_state()
    with get_connection() as connection:
        connection.execute("UPDATE rule_state SET config_json = '{\"threshold_days\": 0}' WHERE rule_id = 'paid_not_fulfilled'")
        connection.commit()
    result = evaluate_rules()
    with get_connection() as connection:
        tasks = connection.execute("SELECT entity_id FROM agent_tasks WHERE rule_id = 'paid_not_fulfilled'").fetchall()
    assert {t["entity_id"] for t in tasks} == {"acme-industrial-csv:ACME-1001", "acme-industrial-csv:ACME-1004"}
    again = evaluate_rules()
    assert again["tasks_created"] == 0  # idempotent


def test_gdpr_cascade_delete(isolated_db):
    connector = CsvCommerceConnector()
    connector.sync(1, ACME_CONFIG)
    deleted = delete_entity("acme-industrial-csv", "ACME-1001")
    assert deleted >= 1
    with get_connection() as connection:
        gone = connection.execute("SELECT COUNT(*) n FROM orders WHERE external_id='ACME-1001'").fetchone()["n"]
    assert gone == 0


def test_bad_rows_skipped_not_fatal(isolated_db, tmp_path):
    folder = tmp_path / "data" / "badcsv"
    folder.mkdir(parents=True)
    (folder / "orders.csv").write_text(
        "order_id,order_number,customer_id,email,status,total,currency,items,country,created_at\n"
        "OK-1,#1,C1,a@b.com,paid,100,USD,1,DE,2026-06-01\n"
        ",#2,C2,b@b.com,paid,200,USD,1,DE,2026-06-01\n"          # missing external id
        "OK-3,#3,C3,c@b.com,paid,notanumber,USD,1,DE,2026-06-01\n",  # bad float
        encoding="utf-8",
    )
    connector = CsvCommerceConnector()
    result = connector.sync(1, {"source_key": "bad-csv-test", "folder_path": str(folder), "mapping": "generic"})
    assert result.records_found == 3 and result.records_imported == 1
    assert "skipped 2" in result.summary and ":3 " in result.summary  # line numbers reported
