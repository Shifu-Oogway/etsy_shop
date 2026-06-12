from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class EventLog(Base, PKMixin, TimestampMixin):
    __tablename__ = "event_logs"

    level: Mapped[str] = mapped_column(String(16), default="INFO", index=True)
    source: Mapped[str] = mapped_column(String(120), default="", index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[dict] = mapped_column(JSON, default=dict)
