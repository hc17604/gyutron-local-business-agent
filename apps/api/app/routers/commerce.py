"""Cross-source commerce overview — feeds the Owner Dashboard. Read-only.
Source filter values come from the data_sources REGISTRY, not ad-hoc strings."""
from fastapi import APIRouter

from app.database import get_connection
from app.services.commerce_metrics import commerce_summary, revenue_reconciliation
from app.services.commerce_store import list_sources
from app.services.website_metrics import load_records, totals_by_type


router = APIRouter(prefix="/commerce", tags=["commerce"])


@router.get("/overview")
def commerce_overview(source: str | None = None, time_range: str = "7d"):
    leads_records = load_records(time_range=time_range)
    with get_connection() as connection:
        open_tasks = connection.execute("SELECT COUNT(*) n FROM agent_tasks WHERE status = 'open'").fetchone()["n"]
    return {
        "sources": list_sources(),
        "filter": {"source": source, "time_range": time_range},
        "leads": totals_by_type(leads_records),
        "commerce": commerce_summary(source=source, time_range=time_range),
        "reconciliation": revenue_reconciliation(source=source),
        "open_tasks": open_tasks,
    }
