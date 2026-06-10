"""Customer (workspace tenant) layer — Phase 5.

`source` answers "where did this row come from"; `customer_id` answers "whose
data is this". Every data_source belongs to exactly one customer; every
customer-scoped query resolves customer_id → its source keys and filters by
source. Demo customers (is_demo=1) are hard-isolated: demo data never enters a
real customer's reports, and demo resets can only touch mock sources.
"""
import json

from app.database import get_connection
from app.services.audit import write_audit_log


DEFAULT_CUSTOMERS = [
    {
        "customer_id": "gyutron",
        "display_name": "GYUTRON",
        "brand_name": "GYUTRON",
        "logo_text": "GYUTRON",
        "accent_color": "#4b2e83",
        "report_language": "zh-CN",
        "currency": "USD",
        "timezone": "Asia/Hong_Kong",
        "footer_legal": "GYUTRON — industrial automation hardware",
        "is_demo": 0,
        "config_json": "{}",
    },
    {
        "customer_id": "acme_demo",
        "display_name": "ACME Demo",
        "brand_name": "ACME Industrial",
        "logo_text": "ACME",
        "accent_color": "#0b6e4f",
        "report_language": "en",
        "currency": "USD",
        "timezone": "Asia/Kuala_Lumpur",
        "footer_legal": "ACME Industrial (demo environment — fictional data)",
        "is_demo": 1,
        "config_json": "{}",
    },
]

# source_key → (customer_id, is_mock)
DEFAULT_SOURCE_OWNERSHIP = {
    "gyutron-website": ("gyutron", 0),
    "gyutron-shop": ("gyutron", 0),
    "acme-website": ("acme_demo", 1),
    "acme-industrial-csv": ("acme_demo", 1),
}


def ensure_customers() -> None:
    """Seed customers + bind known sources to their owners (idempotent)."""
    with get_connection() as connection:
        for c in DEFAULT_CUSTOMERS:
            connection.execute(
                """
                INSERT OR IGNORE INTO workspace_customers
                  (customer_id, display_name, brand_name, logo_text, accent_color, report_language,
                   currency, timezone, footer_legal, is_demo, config_json)
                VALUES (:customer_id, :display_name, :brand_name, :logo_text, :accent_color,
                        :report_language, :currency, :timezone, :footer_legal, :is_demo, :config_json)
                """,
                c,
            )
        for source_key, (customer_id, is_mock) in DEFAULT_SOURCE_OWNERSHIP.items():
            connection.execute(
                "UPDATE data_sources SET customer_id = ?, is_mock = ? WHERE source_key = ? AND (customer_id IS NULL OR customer_id = '')",
                (customer_id, is_mock, source_key),
            )
        connection.commit()


def list_customers() -> list[dict]:
    ensure_customers()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM workspace_customers ORDER BY is_demo, customer_id").fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["config"] = json.loads(item.pop("config_json") or "{}")
        except json.JSONDecodeError:
            item["config"] = {}
        out.append(item)
    return out


def get_customer(customer_id: str) -> dict | None:
    """READ-ONLY lookup (no seeding) — safe to call inside open write transactions."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM workspace_customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    try:
        item["config"] = json.loads(item.pop("config_json") or "{}")
    except json.JSONDecodeError:
        item["config"] = {}
    return item


def customer_sources(customer_id: str | None) -> list[str] | None:
    """Source keys owned by a customer; None = no filtering (all customers)."""
    if not customer_id:
        return None
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT source_key FROM data_sources WHERE customer_id = ?", (customer_id,)
        ).fetchall()
    keys = [r["source_key"] for r in rows]
    # Unbound-but-conventional fallback so a fresh source named <customer>-* still resolves.
    if not keys:
        prefix = customer_id.split("_")[0].replace("_", "-")
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT source_key FROM data_sources WHERE source_key LIKE ?", (f"{prefix}-%",)
            ).fetchall()
        keys = [r["source_key"] for r in rows]
    return keys or ["__none__"]  # unknown customer → match nothing (never leak)


def customer_rule_threshold(customer_id: str | None, rule_id: str) -> dict:
    """Per-customer rule config overrides: customers.config_json.rule_thresholds[rule_id]."""
    if not customer_id:
        return {}
    customer = get_customer(customer_id)
    if not customer:
        return {}
    thresholds = (customer.get("config") or {}).get("rule_thresholds") or {}
    value = thresholds.get(rule_id)
    return value if isinstance(value, dict) else {}


def assert_demo_customer(customer_id: str) -> dict:
    """Guard for destructive demo operations — refuses non-demo customers."""
    customer = get_customer(customer_id)
    if not customer or not customer.get("is_demo"):
        raise ValueError(f"{customer_id} is not a demo customer — refusing destructive operation.")
    return customer


def reset_demo_customer(customer_id: str = "acme_demo") -> dict:
    """Wipe a DEMO customer's commerce + website rows + tasks (mock sources only),
    so the demo can be re-seeded cleanly. Hard-refuses real customers."""
    from app.services.commerce_store import COMMERCE_TABLES

    assert_demo_customer(customer_id)
    sources = customer_sources(customer_id) or []
    deleted = 0
    with get_connection() as connection:
        mock_rows = connection.execute(
            "SELECT source_key FROM data_sources WHERE customer_id = ? AND is_mock = 1", (customer_id,)
        ).fetchall()
        mock_sources = [r["source_key"] for r in mock_rows] or sources
        for table in COMMERCE_TABLES:
            for s in mock_sources:
                deleted += connection.execute(f"DELETE FROM {table} WHERE source = ?", (s,)).rowcount
        for s in mock_sources:
            deleted += connection.execute("DELETE FROM website_data WHERE source = ?", (s,)).rowcount
            deleted += connection.execute("DELETE FROM agent_tasks WHERE source = ?", (s,)).rowcount
        connection.commit()
    write_audit_log("demo_reset", "customer", target_id=customer_id, risk_level="medium",
                    output_summary=f"{deleted} demo row(s) cleared (sources: {', '.join(mock_sources)})")
    return {"customer_id": customer_id, "deleted": deleted, "sources": mock_sources}
