"""Customers (workspace tenants) — list + demo reset (Phase 5)."""
from fastapi import APIRouter, Depends, HTTPException

from app.services.auth import require_min_role
from app.services.customers import list_customers, reset_demo_customer


router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def customers():
    return {"customers": list_customers()}


@router.post("/{customer_id}/demo-reset")
def demo_reset(customer_id: str, _: dict = Depends(require_min_role("admin"))):
    """Wipe a DEMO customer's mock data so the demo can be re-seeded. Refuses
    real customers — real data is never touched by this endpoint."""
    try:
        return reset_demo_customer(customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
