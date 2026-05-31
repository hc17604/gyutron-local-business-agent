from __future__ import annotations

from datetime import datetime, timedelta


WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def next_run_at(schedule: str | None, *, now: datetime | None = None) -> str | None:
    if not schedule:
        return None
    now = now or datetime.now()
    parts = schedule.split(":")
    try:
        if parts[0] == "daily" and len(parts) == 3:
            hour, minute = int(parts[1]), int(parts[2])
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate.isoformat(timespec="seconds")
        if parts[0] == "weekly" and len(parts) == 4:
            weekday = WEEKDAYS[parts[1].lower()]
            hour, minute = int(parts[2]), int(parts[3])
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days = (weekday - now.weekday()) % 7
            candidate += timedelta(days=days)
            if candidate <= now:
                candidate += timedelta(days=7)
            return candidate.isoformat(timespec="seconds")
    except (ValueError, KeyError):
        return None
    return None


def is_due(next_run: str | None, *, now: datetime | None = None) -> bool:
    if not next_run:
        return False
    now = now or datetime.now()
    try:
        return datetime.fromisoformat(next_run) <= now
    except ValueError:
        return False
