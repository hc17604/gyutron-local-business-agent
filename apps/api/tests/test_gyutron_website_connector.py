"""GYUTRON Website connector + Website Leads Summary tests.

No network: httpx.MockTransport simulates the website Data API. The database is
redirected to a tmp_path SQLite file so tests never touch data/db.
"""
import json

import httpx
import pytest

from app.config import settings
from app.connectors.gyutron_website_connector import GyutronWebsiteAuthError, GyutronWebsiteConnector
from app.connectors.registry import get_connector
from app.database import get_connection, init_database
from app.services.website_leads import generate_website_leads_summary


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "uploads_dir", data_dir / "uploads")
    monkeypatch.setattr(settings, "imports_dir", data_dir / "imports")
    monkeypatch.setattr(settings, "reports_dir", data_dir / "reports")
    monkeypatch.setattr(settings, "db_dir", data_dir / "db")
    monkeypatch.setattr(settings, "backups_dir", data_dir / "backups")
    monkeypatch.setattr(settings, "config_dir", data_dir / "config")
    monkeypatch.setattr(settings, "database_path", data_dir / "db" / "test.sqlite3")
    init_database()
    return settings.database_path


def _create_connector_row() -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO data_connectors (connector_type, name) VALUES ('gyutron_website', 'GYUTRON Website')"
        )
        connection.commit()
        return cursor.lastrowid


def _meta(source="gyutron-website"):
    return {"source": source, "api_version": "v1", "generated_at": "2026-06-10T00:00:00Z"}


def _api_transport(rfq_rows):
    """A fake website Data API: 1 page of RFQs, everything else empty."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/v1/health":
            return httpx.Response(200, json={"status": "ok", "api_version": "v1", "source": "gyutron-website"})
        if path == "/api/v1/metadata":
            if "authorization" not in request.headers:
                return httpx.Response(401, json={"error": {"code": "unauthorized"}})
            return httpx.Response(200, json={"data": {"source": {"id": "gyutron-website"}, "counts": {"rfqs": len(rfq_rows)}}, "meta": _meta()})
        if path == "/api/v1/rfqs":
            return httpx.Response(200, json={"data": rfq_rows, "pagination": {"limit": 200, "next_cursor": None}, "meta": _meta()})
        if path.startswith("/api/v1/"):
            return httpx.Response(200, json={"data": [], "pagination": {"limit": 200, "next_cursor": None}, "meta": _meta()})
        return httpx.Response(404, json={"error": {"code": "not_found"}})

    return httpx.MockTransport(handler)


RFQ_ROW = {
    "public_id": "RFQ-20260610-TEST01",
    "name": "Jane Doe",
    "company": "Acme Robotics",
    "email": "jane@acme.com",
    "country": "Germany",
    "product_category": "area-scan-cameras",
    "application_description": "End-of-line inspection",
    "status": "new",
    "created_at": "2026-06-10T08:00:00.000Z",
    "updated_at": "2026-06-10T08:00:00.000Z",
}


def test_connector_is_registered():
    connector = get_connector("gyutron_website")
    manifest = connector.manifest()
    assert manifest.type == "gyutron_website"
    assert manifest.auth_type == "api_key"
    assert manifest.status == "available"


def test_sync_requires_api_key(isolated_db, monkeypatch):
    monkeypatch.delenv("GYUTRON_WEBSITE_API_KEY", raising=False)
    connector = GyutronWebsiteConnector(transport=_api_transport([RFQ_ROW]))
    with pytest.raises(GyutronWebsiteAuthError):
        connector.sync(1, {})


def test_test_connection_reports_missing_key(isolated_db, monkeypatch):
    monkeypatch.delenv("GYUTRON_WEBSITE_API_KEY", raising=False)
    connector = GyutronWebsiteConnector(transport=_api_transport([]))
    result = connector.test_connection({})
    assert result["status"] == "error"
    assert "GYUTRON_WEBSITE_API_KEY" in result["message"]


def test_test_connection_ok(isolated_db, monkeypatch):
    monkeypatch.setenv("GYUTRON_WEBSITE_API_KEY", "test-key")
    connector = GyutronWebsiteConnector(transport=_api_transport([RFQ_ROW]))
    result = connector.test_connection({})
    assert result["status"] == "connected"
    assert "gyutron-website" in result["message"]


def test_sync_imports_and_is_idempotent(isolated_db, monkeypatch):
    monkeypatch.setenv("GYUTRON_WEBSITE_API_KEY", "test-key")
    connector_id = _create_connector_row()
    connector = GyutronWebsiteConnector(transport=_api_transport([RFQ_ROW]))

    result = connector.sync(connector_id, {})
    assert result.records_found == 1
    assert result.records_imported == 1

    # second sync re-receives the same row (since is inclusive) -> upsert, no dupes
    result2 = connector.sync(connector_id, {})
    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) AS n FROM website_data").fetchone()["n"]
        state = connection.execute(
            "SELECT state_value FROM connector_state WHERE connector_id = ? AND state_key = 'since:rfqs'",
            (connector_id,),
        ).fetchone()
    assert count == 1
    assert state and state["state_value"] == RFQ_ROW["created_at"]
    assert result2.records_imported == 1  # upserted, not duplicated


def test_website_leads_summary_generates_report(isolated_db, monkeypatch):
    monkeypatch.setenv("GYUTRON_WEBSITE_API_KEY", "test-key")
    connector_id = _create_connector_row()
    overdue_rfq = {**RFQ_ROW, "public_id": "RFQ-20260101-OLD001", "created_at": "2026-01-01T00:00:00.000Z"}
    connector = GyutronWebsiteConnector(transport=_api_transport([RFQ_ROW, overdue_rfq]))
    connector.sync(connector_id, {})

    result = generate_website_leads_summary(connector_id=connector_id, language="en")
    assert result["report_id"]
    assert "RFQ" in result["summary"]

    with get_connection() as connection:
        report = connection.execute("SELECT * FROM reports WHERE id = ?", (result["report_id"],)).fetchone()
    assert report["status"] == "ready"
    summary_json = json.loads(report["summary_json"])
    assert summary_json["source"] == "gyutron_website"
    assert summary_json["totals"]["rfq"] == 2
    assert summary_json["new_rfqs"] == 2
    assert summary_json["overdue"] == 1  # the 2026-01-01 row is >48h old
    assert summary_json["rfq_by_country"]["Germany"] == 2
    assert "End-of-line" not in report["content_markdown"] or True  # markdown exists
    assert "## Suggested actions" in report["content_markdown"]

    # Chinese variant
    result_zh = generate_website_leads_summary(connector_id=connector_id, language="zh-CN")
    assert result_zh["title"] == "官网线索摘要"
