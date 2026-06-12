from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class Schedule(Base, PKMixin, TimestampMixin):
    __tablename__ = "schedules"

    name: Mapped[str] = mapped_column(String(160), unique=True)
    cron: Mapped[str] = mapped_column(String(64), default="0 6 * * *")
    task_name: Mapped[str] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
