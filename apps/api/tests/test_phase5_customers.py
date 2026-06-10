"""Phase 5 — customer isolation, demo guard, per-customer thresholds."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.database import get_connection, init_database
from app.services import website_metrics as metrics
from app.services.commerce_metrics import commerce_summary
from app.services.commerce_store import ensure_source, upsert
from app.services.customers import (
    customer_sources, ensure_customers, get_customer, list_customers, reset_demo_customer,
)
from app.services.reports_engine import generate_daily_owner_report
from app.services.rules_engine import evaluate_rules, rule_runtime


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
    # register the sources both customers own
    ensure_source("gyutron-website", "GYUTRON Website", "website-api")
    ensure_source("acme-website", "ACME Website (demo)", "website-api")
    ensure_source("acme-industrial-csv", "ACME CSV (mock)", "csv-commerce")
    ensure_customers()  # bind ownership now that sources exist
    return data_dir


NOW = datetime.now(timezone.utc)


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def seed_two_customers(connector_gy=1, connector_acme=2):
    rows = [
        (connector_gy, "gyutron-website", "rfq", "GY-RFQ-1", "new", {"company": "RealCo", "email": "r@real.com", "country": "Germany", "product_category": "area-scan-cameras"}),
        (connector_acme, "acme-website", "rfq", "ACME-RFQ-1", "new", {"company": "DemoCo", "email": "d@demo.com", "country": "Malaysia", "product_category": "mock-cams"}),
    ]
    with get_connection() as connection:
        for cid, source, dtype, ext, status, data in rows:
            data = {**data, "public_id": ext, "status": status, "created_at": _iso(NOW - timedelta(hours=30))}
            connection.execute(
                "INSERT INTO website_data (connector_id, source, data_type, external_id, status, created_at_source, data_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cid, source, dtype, ext, status, data["created_at"], json.dumps(data)),
            )
        # ACME commerce order (mock)
        upsert(connection, "orders", "acme-industrial-csv", "ACME-9001",
               {"status": "paid", "raw_status": "paid", "total_amount": 100.0, "currency": "USD", "amount_base": 100.0,
                "created_at_source": _iso(NOW - timedelta(days=1))}, {"note": "mock"})
        connection.commit()


def test_customer_source_resolution(isolated_db):
    assert set(customer_sources("gyutron")) >= {"gyutron-website"}
    assert set(customer_sources("acme_demo")) >= {"acme-website", "acme-industrial-csv"}
    assert customer_sources(None) is None
    assert customer_sources("unknown_x") == ["__none__"]  # unknown → match nothing


def test_records_and_commerce_isolated_by_customer(isolated_db):
    seed_two_customers()
    gy = metrics.load_records(sources=customer_sources("gyutron"))
    acme = metrics.load_records(sources=customer_sources("acme_demo"))
    assert {r["id"] for r in gy} == {"GY-RFQ-1"}
    assert {r["id"] for r in acme} == {"ACME-RFQ-1"}
    # commerce: ACME order never appears under gyutron
    assert commerce_summary(sources=customer_sources("gyutron"))["orders"] == 0
    assert commerce_summary(sources=customer_sources("acme_demo"))["orders"] == 1


def test_tasks_and_reports_carry_customer_context(isolated_db):
    seed_two_customers()
    result = evaluate_rules(customer_id="acme_demo")
    assert result["tasks_created"] >= 1
    with get_connection() as connection:
        rows = connection.execute("SELECT entity_id, source FROM agent_tasks WHERE rule_id='rfq_followup'").fetchall()
    tasks = {r["entity_id"]: r["source"] for r in rows}
    assert "ACME-RFQ-1" in tasks and tasks["ACME-RFQ-1"] == "acme-website"
    assert "GY-RFQ-1" not in tasks  # gyutron entity untouched by the acme run

    acme_report = generate_daily_owner_report(customer_id="acme_demo")
    gy_report = generate_daily_owner_report(customer_id="gyutron", language="zh-CN")
    with get_connection() as connection:
        acme_row = connection.execute("SELECT * FROM reports WHERE id = ?", (acme_report["report_id"],)).fetchone()
        gy_row = connection.execute("SELECT * FROM reports WHERE id = ?", (gy_report["report_id"],)).fetchone()
    assert acme_row["customer_id"] == "acme_demo"
    assert gy_row["customer_id"] == "gyutron"
    # demo data never leaks into the real customer's report and vice versa
    assert "DemoCo" not in gy_row["content_markdown"]
    assert "RealCo" not in acme_row["content_markdown"]
    # acme defaults to English (customer config), gyutron got Chinese as requested
    assert acme_row["title"] == "Daily Owner Report"
    assert gy_row["title"] == "老板日报"


def test_per_customer_rule_thresholds(isolated_db):
    with get_connection() as connection:
        connection.execute(
            "UPDATE workspace_customers SET config_json = ? WHERE customer_id = 'acme_demo'",
            (json.dumps({"rule_thresholds": {"rfq_followup": {"threshold_hours": 999}}}),),
        )
        connection.commit()
    _, gy_cfg = rule_runtime("rfq_followup", "gyutron")
    _, acme_cfg = rule_runtime("rfq_followup", "acme_demo")
    assert gy_cfg["threshold_hours"] == 24
    assert acme_cfg["threshold_hours"] == 999


def test_demo_reset_guards_real_customers(isolated_db):
    seed_two_customers()
    with pytest.raises(ValueError):
        reset_demo_customer("gyutron")  # NEVER allowed on a real customer
    result = reset_demo_customer("acme_demo")
    assert result["deleted"] >= 1
    # acme rows gone, gyutron rows intact
    assert metrics.load_records(sources=customer_sources("acme_demo")) == []
    assert {r["id"] for r in metrics.load_records(sources=customer_sources("gyutron"))} == {"GY-RFQ-1"}
    assert commerce_summary(sources=customer_sources("acme_demo"))["orders"] == 0


def test_customers_listed_with_branding(isolated_db):
    customers = {c["customer_id"]: c for c in list_customers()}
    assert customers["gyutron"]["is_demo"] == 0
    assert customers["acme_demo"]["is_demo"] == 1
    assert customers["acme_demo"]["brand_name"] == "ACME Industrial"
    assert get_customer("gyutron")["accent_color"] == "#4b2e83"
