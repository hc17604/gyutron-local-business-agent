from fastapi import APIRouter

from app.database import get_connection
from app.services.reports import generate_owner_report


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT 100").fetchall()
    return {"reports": [dict(row) for row in rows]}


@router.post("/generate-owner-report")
def generate_owner_report_endpoint():
    return generate_owner_report(source="manual")
