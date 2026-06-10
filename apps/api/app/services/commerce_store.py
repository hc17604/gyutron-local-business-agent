"""Commerce store — the ONLY write path into the unified commerce model.

Every adapter (CSV commerce connector, shop behavior events, future SaaS
connectors) writes through `upsert`, which enforces: (source, external_id)
idempotency, raw_payload SANITIZATION, schema_version stamping, and source
registration in `data_sources`. GDPR path: `delete_entity(source, external_id)`.
"""
import json

from app.database import get_connection
from app.services.commerce_sanitize import sanitize_payload


SCHEMA_VERSION = 1
BASE_CURRENCY = "USD"

# Phase-4 static conversion (configurable later; good enough for reporting).
FX_TO_BASE = {"USD": 1.0, "EUR": 1.08, "CNY": 0.14, "HKD": 0.13, "JPY": 0.0066, "GBP": 1.27, "SGD": 0.74}

COMMERCE_TABLES = {
    "orders": ["order_number", "customer_external_id", "customer_email", "status", "raw_status",
               "total_amount", "currency", "amount_base", "item_count", "country", "created_at_source"],
    "order_items": ["order_external_id", "product_external_id", "sku", "title", "quantity",
                    "unit_amount", "currency", "amount_base"],
    "customers": ["email", "name", "company", "country", "first_seen_at", "last_seen_at"],
    "commerce_products": ["sku", "title", "category", "price_amount", "currency", "amount_base", "status"],
    "payments": ["order_ref", "status", "raw_status", "amount", "currency", "amount_base", "method", "created_at_source"],
    "shipments": ["order_ref", "status", "raw_status", "carrier", "tracking_ref", "country", "created_at_source"],
    "cart_events": ["event_type", "product_handle", "locale", "occurred_at"],
    "refunds": ["order_ref", "status", "amount", "currency", "amount_base", "created_at_source"],
    "inventory_snapshots": ["sku", "quantity", "snapshot_at"],
}

# Canonical status vocabularies + per-source raw→canonical maps (config-driven).
ORDER_STATUSES = ("pending", "paid", "fulfilled", "cancelled", "refunded")
ORDER_STATUS_MAP = {
    # generic + Shopify-style raw values
    "pending": "pending", "open": "pending", "unpaid": "pending", "awaiting_payment": "pending",
    "paid": "paid", "authorized": "paid", "partially_paid": "paid",
    "fulfilled": "fulfilled", "shipped": "fulfilled", "complete": "fulfilled", "completed": "fulfilled", "delivered": "fulfilled",
    "cancelled": "cancelled", "canceled": "cancelled", "voided": "cancelled",
    "refunded": "refunded", "partially_refunded": "refunded",
}
PAYMENT_STATUS_MAP = {
    "pending": "pending", "authorized": "pending", "success": "paid", "succeeded": "paid", "paid": "paid",
    "captured": "paid", "failed": "failed", "refunded": "refunded", "voided": "cancelled",
}


def to_base(amount, currency) -> float | None:
    if amount is None:
        return None
    try:
        return round(float(amount) * FX_TO_BASE.get((currency or BASE_CURRENCY).upper(), 1.0), 2)
    except (TypeError, ValueError):
        return None


def canonical_order_status(raw: str | None) -> str:
    return ORDER_STATUS_MAP.get((raw or "").strip().lower(), "pending")


def canonical_payment_status(raw: str | None) -> str:
    return PAYMENT_STATUS_MAP.get((raw or "").strip().lower(), "pending")


def ensure_source(source_key: str, display_name: str, kind: str, connector_id: int | None = None) -> None:
    """Register a data source (idempotent). Reports/dashboard filters key off this."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO data_sources (source_key, display_name, kind, connector_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source_key) DO UPDATE SET
              display_name = excluded.display_name, kind = excluded.kind,
              connector_id = COALESCE(excluded.connector_id, data_sources.connector_id),
              updated_at = CURRENT_TIMESTAMP
            """,
            (source_key, display_name, kind, connector_id),
        )
        connection.commit()


def list_sources() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM data_sources ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def upsert(connection, table: str, source: str, external_id: str, columns: dict, raw_payload) -> bool:
    """Idempotent upsert; returns True. Raw payload is sanitized HERE — no caller
    may write raw_payload directly."""
    if table not in COMMERCE_TABLES:
        raise ValueError(f"Unknown commerce table: {table}")
    allowed = COMMERCE_TABLES[table]
    cols = {k: v for k, v in columns.items() if k in allowed}
    raw = json.dumps(sanitize_payload(raw_payload or {}), ensure_ascii=False)
    names = ["source", "external_id", *cols.keys(), "raw_payload", "schema_version"]
    values = [source, str(external_id), *cols.values(), raw, SCHEMA_VERSION]
    placeholders = ", ".join("?" for _ in names)
    updates = ", ".join(f"{c} = excluded.{c}" for c in [*cols.keys(), "raw_payload", "schema_version"])
    connection.execute(
        f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders}) "
        f"ON CONFLICT(source, external_id) DO UPDATE SET {updates}, synced_at = CURRENT_TIMESTAMP",
        values,
    )
    return True


def delete_entity(source: str, external_id: str) -> int:
    """GDPR-style cascade delete across all commerce tables by (source, external_id)."""
    deleted = 0
    with get_connection() as connection:
        for table in COMMERCE_TABLES:
            cursor = connection.execute(f"DELETE FROM {table} WHERE source = ? AND external_id = ?", (source, str(external_id)))
            deleted += cursor.rowcount
        connection.commit()
    return deleted
