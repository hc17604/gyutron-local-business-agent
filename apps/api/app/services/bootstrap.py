"""Phase-3 startup defaults: rule state + the two default automations.

Idempotent (runs every startup). Automations are seeded only when a
gyutron_website connector exists — they are matched by name, so the owner can
edit/pause them freely without them being recreated differently.
"""
from app.database import get_connection
from app.scheduler.cron import next_run_at
from app.services.rules_engine import ensure_rule_state


DEFAULT_AUTOMATIONS = [
    {
        "name": "Website auto-sync",
        "description": "Pull new website data (incremental) and run the business rules.",
        "trigger_type": "schedule",
        "schedule_cron": "every:15",
        "action_type": "connector_sync",
    },
    {
        "name": "Daily owner report",
        "description": "Generate the bilingual daily owner report every morning.",
        "trigger_type": "schedule",
        "schedule_cron": "daily:08:00",
        "action_type": "generate_daily_owner_report",
    },
]


def ensure_phase3_defaults() -> None:
    ensure_rule_state()
    from app.services.customers import ensure_customers

    ensure_customers()
    with get_connection() as connection:
        connector = connection.execute(
            "SELECT id FROM data_connectors WHERE connector_type = 'gyutron_website' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if connector is None:
            return
        for auto in DEFAULT_AUTOMATIONS:
            exists = connection.execute("SELECT id FROM automation_rules WHERE name = ?", (auto["name"],)).fetchone()
            if exists:
                continue
            connection.execute(
                """
                INSERT INTO automation_rules (name, description, trigger_type, schedule_cron, action_type, action_config_json, status, next_run_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                """,
                (
                    auto["name"],
                    auto["description"],
                    auto["trigger_type"],
                    auto["schedule_cron"],
                    auto["action_type"],
                    '{"connector_id": %d}' % connector["id"],
                    next_run_at(auto["schedule_cron"]),
                ),
            )
        connection.commit()
