"""Boss Decision Center + health check API (Phase 6). Read-only aggregation —
everything is customer-scoped; demo customers never see real data and vice versa."""
from fastapi import APIRouter

from app.services import website_metrics as metrics
from app.services.analyst import action_cards
from app.services.commerce_metrics import commerce_summary, paid_not_fulfilled, revenue_reconciliation
from app.services.customers import customer_sources, get_customer
from app.services.health import check_customer_health
from app.services.rules_engine import report_flags


router = APIRouter(tags=["decision-center"])


@router.get("/health-check")
def health_check(customer_id: str = "gyutron"):
    return check_customer_health(customer_id)


@router.get("/decision-center")
def decision_center(customer_id: str = "gyutron", language: str | None = None):
    customer = get_customer(customer_id) or {}
    language = language or customer.get("report_language") or "en"
    sources = customer_sources(customer_id)

    today = metrics.load_records(sources=sources, time_range="today")
    week = metrics.load_records(sources=sources, time_range="7d")
    today_totals = metrics.totals_by_type(today)
    com_today = commerce_summary(time_range="today", sources=sources)
    com_week = commerce_summary(time_range="7d", sources=sources)
    flags = report_flags()
    health = check_customer_health(customer_id)
    cards = action_cards(customer_id, language)

    high_cards = [c for c in cards if c["priority"] == "high"]
    risk_watch = [
        {"kind": c["check"], "severity": c["severity"], "detail": c["detail"], "count": c["count"]}
        for c in health["checks"]
    ]
    stale_paid = paid_not_fulfilled(sources=sources)
    if stale_paid:
        risk_watch.append({"kind": "paid_not_fulfilled", "severity": "warning", "count": len(stale_paid),
                           "detail": f"{len(stale_paid)} paid order(s) not fulfilled"})
    rec = revenue_reconciliation(sources=sources)
    if rec["unmatched"]:
        risk_watch.append({"kind": "payment_unmatched", "severity": "warning", "count": rec["unmatched"],
                           "detail": f"{rec['unmatched']} paid payment(s) match no order"})

    opportunity_radar = {
        "repeat_inquirers": flags.get("repeat_inquirers", []),
        "rfq_by_country_7d": dict(metrics.count_by(week, "country", types=("rfq",)).most_common(5)),
        "rfq_by_category_7d": dict(metrics.count_by(week, "product_category", types=("rfq",)).most_common(5)),
        "top_products_7d": com_week.get("top_products", {}),
        "cart_events_7d": com_week.get("cart_events", {}),
    }

    return {
        "customer_id": customer_id,
        "language": language,
        "health_status": health["status"],
        "today_brief": {
            "new_leads": today_totals,
            "new_orders": com_today.get("orders", 0),
            "revenue_today": com_today.get("revenue_base", 0),
            "high_priority_actions": len(high_cards),
            "anomalies": sum(1 for c in health["checks"] if c["severity"] == "critical"),
            "suggested": [c["action"] for c in cards[:3]],
        },
        "priority_queue": high_cards or cards[:5],
        "opportunity_radar": opportunity_radar,
        "risk_watch": risk_watch,
        "action_cards": cards,
    }
