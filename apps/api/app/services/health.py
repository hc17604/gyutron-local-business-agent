"""Per-customer health check + data quality (Phase 6).

Levels: healthy / warning / critical. Never leaks secret values — only
"configured / missing". Deterministic; safe to run on a schedule.
"""
import json
import os
from datetime import datetime, timedelta, timezone

import httpx

from app.database import get_connection
from app.services.customers import customer_sources, get_customer


SYNC_STALE_HOURS = 2      # warning if no successful sync for this long
REPORT_STALE_HOURS = 36   # warning if no report generated for this long
MAX_ABS_AMOUNT = 1_000_000


def _level(checks: list[dict]) -> str:
    if any(c["severity"] == "critical" for c in checks):
        return "critical"
    if any(c["severity"] == "warning" for c in checks):
        return "warning"
    return "healthy"


def data_quality_checks(sources: list[str] | None = None) -> list[dict]:
    """≥8 anomaly classes across the commerce + website stores."""
    out: list[dict] = []
    flt = ""
    params: list = []
    if sources is not None:
        flt = " WHERE source IN (%s)" % (", ".join("?" for _ in sources) or "''")
        params = list(sources)

    def add(check, severity, count, detail):
        if count:
            out.append({"check": check, "severity": severity, "count": count, "detail": detail})

    with get_connection() as connection:
        q = lambda sql: connection.execute(sql, params).fetchone()[0]  # noqa: E731
        add("order_negative_or_huge_amount", "critical",
            q(f"SELECT COUNT(*) FROM orders{flt or ' WHERE 1=1'} AND (total_amount < 0 OR total_amount > {MAX_ABS_AMOUNT})"
              if flt else f"SELECT COUNT(*) FROM orders WHERE total_amount < 0 OR total_amount > {MAX_ABS_AMOUNT}"),
            "orders with negative or implausibly large totals")
        add("order_missing_currency", "warning",
            q(f"SELECT COUNT(*) FROM orders{flt or ' WHERE 1=1'} AND total_amount IS NOT NULL AND (currency IS NULL OR currency = '')"
              if flt else "SELECT COUNT(*) FROM orders WHERE total_amount IS NOT NULL AND (currency IS NULL OR currency = '')"),
            "orders with an amount but no currency")
        add("order_missing_created_at", "warning",
            q(f"SELECT COUNT(*) FROM orders{flt or ' WHERE 1=1'} AND (created_at_source IS NULL OR created_at_source = '')"
              if flt else "SELECT COUNT(*) FROM orders WHERE created_at_source IS NULL OR created_at_source = ''"),
            "orders without a source timestamp")
        add("order_invalid_status", "warning",
            q(f"SELECT COUNT(*) FROM orders{flt or ' WHERE 1=1'} AND status NOT IN ('pending','paid','fulfilled','cancelled','refunded')"
              if flt else "SELECT COUNT(*) FROM orders WHERE status NOT IN ('pending','paid','fulfilled','cancelled','refunded')"),
            "orders with a non-canonical status")
        add("payment_without_order", "warning",
            connection.execute(
                "SELECT COUNT(*) FROM payments p WHERE p.status='paid' AND NOT EXISTS "
                "(SELECT 1 FROM orders o WHERE o.source = p.source AND o.external_id = p.order_ref)"
                + (" AND p.source IN (%s)" % ", ".join("?" for _ in sources) if sources is not None else ""),
                params,
            ).fetchone()[0],
            "paid payments whose order_ref matches no order (reconciliation gap)")
        add("source_unbound_to_customer", "warning",
            connection.execute("SELECT COUNT(*) FROM data_sources WHERE customer_id IS NULL OR customer_id = ''").fetchone()[0],
            "data_sources rows not bound to any customer")
        add("task_missing_context", "warning",
            connection.execute("SELECT COUNT(*) FROM agent_tasks WHERE source IS NULL OR source = ''").fetchone()[0],
            "tasks without a source context")
        add("empty_report_content", "warning",
            connection.execute("SELECT COUNT(*) FROM reports WHERE status='ready' AND (content_markdown IS NULL OR content_markdown = '')").fetchone()[0],
            "ready reports with empty content")
        add("website_row_missing_created", "warning",
            connection.execute(
                "SELECT COUNT(*) FROM website_data WHERE data_type != 'event' AND (created_at_source IS NULL OR created_at_source = '')"
                + (" AND source IN (%s)" % ", ".join("?" for _ in sources) if sources is not None else ""),
                params,
            ).fetchone()[0],
            "synced records without a source timestamp")
    return out


