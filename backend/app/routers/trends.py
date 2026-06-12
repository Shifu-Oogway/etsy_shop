from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.trend_agent import TrendAgent
from app.core.database import get_db
from app.models.trend import Trend
from app.schemas.trend import TrendOut

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=list[TrendOut])
async def list_trends(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Trend).order_by(Trend.score.desc()).limit(limit).offset(offset))
    return rows.scalars().all()


@router.post("/discover")
async def discover_trends(n: int = 5, db: AsyncSession = Depends(get_db)):
    result = await TrendAgent(db).execute(n=n)
    await db.commit()
    return dict(result)
