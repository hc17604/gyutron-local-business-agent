from app.database import get_connection


def write_audit_log(
    action: str,
    target_type: str,
    *,
    target_id: str | None = None,
    risk_level: str = "low",
    input_summary: str | None = None,
    output_summary: str | None = None,
    actor: str = "local_user",
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs (
              actor, action, target_type, target_id, risk_level, input_summary, output_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (actor, action, target_type, target_id, risk_level, input_summary, output_summary),
        )
        connection.commit()
