from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_connection
from app.services.auth import require_min_role
from app.services.reports import generate_owner_report
from app.services.reports_engine import generate_daily_owner_report, generate_opportunities_report, generate_weekly_pipeline_report
from app.services.website_leads import generate_website_leads_summary


router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportPayload(BaseModel):
    language: str | None = "en"
    customer_id: str | None = None


class WebsiteLeadsPayload(BaseModel):
    connector_id: int | None = None
    language: str | None = None
    time_range: str | None = "all"
    customer_id: str | None = None


@router.get("")
def list_reports(customer_id: str | None = None):
    with get_connection() as connection:
        if customer_id:
            rows = connection.execute(
                "SELECT * FROM reports WHERE customer_id = ? ORDER BY created_at DESC LIMIT 100", (customer_id,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT 100").fetchall()
    return {"reports": [dict(row) for row in rows]}


@router.post("/generate-owner-report")
def generate_owner_report_endpoint(payload: GenerateReportPayload | None = None, _: dict = Depends(require_min_role("operator"))):
    return generate_owner_report(source="manual", language=(payload.language if payload else "en"))


@router.post("/website-leads-summary")
def website_leads_summary_endpoint(payload: WebsiteLeadsPayload | None = None, _: dict = Depends(require_min_role("operator"))):
    return generate_website_leads_summary(
        connector_id=(payload.connector_id if payload else None),
        language=((payload.language if payload else None) or "en"),
        time_range=((payload.time_range if payload else None) or "all"),
    )


@router.post("/daily-owner")
def daily_owner_endpoint(payload: WebsiteLeadsPayload | None = None, _: dict = Depends(require_min_role("operator"))):
    return generate_daily_owner_report(
        language=(payload.language if payload else None),
        connector_id=(payload.connector_id if payload else None),
        customer_id=(payload.customer_id if payload else None),
    )


@router.post("/weekly-pipeline")
def weekly_pipeline_endpoint(payload: WebsiteLeadsPayload | None = None, _: dict = Depends(require_min_role("operator"))):
    return generate_weekly_pipeline_report(
        language=((payload.language if payload else None) or "en"),
        connector_id=(payload.connector_id if payload else None),
    )


@router.post("/opportunities")
def opportunities_endpoint(payload: WebsiteLeadsPayload | None = None, _: dict = Depends(require_min_role("operator"))):
    return generate_opportunities_report(
        language=((payload.language if payload else None) or "en"),
        connector_id=(payload.connector_id if payload else None),
    )
