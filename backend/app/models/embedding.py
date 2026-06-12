from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, EmbeddingVector
from app.models.base_mixin import PKMixin, TimestampMixin


class Embedding(Base, PKMixin, TimestampMixin):
    __tablename__ = "embeddings"

    ref_type: Mapped[str] = mapped_column(String(40), index=True)  # product | trend | listing
    ref_id: Mapped[int] = mapped_column(index=True)
    model: Mapped[str] = mapped_column(String(80), default="nomic-embed-text")
    vector: Mapped[list] = mapped_column(EmbeddingVector(768), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
