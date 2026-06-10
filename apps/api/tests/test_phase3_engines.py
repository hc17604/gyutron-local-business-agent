"""Phase 3 — rules engine, task engine, and reports engine tests.

Uses the same isolated tmp DB pattern as the connector tests; rows are inserted
directly into website_data (no network).
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.database import get_connection, init_database
from app.services import website_metrics as metrics
from app.services.reports_engine import generate_daily_owner_report, generate_opportunities_report, generate_weekly_pipeline_report
from app.services.rules_engine import ensure_rule_state, evaluate_rules, list_rules_with_state, set_rule_enabled
from app.services.website_leads import generate_website_leads_summary


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    for attr in ("uploads_dir", "imports_dir", "reports_dir", "backups_dir", "config_dir"):
        monkeypatch.setattr(settings, attr, data_dir / attr)
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "db_dir", data_dir / "db")
    monkeypatch.setattr(settings, "database_path", data_dir / "db" / "test.sqlite3")
    init_database()
    with get_connection() as connection:
        cursor = connection.execute("INSERT INTO data_connectors (connector_type, name) VALUES ('gyutron_website', 'GYUTRON Website')")
        connection.commit()
        connector_id = cursor.lastrowid
    return connector_id


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def insert_row(connector_id, data_type, external_id, status, created, data):
    data = {**data, "public_id": external_id, "status": status, "created_at": _iso(created)}
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO website_data (connector_id, source, data_type, external_id, status, created_at_source, data_json) VALUES (?, 'gyutron-website', ?, ?, ?, ?, ?)",
            (connector_id, data_type, external_id, status, _iso(created), json.dumps(data)),
        )
        connection.commit()


NOW = datetime.now(timezone.utc)


def seed(connector_id):
    insert_row(connector_id, "rfq", "RFQ-1", "new", NOW - timedelta(hours=30),
               {"company": "Acme", "email": "a@acme.com", "country": "Germany", "product_category": "area-scan-cameras"})
    insert_row(connector_id, "rfq", "RFQ-2", "new", NOW - timedelta(hours=2),
               {"company": "Beta", "email": "b@beta.com", "country": "France", "product_category": "vision-lighting"})
    insert_row(connector_id, "rfq", "RFQ-SPAM", "spam", NOW - timedelta(hours=1),
               {"company": "SpamCo", "email": "s@spam.com", "country": "X", "product_category": "area-scan-cameras"})
    insert_row(connector_id, "rfq", "RFQ-TEST", "new", NOW - timedelta(hours=1),
               {"company": "GYUTRON Internal Test", "email": "test@gyutron.com", "country": "HK", "product_category": "android-pda"})
    insert_row(connector_id, "support_request", "SUP-1", "new", NOW - timedelta(hours=30),
               {"company": "Acme", "email": "a@acme.com", "issue_type": "rma"})
    insert_row(connector_id, "download_request", "DL-1", "new", NOW - timedelta(hours=3),
               {"company": "Beta", "email": "b@beta.com", "requested_file": "ds-gy-a90-touch", "access_type": "manual_review"})
    insert_row(connector_id, "lead", "LEAD-1", "new", NOW - timedelta(hours=5),
               {"company": "NoMail Ltd", "email": "", "country": ""})


def test_exclusions_filter_spam_and_internal_tests(isolated_db):
    seed(isolated_db)
    records = metrics.load_records(isolated_db)
    ids = {r["id"] for r in records}
    assert "RFQ-SPAM" not in ids        # spam status excluded
    assert "RFQ-TEST" not in ids        # internal-test company excluded
    assert {"RFQ-1", "RFQ-2", "SUP-1", "DL-1", "LEAD-1"} <= ids
    # raw data stays available for audit
    raw = metrics.load_records(isolated_db, include_excluded=True)
    assert {"RFQ-SPAM", "RFQ-TEST"} <= {r["id"] for r in raw}


def test_rules_create_tasks_idempotently(isolated_db):
    seed(isolated_db)
    first = evaluate_rules(isolated_db)
    # RFQ-1, RFQ-2 (followup), SUP-1 (support), DL-1 (download), LEAD-1+RFQ-? hygiene
    assert first["tasks_created"] >= 5
    second = evaluate_rules(isolated_db)
    assert second["tasks_created"] == 0  # idempotent — nothing duplicated

    with get_connection() as connection:
        rows = connection.execute("SELECT rule_id, entity_id, priority, status FROM agent_tasks").fetchall()
    tasks = {(r["rule_id"], r["entity_id"]): r for r in rows}
    # overdue Germany RFQ → high (overdue + priority country + priority category)
    assert tasks[("rfq_followup", "RFQ-1")]["priority"] == "high"
    # fresh France RFQ, non-priority category → medium
    assert tasks[("rfq_followup", "RFQ-2")]["priority"] == "medium"
    assert ("download_review", "DL-1") in tasks
    assert ("data_hygiene", "LEAD-1") in tasks
    # spam/test rows never get tasks
    assert ("rfq_followup", "RFQ-SPAM") not in tasks
    assert ("rfq_followup", "RFQ-TEST") not in tasks


def test_tasks_auto_close_when_entity_resolves(isolated_db):
    seed(isolated_db)
    evaluate_rules(isolated_db)
    # the website admin replies to RFQ-1 → status_changed → re-sync updates local status
    with get_connection() as connection:
        connection.execute("UPDATE website_data SET status = 'quoted' WHERE external_id = 'RFQ-1'")
        connection.commit()
    result = evaluate_rules(isolated_db)
    assert result["tasks_created"] == 0
    assert result["tasks_auto_closed"] >= 1
    with get_connection() as connection:
        row = connection.execute("SELECT status FROM agent_tasks WHERE rule_id='rfq_followup' AND entity_id='RFQ-1'").fetchone()
    assert row["status"] == "done"
    # and it never re-triggers for the same entity afterwards
    again = evaluate_rules(isolated_db)
    assert again["tasks_created"] == 0


def test_rule_toggle_disables_rule(isolated_db):
    seed(isolated_db)
    ensure_rule_state()
    set_rule_enabled("data_hygiene", False)
    evaluate_rules(isolated_db)
    with get_connection() as connection:
        n = connection.execute("SELECT COUNT(*) n FROM agent_tasks WHERE rule_id='data_hygiene'").fetchone()["n"]
    assert n == 0
    rules = {r["rule_id"]: r for r in list_rules_with_state()}
    assert rules["data_hygiene"]["enabled"] is False
    assert rules["rfq_followup"]["triggered_count"] >= 1


def test_daily_and_weekly_reports_generate_bilingual(isolated_db):
    seed(isolated_db)
    evaluate_rules(isolated_db)
    daily_en = generate_daily_owner_report("en", isolated_db)
    daily_zh = generate_daily_owner_report("zh-CN", isolated_db)
    assert daily_en["title"] == "Daily Owner Report"
    assert daily_zh["title"] == "老板日报"
    weekly = generate_weekly_pipeline_report("en", isolated_db)
    opp = generate_opportunities_report("zh-CN", isolated_db)
    with get_connection() as connection:
        daily_row = connection.execute("SELECT * FROM reports WHERE id = ?", (daily_en["report_id"],)).fetchone()
        weekly_row = connection.execute("SELECT * FROM reports WHERE id = ?", (weekly["report_id"],)).fetchone()
    # report references the open tasks + overdue list
    assert "Follow up RFQ-1" in daily_row["content_markdown"]
    assert "Overdue follow-ups" in daily_row["content_markdown"]
    sj = json.loads(weekly_row["summary_json"])
    assert sj["report_type"] == "weekly_pipeline"
    assert sj["totals"]["rfq"] == 2  # spam + internal test excluded
    assert opp["report_id"]


def test_summary_v2_time_ranges(isolated_db):
    seed(isolated_db)
    all_range = generate_website_leads_summary(connector_id=isolated_db, language="en", time_range="all")
    today = generate_website_leads_summary(connector_id=isolated_db, language="en", time_range="today")
    assert all_range["structured"]["totals"]["rfq"] == 2
    assert all_range["structured"]["time_range"] == "all"
    assert today["structured"]["time_range"] == "today"
    # RFQ-2 (2h ago) counts today; RFQ-1 (30h ago) may not — totals must be <= all
    assert today["structured"]["totals"].get("rfq", 0) <= 2
