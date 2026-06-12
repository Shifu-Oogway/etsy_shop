from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductStatus, ProductType


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    product_type: ProductType
    niche: str = ""
    price: float = Field(default=4.99, ge=0.99, le=50.0)


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    niche: str | None = None
    price: float | None = Field(default=None, ge=0.99, le=50.0)
    status: ProductStatus | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    product_type: ProductType
    status: ProductStatus
    niche: str
    price: float
    file_path: str
    created_at: datetime
    updated_at: datetime
