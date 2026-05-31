from __future__ import annotations

import threading
import time
from datetime import datetime

from app.database import get_connection
from app.scheduler.cron import is_due, next_run_at
from app.scheduler.runner import run_automation


class LocalScheduler:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.refresh_next_runs()
        self._thread = threading.Thread(target=self._loop, name="gyutron-local-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def refresh_next_runs(self) -> None:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, schedule_cron FROM automation_rules WHERE trigger_type = 'schedule' AND status = 'active' AND next_run_at IS NULL"
            ).fetchall()
            for row in rows:
                connection.execute("UPDATE automation_rules SET next_run_at = ? WHERE id = ?", (next_run_at(row["schedule_cron"]), row["id"]))
            connection.commit()

    def _loop(self) -> None:
        while not self._stop.wait(30):
            with get_connection() as connection:
                rows = connection.execute(
                    "SELECT id, next_run_at FROM automation_rules WHERE trigger_type = 'schedule' AND status = 'active'"
                ).fetchall()
            for row in rows:
                if is_due(row["next_run_at"], now=datetime.now()):
                    run_automation(row["id"], trigger_source="schedule")


local_scheduler = LocalScheduler()
