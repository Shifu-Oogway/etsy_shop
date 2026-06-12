from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.listing import Listing
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingOut])
async def list_listings(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Listing).order_by(Listing.id.desc()).limit(limit).offset(offset))
    return rows.scalars().all()


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(404, f"listing {listing_id} not found")
    return listing


from datetime import datetime, timezone

from pydantic import BaseModel

from app.services.etsy_client import EtsyClient


class ListingPatch(BaseModel):
    title: str | None = None
    price: float | None = None
    tags: list[str] | None = None


@router.patch("/{listing_id}")
async def patch_listing(listing_id: int, body: ListingPatch,
                        db: AsyncSession = Depends(get_db)):
    """Update a listing locally AND push the change to Etsy (or dry-run)."""
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(404, f"listing {listing_id} not found")

    result = await EtsyClient().update_listing(
        listing.etsy_listing_id,
        title=body.title, price=body.price, tags=body.tags)

    if body.title is not None:
        listing.title = body.title[:140]
    if body.price is not None:
        listing.price = float(body.price)
    if body.tags is not None:
        listing.tags = body.tags[:13]
    await db.commit()
    return {"id": listing.id, "etsy_result": result}


@router.post("/{listing_id}/refresh-stats")
async def refresh_stats(listing_id: int, db: AsyncSession = Depends(get_db)):
    """Pull fresh view/favorite stats from Etsy for one listing."""
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(404, f"listing {listing_id} not found")
    stats = await EtsyClient().get_listing_stats(listing.etsy_listing_id)
    listing.stats = {**stats,
                     "last_synced": datetime.now(timezone.utc).isoformat()}
    await db.commit()
    return {"id": listing.id, "stats": listing.stats}
