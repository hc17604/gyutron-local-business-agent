"""Phase 6 — health checks (fault injection), data quality, AI analyst layer."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.database import get_connection, init_database
from app.services.analyst import action_cards, executive_summary, explain_task, followup_drafts
from app.services.commerce_store import ensure_source, upsert
from app.services.customers import ensure_customers
from app.services.health import check_customer_health, data_quality_checks


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    for attr in ("uploads_dir", "imports_dir", "reports_dir", "backups_dir", "config_dir"):
        monkeypatch.setattr(settings, attr, data_dir / attr)
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "db_dir", data_dir / "db")
    monkeypatch.setattr(settings, "database_path", data_dir / "db" / "test.sqlite3")
    init_database()
    ensure_customers()
    ensure_source("gyutron-website", "GYUTRON Website", "website-api")
    ensure_source("acme-website", "ACME Website (demo)", "website-api")
    ensure_customers()
    return data_dir


def _connector(name="GW", ctype="gyutron_website", config=None):
    with get_connection() as connection:
        cur = connection.execute(
            "INSERT INTO data_connectors (connector_type, name, config_json, last_sync_at, last_sync_status) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'ok')",
            (ctype, name, json.dumps(config or {})),
        )
        cid = cur.lastrowid
        connection.execute("UPDATE data_sources SET connector_id = ? WHERE source_key = 'gyutron-website'", (cid,))
        connection.commit()
    return cid


# ---- fault injection #1: missing critical secret -> critical ----
def test_health_critical_on_missing_api_key(isolated_db, monkeypatch):
    monkeypatch.delenv("GYUTRON_WEBSITE_API_KEY", raising=False)
    _connector(config={"base_url": "http://127.0.0.1:9"})  # unreachable too
    health = check_customer_health("gyutron")
    assert health["status"] == "critical"
    kinds = {c["check"] for c in health["checks"]}
    assert "api_key_configured" in kinds and "website_reachable" in kinds
    # secrets never leaked — only presence/absence wording
    assert "GYUTRON_WEBSITE_API_KEY" in json.dumps(health)
    assert "Bearer" not in json.dumps(health)


# ---- fault injection #2: bad commerce data -> warning/critical ----
def test_health_warning_on_bad_data(isolated_db, monkeypatch):
    monkeypatch.setenv("GYUTRON_WEBSITE_API_KEY", "k")
    with get_connection() as connection:
        upsert(connection, "orders", "gyutron-website", "BAD-1",
               {"status": "paid", "total_amount": -50, "created_at_source": "2026-06-01T00:00:00Z"}, {})
        upsert(connection, "orders", "gyutron-website", "BAD-2",
               {"status": "paid", "total_amount": 100, "currency": "", "created_at_source": "2026-06-01T00:00:00Z"}, {})
        connection.commit()
    issues = {c["check"]: c for c in data_quality_checks(["gyutron-website"])}
    assert issues["order_negative_or_huge_amount"]["severity"] == "critical"
    assert "order_missing_currency" in issues


# ---- fault injection #3: stale / never-synced connector -> warning ----
def test_health_warning_on_stale_sync(isolated_db, monkeypatch):
    monkeypatch.setenv("GYUTRON_WEBSITE_API_KEY", "k")
    with get_connection() as connection:
        cur = connection.execute(
            "INSERT INTO data_connectors (connector_type, name, config_json, last_sync_at) VALUES ('gyutron_website', 'Stale', '{}', '2026-01-01 00:00:00')"
        )
        connection.execute("UPDATE data_sources SET connector_id = ? WHERE source_key = 'gyutron-website'", (cur.lastrowid,))
        connection.commit()
    health = check_customer_health("gyutron")
    assert any(c["check"] == "sync_fresh" for c in health["checks"])
    assert health["status"] in ("warning", "critical")


# ---- analyst: explanations, drafts, isolation ----
def seed_task(source, entity, rule="rfq_followup", priority="high"):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO agent_tasks (title, description, task_type, priority, status, source, entity_type, entity_id, rule_id, recommendation_text) "
            "VALUES (?, ?, 'follow_up_rfq', ?, 'open', ?, 'rfq', ?, ?, 'reply')",
            (f"Follow up {entity}", f"DemoCo · mock-cams — status new, waiting 30h.", priority, source, entity, rule),
        )
        connection.commit()


def test_action_cards_explain_and_stay_isolated(isolated_db):
    seed_task("acme-website", "ACME-RFQ-9")
    seed_task("gyutron-website", "GY-RFQ-9")
    acme_cards = action_cards("acme_demo", "en")
    gy_cards = action_cards("gyutron", "zh-CN")
    assert {c["entity_id"] for c in acme_cards} == {"ACME-RFQ-9"}   # no cross-customer leak
    assert {c["entity_id"] for c in gy_cards} == {"GY-RFQ-9"}
    card = acme_cards[0]
    assert card["what"] and card["why"] and card["action"] and card["evidence"]
    assert card["customer_id"] == "acme_demo"
    # zh explanation for the gyutron card (customer language honored by caller)
    assert "RFQ" in gy_cards[0]["what"]
    # drafts: bilingual, never auto-send
    drafts = card["drafts"]
    assert "Subject:" in drafts["email_en"] and "主题：" in drafts["email_zh"] and drafts["whatsapp"]
    assert drafts["auto_send"] is False
    assert "ACME Industrial" in drafts["email_en"]  # branded from customer config


def test_explanations_cover_three_rule_kinds(isolated_db):
    for rule in ("rfq_followup", "paid_not_fulfilled", "high_views_no_inquiry"):
        exp = explain_task({"id": 1, "rule_id": rule, "priority": "high", "description": "x", "source": "s", "entity_id": "e"}, "en")
        assert exp["what"] and exp["why"] and exp["action"]


def test_executive_summary_bilingual():
    stats = {"yesterday": {"rfq": 2}, "overdue": 1, "open_tasks": 3,
             "flags": {"surge_days": [], "abandoned_carts": [], "repeat_inquirers": [{"email": "a@b.c", "count": 2}]}}
    en = executive_summary(stats, "en")
    zh = executive_summary(stats, "zh-CN")
    assert "overdue" in en and "high-intent" in en
    assert "超时" in zh and "高意向" in zh
