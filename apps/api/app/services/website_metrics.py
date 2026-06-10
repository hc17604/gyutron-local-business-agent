"""Website metrics layer — the single foundation for reports, rules, and summaries.

Loads synced rows from `website_data`, applies the exclusion rules (spam +
internal-test markers, configurable via the `exclude_internal_tests` rule), and
provides time-range filtering plus the aggregations every report needs. All
deterministic — no model calls.
"""
import json
from collections import Counter
from datetime import datetime, timedelta

from app.database import get_connection


TIME_RANGES = ("today", "yesterday", "7d", "30d", "all")
RECORD_TYPES = ("lead", "rfq", "support_request", "download_request")
OPEN_STATUSES = ("new", "reviewing")
FUNNEL_STATUSES = ("new", "reviewing", "waiting_for_info", "quoted", "won", "lost")

DEFAULT_EXCLUSIONS = {"statuses": ["spam"], "companies": ["GYUTRON Internal Test"], "utm_sources": ["e2e-test"]}


def _local_tz():
    return datetime.now().astimezone().tzinfo


def parse_created(value: str | None) -> datetime | None:
    """ISO timestamp (UTC from the API) → aware datetime in the LOCAL timezone."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(_local_tz())
    except ValueError:
        return None


def range_bounds(time_range: str, *, now: datetime | None = None) -> tuple[datetime | None, datetime | None]:
    """(start, end) in local time; None = unbounded. Day boundaries are local."""
    now = now or datetime.now(_local_tz())
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if time_range == "today":
        return today, None
    if time_range == "yesterday":
        return today - timedelta(days=1), today
    if time_range == "7d":
        return now - timedelta(days=7), None
    if time_range == "30d":
        return now - timedelta(days=30), None
    return None, None


def exclusion_config() -> dict:
    """Markers from the exclude_internal_tests rule (falls back to defaults)."""
    try:
        with get_connection() as connection:
            row = connection.execute("SELECT enabled, config_json FROM rule_state WHERE rule_id = 'exclude_internal_tests'").fetchone()
        if row is None:
            return DEFAULT_EXCLUSIONS
        if not row["enabled"]:
            return {"statuses": [], "companies": [], "utm_sources": []}
        config = json.loads(row["config_json"] or "{}")
        return {**DEFAULT_EXCLUSIONS, **{k: v for k, v in config.items() if v is not None}}
    except Exception:
        return DEFAULT_EXCLUSIONS


def is_excluded(item: dict, exclusions: dict) -> bool:
    if item["status"] in (exclusions.get("statuses") or []):
        return True
    company = (item["data"].get("company") or "").strip()
    if company and company in (exclusions.get("companies") or []):
        return True
    utm = (item["data"].get("utm_source") or "").strip()
    if utm and utm in (exclusions.get("utm_sources") or []):
        return True
    return False


def load_records(
    connector_id: int | None = None,
    *,
    time_range: str = "all",
    types: tuple = RECORD_TYPES,
    include_excluded: bool = False,
) -> list[dict]:
    """Parsed, exclusion-filtered records: {type,id,status,created(dt),data}."""
    with get_connection() as connection:
        if connector_id is None:
            rows = connection.execute("SELECT data_type, external_id, status, created_at_source, data_json FROM website_data").fetchall()
        else:
            rows = connection.execute(
                "SELECT data_type, external_id, status, created_at_source, data_json FROM website_data WHERE connector_id = ?",
                (connector_id,),
            ).fetchall()

    start, end = range_bounds(time_range)
    exclusions = exclusion_config()
    out: list[dict] = []
    for row in rows:
        if row["data_type"] not in types:
            continue
        try:
            data = json.loads(row["data_json"] or "{}")
        except json.JSONDecodeError:
            data = {}
        created = parse_created(row["created_at_source"])
        if start and (created is None or created < start):
            continue
        if end and created and created >= end:
            continue
        item = {"type": row["data_type"], "id": row["external_id"], "status": row["status"], "created": created, "data": data}
        if not include_excluded and is_excluded(item, exclusions):
            continue
        out.append(item)
    return out


def count_by(records: list[dict], field: str, *, types: tuple | None = None, empty_label: str = "—") -> Counter:
    counter: Counter = Counter()
    for item in records:
        if types and item["type"] not in types:
            continue
        counter[(item["data"].get(field) or empty_label)] += 1
    return counter


def totals_by_type(records: list[dict]) -> dict:
    return dict(Counter(item["type"] for item in records))


def waiting_hours(item: dict, *, now: datetime | None = None) -> float | None:
    if item["created"] is None:
        return None
    now = now or datetime.now(_local_tz())
    return (now - item["created"]).total_seconds() / 3600


def open_items(records: list[dict], *, types: tuple = ("lead", "rfq", "support_request")) -> list[dict]:
    return [i for i in records if i["type"] in types and i["status"] in OPEN_STATUSES]


def overdue_items(records: list[dict], threshold_hours: float, *, types: tuple = ("lead", "rfq", "support_request")) -> list[dict]:
    out = []
    for item in open_items(records, types=types):
        hours = waiting_hours(item)
        if hours is not None and hours >= threshold_hours:
            out.append({**item, "waiting_hours": hours})
    out.sort(key=lambda x: -x["waiting_hours"])
    return out


def rfq_funnel(records: list[dict]) -> dict:
    counter = Counter(i["status"] for i in records if i["type"] == "rfq")
    return {status: counter.get(status, 0) for status in FUNNEL_STATUSES}


def day_counts(records: list[dict], *, types: tuple | None = None, days: int = 7) -> list[tuple[str, int]]:
    """[(YYYY-MM-DD, count)] for the last `days` local days, oldest first."""
    now = datetime.now(_local_tz())
    buckets = {(now - timedelta(days=offset)).strftime("%Y-%m-%d"): 0 for offset in range(days - 1, -1, -1)}
    for item in records:
        if types and item["type"] not in types:
            continue
        if item["created"] is None:
            continue
        key = item["created"].strftime("%Y-%m-%d")
        if key in buckets:
            buckets[key] += 1
    return list(buckets.items())


def repeat_emails(records: list[dict], *, min_count: int = 2) -> list[tuple[str, int]]:
    counter = Counter((i["data"].get("email") or "").lower() for i in records if i["data"].get("email"))
    return [(email, n) for email, n in counter.most_common() if n >= min_count]


def category_country_matrix(records: list[dict]) -> dict:
    """{category: {country: n}} for RFQs."""
    matrix: dict = {}
    for item in records:
        if item["type"] != "rfq":
            continue
        cat = item["data"].get("product_category") or "—"
        country = item["data"].get("country") or "—"
        matrix.setdefault(cat, Counter())[country] += 1
    return {cat: dict(c) for cat, c in matrix.items()}


def event_type_counts(connector_id: int | None = None) -> dict:
    with get_connection() as connection:
        if connector_id is None:
            rows = connection.execute("SELECT data_json FROM website_data WHERE data_type = 'event'").fetchall()
        else:
            rows = connection.execute("SELECT data_json FROM website_data WHERE data_type = 'event' AND connector_id = ?", (connector_id,)).fetchall()
    counter: Counter = Counter()
    for row in rows:
        try:
            counter[json.loads(row["data_json"]).get("event_type") or "?"] += 1
        except json.JSONDecodeError:
            continue
    return dict(counter)
