from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class ExperimentStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    aborted = "aborted"


class Experiment(Base, PKMixin, TimestampMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ExperimentStatus] = mapped_column(Enum(ExperimentStatus), default=ExperimentStatus.running)
    variants: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