def check_customer_health(customer_id: str) -> dict:
    customer = get_customer(customer_id)
    if not customer:
        return {"customer_id": customer_id, "status": "critical",
                "checks": [{"check": "customer_exists", "severity": "critical", "count": 1, "detail": "unknown customer_id"}]}
    sources = customer_sources(customer_id)
    checks: list[dict] = []
    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        connectors = connection.execute(
            "SELECT dc.* FROM data_connectors dc JOIN data_sources ds ON ds.connector_id = dc.id WHERE ds.customer_id = ? GROUP BY dc.id",
            (customer_id,),
        ).fetchall()
        report = connection.execute(
            "SELECT created_at FROM reports WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,)
        ).fetchone()
        stuck_high = connection.execute(
            "SELECT COUNT(*) FROM agent_tasks WHERE status='open' AND priority='high' AND source IN (%s)"
            % (", ".join("?" for _ in sources) or "''"),
            sources or [],
        ).fetchone()[0]

    if not connectors:
        checks.append({"check": "connector_configured", "severity": "warning", "count": 1, "detail": "no connector bound to this customer's sources"})
    for c in connectors:
        config = json.loads(c["config_json"] or "{}")
        # secret presence (value NEVER read into the result)
        if c["connector_type"] == "gyutron_website":
            env_var = config.get("api_key_env") or "GYUTRON_WEBSITE_API_KEY"
            if not os.environ.get(env_var, "").strip():
                checks.append({"check": "api_key_configured", "severity": "critical", "count": 1, "detail": f"{env_var} not set in the environment"})
            base = (config.get("base_url") or "https://www.gyutron.com").rstrip("/")
            try:
                r = httpx.get(f"{base}/api/v1/health", timeout=6.0)
                if r.status_code != 200:
                    checks.append({"check": "website_reachable", "severity": "critical", "count": 1, "detail": f"health returned {r.status_code}"})
            except httpx.HTTPError as exc:
                checks.append({"check": "website_reachable", "severity": "critical", "count": 1, "detail": f"unreachable: {type(exc).__name__}"})
        if c["last_sync_at"]:
            try:
                last = datetime.fromisoformat(str(c["last_sync_at"]).replace(" ", "T")).replace(tzinfo=timezone.utc)
                if now - last > timedelta(hours=SYNC_STALE_HOURS):
                    checks.append({"check": "sync_fresh", "severity": "warning", "count": 1,
                                   "detail": f"{c['name']}: last sync {c['last_sync_at']} (> {SYNC_STALE_HOURS}h)"})
            except ValueError:
                pass
        else:
            checks.append({"check": "sync_fresh", "severity": "warning", "count": 1, "detail": f"{c['name']}: never synced"})
        if c["status"] == "error":
            checks.append({"check": "connector_status", "severity": "critical", "count": 1, "detail": f"{c['name']}: last sync errored ({c['last_sync_status']})"})

    if report is None:
        checks.append({"check": "report_fresh", "severity": "warning", "count": 1, "detail": "no report generated yet for this customer"})
    if stuck_high:
        checks.append({"check": "high_tasks_backlog", "severity": "warning", "count": stuck_high, "detail": f"{stuck_high} open high-priority task(s)"})

    checks.extend(data_quality_checks(sources))
    return {"customer_id": customer_id, "status": _level(checks), "checks": checks,
            "checked_at": now.isoformat(timespec="seconds")}
