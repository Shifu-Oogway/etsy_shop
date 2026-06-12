from __future__ import annotations

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class SEOMetadata(Base, PKMixin, TimestampMixin):
    __tablename__ = "seo_metadata"

    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    optimized_title: Mapped[str] = mapped_column(String(140), default="")
    optimized_description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    keywords: Mapped[list] = mapped_column(JSON, default=list)

    product: Mapped["Product"] = relationship(back_populates="seo_entries")


from app.models.product import Product  # noqa: E402
