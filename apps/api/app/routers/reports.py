from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_connection
from app.services.auth import require_min_role
from app.services.reports import generate_owner_report
from app.services.website_leads import generate_website_leads_summary


router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportPayload(BaseModel):
    language: str | None = "en"


class WebsiteLeadsPayload(BaseModel):
    connector_id: int | None = None
    language: str | None = "en"


@router.get("")
def list_reports():
    with get_connection() as connection:
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
    )
