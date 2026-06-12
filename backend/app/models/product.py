from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixin import PKMixin, TimestampMixin


class ProductType(str, enum.Enum):
    pdf_planner = "pdf_planner"
    excel_template = "excel_template"
    notion_template = "notion_template"


class ProductStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    qa_passed = "qa_passed"
    qa_failed = "qa_failed"
    published = "published"
    archived = "archived"


class Product(Base, PKMixin, TimestampMixin):
    __tablename__ = "products"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType), nullable=False)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.draft, index=True)
    niche: Mapped[str] = mapped_column(String(120), default="", index=True)
    price: Mapped[float] = mapped_column(Float, default=4.99)
    file_path: Mapped[str] = mapped_column(String(512), default="")
    spec: Mapped[dict] = mapped_column(JSON, default=dict)

    # one-to-many: a product has many listings over time (A/B variants, relists).
    # `uselist=False` must NOT be used here — that silently breaks the model.
    listings: Mapped[list["Listing"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    qa_reports: Mapped[list["QAReport"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    seo_entries: Mapped[list["SEOMetadata"]] = relationship(back_populates="product", cascade="all, delete-orphan")


from app.models.listing import Listing  # noqa: E402
from app.models.qa_report import QAReport  # noqa: E402
from app.models.seo import SEOMetadata  # noqa: E402
