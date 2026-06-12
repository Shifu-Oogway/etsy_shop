from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class TaskStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failure = "failure"


class TaskRun(Base, PKMixin, TimestampMixin):
    __tablename__ = "task_runs"

    task_name: Mapped[str] = mapped_column(String(160), index=True)
    celery_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.queued)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str] = mapped_column(Text, default="")  # full traceback — never suppressed
