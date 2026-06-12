from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.publisher_agent import PublisherAgent
from app.core.database import get_db

router = APIRouter(prefix="/publisher", tags=["publisher"])


@router.post("/publish/{product_id}")
async def publish(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await PublisherAgent(db).execute(product_id=product_id)
    if not result.ok:
        raise HTTPException(409, result.get("error", "publish failed"))
    await db.commit()
    return dict(result)
