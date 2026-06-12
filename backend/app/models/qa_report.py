from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class QAReport(Base, PKMixin, TimestampMixin):
    __tablename__ = "qa_reports"

    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    checks: Mapped[dict] = mapped_column(JSON, default=dict)

    product: Mapped["Product"] = relationship(back_populates="qa_reports")


from app.models.product import Product  # noqa: E402
