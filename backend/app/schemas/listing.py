from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.listing import ListingStatus


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    etsy_listing_id: str
    status: ListingStatus
    title: str
    tags: list
    price: float
    url: str
    created_at: datetime
