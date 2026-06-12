from __future__ import annotations

import enum

from sqlalchemy import JSON, BigInteger, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class ListingStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    inactive = "inactive"
    failed = "failed"


class Listing(Base, PKMixin, TimestampMixin):
    __tablename__ = "listings"

    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.pending)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    price: Mapped[float] = mapped_column(Float, default=4.99)
    url: Mapped[str] = mapped_column(String(512), default="")
    stats: Mapped[dict] = mapped_column(JSON, default=dict)  # views, favorites, last_synced

    product: Mapped["Product"] = relationship(back_populates="listings")
    sales: Mapped[list["Sale"]] = relationship(back_populates="listing", cascade="all, delete-orphan")


from app.models.product import Product  # noqa: E402
from app.models.sale import Sale  # noqa: E402
