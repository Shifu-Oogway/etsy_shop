from __future__ import annotations

from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class Trend(Base, PKMixin, TimestampMixin):
    __tablename__ = "trends"

    keyword: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    niche: Mapped[str] = mapped_column(String(120), default="", index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(64), default="ollama")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
