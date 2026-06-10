"""Commerce metrics — same four-layer pattern as website_metrics (NO parallel
ad-hoc math anywhere else). Revenue is double-count-safe: it comes from ORDERS
in a paid-like state only; payments are used for reconciliation, never summed
into revenue alongside orders.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.database import get_connection
from app.services.website_metrics import parse_created, range_bounds


REVENUE_STATUSES = ("paid", "fulfilled")


def _rows(table: str, source: str | None = None) -> list[dict]:
    query = f"SELECT * FROM {table}"
    params: list = []
    if source:
        query += " WHERE source = ?"
        params.append(source)
    with get_connection() as connection:
        return [dict(r) for r in connection.execute(query, params).fetchall()]


def _in_range(item_created: str | None, time_range: str) -> bool:
    start, end = range_bounds(time_range)
    created = parse_created(item_created)
    if start and (created is None or created < start):
        return False
    if end and created and created >= end:
        return False
    return True


def commerce_summary(source: str | None = None, time_range: str = "all") -> dict:
    orders = [o for o in _rows("orders", source) if _in_range(o.get("created_at_source"), time_range)]
    revenue_orders = [o for o in orders if o["status"] in REVENUE_STATUSES]
    revenue = round(sum(o.get("amount_base") or 0 for o in revenue_orders), 2)
    aov = round(revenue / len(revenue_orders), 2) if revenue_orders else 0.0

    items = _rows("order_items", source)
    order_ids = {o["external_id"] for o in orders}
    top_products: Counter = Counter()
    for item in items:
        if item.get("order_external_id") in order_ids:
            top_products[item.get("title") or item.get("sku") or "?"] += int(item.get("quantity") or 0)

    by_country = Counter((o.get("country") or "—") for o in orders)
    by_status = Counter(o["status"] for o in orders)

    events = [e for e in _rows("cart_events", None if source else None) if _in_range(e.get("occurred_at"), time_range)]
    if source:
        events = [e for e in events if e["source"] == source]
    event_counts = Counter(e["event_type"] for e in events)

    return {
        "orders": len(orders),
        "revenue_base": revenue,
        "aov_base": aov,
        "by_status": dict(by_status),
        "by_country": dict(by_country),
        "top_products": dict(top_products.most_common(8)),
        "cart_events": dict(event_counts),
    }


def abandoned_carts(window_hours: int = 48, source: str = "gyutron-shop") -> list[dict]:
    """cart.added events older than the window with NO later quote.requested for
    the same product handle (no session linkage by design — handle-level signal)."""
    events = _rows("cart_events", source)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    quoted_handles = {
        e.get("product_handle")
        for e in events
        if e["event_type"] == "quote.requested" and e.get("product_handle")
    }
    out = []
    for e in events:
        if e["event_type"] != "cart.added":
            continue
        occurred = parse_created(e.get("occurred_at"))
        if occurred is None or occurred > cutoff:
            continue
        if e.get("product_handle") in quoted_handles:
            continue
        out.append(e)
    return out


def paid_not_fulfilled(threshold_days: int = 7, source: str | None = None) -> list[dict]:
    orders = _rows("orders", source)
    cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)
    out = []
    for o in orders:
        if o["status"] != "paid":
            continue
        created = parse_created(o.get("created_at_source"))
        if created and created < cutoff:
            out.append(o)
    return out


def high_views_no_inquiry(min_views: int = 5, source: str = "gyutron-shop") -> list[tuple[str, int]]:
    events = _rows("cart_events", source)
    views: Counter = Counter()
    engaged = set()
    for e in events:
        handle = e.get("product_handle")
        if not handle:
            continue
        if e["event_type"] == "product.viewed":
            views[handle] += 1
        else:
            engaged.add(handle)
    return [(h, n) for h, n in views.most_common() if n >= min_views and h not in engaged]


def revenue_reconciliation(source: str | None = None) -> dict:
    """payments vs orders cross-check (per order_ref) — proves no double count."""
    orders = {o["external_id"]: o for o in _rows("orders", source)}
    payments = [p for p in _rows("payments", source) if p["status"] == "paid"]
    matched = sum(1 for p in payments if p.get("order_ref") in orders)
    return {"paid_payments": len(payments), "matched_to_orders": matched, "unmatched": len(payments) - matched}
