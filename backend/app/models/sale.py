from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class Sale(Base, PKMixin, TimestampMixin):
    __tablename__ = "sales"

    listing_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    etsy_receipt_id: Mapped[str] = mapped_column(String(64), default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    buyer_country: Mapped[str] = mapped_column(String(64), default="")

    listing: Mapped["Listing"] = relationship(back_populates="sales")


from app.models.listing import Listing  # noqa: E402
