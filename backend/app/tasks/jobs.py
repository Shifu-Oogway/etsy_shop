"""Celery jobs. Celery is sync, the app is async — each job runs its own event
loop and records a TaskRun row with status and FULL error output (tracebacks
are stored, not suppressed)."""
from __future__ import annotations

import asyncio
import logging
import traceback
from typing import Any

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_agent_async(agent_name: str, payload: dict[str, Any],
                           celery_id: str) -> dict[str, Any]:
    # Imports happen inside so the worker boots even if the API package changes.
    from app.agents import AGENT_REGISTRY
    from app.core.database import get_session_factory
    from app.models.task_run import TaskRun, TaskStatus

    factory = get_session_factory()
    async with factory() as db:
        run = TaskRun(task_name=f"agent.{agent_name}", celery_id=celery_id,
                      status=TaskStatus.running, payload=payload)
        db.add(run)
        await db.commit()

        agent_cls = AGENT_REGISTRY.get(agent_name)
        if agent_cls is None:
            run.status = TaskStatus.failure
            run.error = f"unknown agent '{agent_name}'"
            await db.commit()
            return {"ok": False, "error": run.error}

        try:
            result = await agent_cls(db).execute(**payload)
            run.status = TaskStatus.success if result.ok else TaskStatus.failure
            run.error = result.get("traceback", "") or result.get("error", "") if not result.ok else ""
            await db.commit()
            return dict(result)
        except Exception as exc:
            run.status = TaskStatus.failure
            run.error = traceback.format_exc()
            await db.commit()
            logger.error("Task %s failed:\n%s", agent_name, run.error)
            raise


@celery_app.task(name="app.tasks.run_agent", bind=True, max_retries=2,
                 default_retry_delay=60)
def run_agent(self, agent_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return asyncio.run(_run_agent_async(agent_name, payload or {}, self.request.id or ""))


async def _dispatch_schedules_async() -> dict[str, Any]:
    """Runs every minute via beat. Fires any enabled DB schedule whose cron
    matches the current minute (and hasn't already run this minute)."""
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.core.database import get_session_factory
    from app.models.schedule import Schedule
    from app.services.cron_match import cron_matches

    now = datetime.now(timezone.utc)
    fired: list[str] = []

    factory = get_session_factory()
    async with factory() as db:
        rows = await db.execute(select(Schedule).where(Schedule.enabled == True))  # noqa: E712
        for schedule in rows.scalars():
            if not cron_matches(schedule.cron, now):
                continue
            # Skip if already fired this minute
            if (schedule.last_run_at
                    and schedule.last_run_at.replace(second=0, microsecond=0)
                    == now.replace(second=0, microsecond=0, tzinfo=schedule.last_run_at.tzinfo)):
                continue
            celery_app.send_task(
                "app.tasks.run_agent",
                kwargs={"agent_name": schedule.task_name, "payload": {}})
            schedule.last_run_at = now
            fired.append(schedule.name)
        await db.commit()

    if fired:
        logger.info("schedule dispatcher fired: %s", fired)
    return {"fired": fired, "checked_at": now.isoformat()}


@celery_app.task(name="app.tasks.dispatch_schedules")
def dispatch_schedules() -> dict[str, Any]:
    return asyncio.run(_dispatch_schedules_async())
