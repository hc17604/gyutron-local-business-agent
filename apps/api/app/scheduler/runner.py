import json

from app.connectors.registry import get_connector
from app.database import get_connection
from app.scheduler.cron import next_run_at
from app.services.audit import write_audit_log
from app.services.reports import generate_owner_report


def run_automation(rule_id: int, *, trigger_source: str = "manual") -> dict:
    with get_connection() as connection:
        rule = connection.execute("SELECT * FROM automation_rules WHERE id = ?", (rule_id,)).fetchone()
        if rule is None:
            raise ValueError("Automation rule not found.")
        cursor = connection.execute(
            """
            INSERT INTO automation_runs (automation_rule_id, status, trigger_source, started_at)
            VALUES (?, 'running', ?, CURRENT_TIMESTAMP)
            """,
            (rule_id, trigger_source),
        )
        run_id = cursor.lastrowid
        connection.commit()

    try:
        result = execute_action(rule)
        status = "completed"
        error = None
    except Exception as exc:
        result = {"summary": f"Automation failed: {type(exc).__name__}", "error": type(exc).__name__}
        status = "failed"
        error = type(exc).__name__

    next_at = next_run_at(rule["schedule_cron"])
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE automation_runs
            SET status = ?, result_summary = ?, result_json = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, result.get("summary"), json.dumps(result, ensure_ascii=False), error, run_id),
        )
        connection.execute(
            """
            UPDATE automation_rules
            SET last_run_at = CURRENT_TIMESTAMP, next_run_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (next_at, rule_id),
        )
        connection.commit()

    write_audit_log(
        "automation_run",
        "automation_rule",
        target_id=str(rule_id),
        risk_level="medium",
        input_summary=f"trigger={trigger_source}, action={rule['action_type']}",
        output_summary=result.get("summary"),
    )
    return {"automation_run_id": run_id, "status": status, **result}


def execute_action(rule) -> dict:
    action_config = json.loads(rule["action_config_json"] or "{}")
    action_type = rule["action_type"]
    if action_type == "generate_report":
        report = generate_owner_report(source="scheduled" if rule["trigger_type"] == "schedule" else "automation", connector_id=action_config.get("connector_id"))
        return {"summary": report["summary"], "report_id": report["report_id"]}
    if action_type == "scan_connector":
        connector_id = int(action_config["connector_id"])
        return run_connector_sync(connector_id)
    if action_type == "create_alert":
        return create_alert_from_rule(action_config)
    if action_type == "run_agent_analysis":
        return {"summary": "Agent analysis action is queued for a future MVP iteration."}
    return {"summary": f"Unknown action: {action_type}"}


def run_connector_sync(connector_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM data_connectors WHERE id = ?", (connector_id,)).fetchone()
    if row is None:
        raise ValueError("Connector not found.")
    connector = get_connector(row["connector_type"])
    result = connector.sync(connector_id, json.loads(row["config_json"] or "{}"), {}, sync_type="scheduled")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO sync_jobs (
              connector_id, status, sync_type, records_found, records_imported, started_at, completed_at
            ) VALUES (?, 'completed', 'scheduled', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (connector_id, result.records_found, result.records_imported),
        )
        connection.execute(
            "UPDATE data_connectors SET last_sync_at = CURRENT_TIMESTAMP, last_sync_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result.summary, connector_id),
        )
        connection.commit()
    return {"summary": result.summary, "records_found": result.records_found, "records_imported": result.records_imported}


def create_alert_from_rule(action_config: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (title, description, severity, source_type, source_id)
            VALUES (?, ?, ?, 'automation', ?)
            """,
            (
                action_config.get("title", "Automation alert"),
                action_config.get("description", "Created by automation."),
                action_config.get("severity", "medium"),
                str(action_config.get("source_id", "")),
            ),
        )
        connection.commit()
    return {"summary": "Alert created.", "alert_id": cursor.lastrowid}
