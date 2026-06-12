"""Celery application with beat schedule for the daily pipeline."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_etsy_system",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "dispatch-db-schedules": {
        "task": "app.tasks.dispatch_schedules",
        "schedule": 60.0,  # every minute — fires DB-managed schedules
    },
    "daily-full-pipeline": {
        "task": "app.tasks.run_agent",
        "schedule": crontab(hour=6, minute=0),
        "kwargs": {"agent_name": "orchestrator", "payload": {}},
    },
    "daily-trend-scan": {
        "task": "app.tasks.run_agent",
        "schedule": crontab(hour=5, minute=30),
        "kwargs": {"agent_name": "trend", "payload": {"n": 8}},
    },
    "hourly-analytics": {
        "task": "app.tasks.run_agent",
        "schedule": crontab(minute=15),
        "kwargs": {"agent_name": "analytics", "payload": {}},
    },
}
