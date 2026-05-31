import json

from app.database import get_connection
from app.services.audit import write_audit_log


def generate_owner_report(source: str = "manual", connector_id: int | None = None) -> dict:
    with get_connection() as connection:
        uploads = connection.execute(
            "SELECT * FROM uploads ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        rules = connection.execute("SELECT * FROM business_rules WHERE is_active = 1 ORDER BY priority ASC LIMIT 10").fetchall()
        open_alerts = connection.execute("SELECT * FROM alerts WHERE status = 'open' ORDER BY created_at DESC LIMIT 5").fetchall()

        total_files = len(uploads)
        total_size = sum(int(row["file_size"] or 0) for row in uploads)
        report_title = "Owner Daily Report"
        content = f"""# Owner Daily Report

## Owner Summary

GyuTron scanned {total_files} recent local data file(s). Total imported file size is {total_size} bytes. The report was generated locally from connector data, business rules, and alert status.

## Core Data Changes

- Recent files: {", ".join(row["original_filename"] for row in uploads[:5]) or "No imported files yet."}
- Active rules referenced: {len(rules)}
- Open alerts: {len(open_alerts)}

## Anomaly Alerts

{format_alerts(open_alerts)}

## Sales Follow-up Tasks

- Review newly imported inquiry/order files.
- Check high-priority countries and overdue follow-ups.
- Confirm inventory-sensitive products before sending quotes.

## Next Suggestions

- Keep Local Folder Connector active for daily imports.
- Run this report every morning at 09:00.
- Resolve open alerts after the owner review.
"""
        cursor = connection.execute(
            """
            INSERT INTO reports (
              title, status, content_markdown, summary_json, rules_snapshot_json, model_snapshot_json
            ) VALUES (?, 'ready', ?, ?, ?, ?)
            """,
            (
                report_title,
                content,
                json.dumps({"source": source, "connector_id": connector_id, "files": total_files}, ensure_ascii=False),
                json.dumps([dict(row) for row in rules], ensure_ascii=False),
                json.dumps({"mode": "local_deterministic"}, ensure_ascii=False),
            ),
        )
        report_id = cursor.lastrowid
        connection.commit()

    write_audit_log(
        "report_generated",
        "report",
        target_id=str(report_id),
        risk_level="low",
        input_summary=f"source={source}, connector_id={connector_id}",
        output_summary=f"Owner report generated with {total_files} files.",
    )
    return {"report_id": report_id, "title": report_title, "summary": f"Generated from {total_files} recent local file(s)."}


def format_alerts(alerts) -> str:
    if not alerts:
        return "- No open alerts at generation time."
    return "\n".join(f"- {row['severity'].upper()}: {row['title']} - {row['description']}" for row in alerts)
