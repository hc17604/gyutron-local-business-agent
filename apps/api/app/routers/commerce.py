"""Cross-source commerce overview — feeds the Owner Dashboard. Read-only.
Source filter values come from the data_sources REGISTRY, not ad-hoc strings."""
from fastapi import APIRouter

from app.database import get_connection
from app.services.commerce_metrics import commerce_summary, revenue_reconciliation
from app.services.commerce_store import list_sources
from app.services.website_metrics import load_records, totals_by_type


router = APIRouter(prefix="/commerce", tags=["commerce"])


@router.get("/overview")
def commerce_overview(source: str | None = None, time_range: str = "7d", customer_id: str | None = None):
    from app.services.customers import customer_sources

    sources = customer_sources(customer_id)
    leads_records = load_records(time_range=time_range, sources=sources)
    with get_connection() as connection:
        if sources is None:
            open_tasks = connection.execute("SELECT COUNT(*) n FROM agent_tasks WHERE status = 'open'").fetchone()["n"]
        else:
            placeholders = ", ".join("?" for _ in sources)
            open_tasks = connection.execute(
                f"SELECT COUNT(*) n FROM agent_tasks WHERE status = 'open' AND source IN ({placeholders})", sources
            ).fetchone()["n"]
    visible_sources = list_sources()
    if customer_id:
        visible_sources = [s for s in visible_sources if s.get("customer_id") == customer_id]
    return {
        "sources": visible_sources,
        "filter": {"source": source, "time_range": time_range, "customer_id": customer_id},
        "leads": totals_by_type(leads_records),
        "commerce": commerce_summary(source=source, time_range=time_range, sources=sources),
        "reconciliation": revenue_reconciliation(source=source, sources=sources),
        "open_tasks": open_tasks,
    }
