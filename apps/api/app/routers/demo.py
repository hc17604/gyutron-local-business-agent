from fastapi import APIRouter, Depends

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services.auth import require_min_role
from app.services.reports import generate_owner_report


router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/status")
def demo_status():
    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM uploads WHERE status = 'demo'").fetchone()["count"]
    return {"loaded": count > 0, "demo_uploads": count}


@router.post("/load")
def load_demo(_: dict = Depends(require_min_role("admin"))):
    files = [
        ("inquiry", "alibaba_inquiries_demo.csv", 42),
        ("inventory", "erp_inventory_demo.xlsx", 128),
        ("order", "shopee_orders_demo.csv", 86),
        ("order", "amazon_orders_demo.csv", 73),
        ("product", "product_catalog_demo.xlsx", 36),
    ]
    rules = [
        ("Brazil customer priority", "Brazil customers should be high priority.", "customer", 10),
        ("24h no follow-up", "Inquiries without follow-up after 24 hours should alert.", "inquiry", 20),
        ("Industrial camera focus", "Industrial cameras, barcode scanners, AGV parts, sensors, and controllers are strategic products.", "product", 30),
    ]
    alerts = [
        ("High-value customer pending", "Brazil inquiry for industrial camera needs owner review.", "high"),
        ("Inventory low", "IC-420 industrial camera stock is below threshold.", "medium"),
    ]
    with get_connection() as connection:
        connection.execute("DELETE FROM uploads WHERE status = 'demo'")
        for data_type, name, rows in files:
            connection.execute(
                "INSERT INTO uploads (data_type, original_filename, stored_path, file_size, status) VALUES (?, ?, ?, ?, 'demo')",
                (data_type, name, f"demo/{name}", rows * 100),
            )
        for name, description, data_type, priority in rules:
            connection.execute(
                "INSERT INTO business_rules (name, description, data_type, priority, is_active) VALUES (?, ?, ?, ?, 1)",
                (name, description, data_type, priority),
            )
        for title, description, severity in alerts:
            connection.execute(
                "INSERT INTO alerts (title, description, severity, source_type, source_id) VALUES (?, ?, ?, 'demo', 'demo')",
                (title, description, severity),
            )
        connection.commit()
    report = generate_owner_report(source="demo")
    write_audit_log("demo_data_loaded", "demo", risk_level="medium", output_summary=report["summary"])
    return {"status": "loaded", "report": report}


@router.post("/reset")
def reset_demo(_: dict = Depends(require_min_role("admin"))):
    with get_connection() as connection:
        connection.execute("DELETE FROM uploads WHERE status = 'demo'")
        connection.execute("DELETE FROM alerts WHERE source_type = 'demo'")
        connection.commit()
    write_audit_log("demo_data_reset", "demo", risk_level="medium")
    return {"status": "reset"}
