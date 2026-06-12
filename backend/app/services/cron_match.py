"""Minimal 5-field cron matcher: minute hour dom month dow.

Supports: "*", "*/n", "n", "n,m,o", and ranges "a-b" per field.
Enough for dashboard-managed schedules without a croniter dependency.
"""
from __future__ import annotations

from datetime import datetime


def _field_matches(field: str, value: int) -> bool:
    field = field.strip()
    if field == "*":
        return True
    for part in field.split(","):
        part = part.strip()
        if part.startswith("*/"):
            try:
                step = int(part[2:])
                if step > 0 and value % step == 0:
                    return True
            except ValueError:
                continue
        elif "-" in part:
            try:
                a, b = part.split("-", 1)
                if int(a) <= value <= int(b):
                    return True
            except ValueError:
                continue
        else:
            try:
                if int(part) == value:
                    return True
            except ValueError:
                continue
    return False


def cron_matches(cron: str, now: datetime) -> bool:
    parts = cron.split()
    if len(parts) != 5:
        return False
    minute, hour, dom, month, dow = parts
    return (_field_matches(minute, now.minute)
            and _field_matches(hour, now.hour)
            and _field_matches(dom, now.day)
            and _field_matches(month, now.month)
            and _field_matches(dow, now.weekday()))
