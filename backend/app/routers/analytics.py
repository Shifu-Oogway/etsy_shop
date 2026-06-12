from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.analytics_agent import AnalyticsAgent
from app.core.database import get_db
from app.schemas.analytics import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(db: AsyncSession = Depends(get_db)):
    result = await AnalyticsAgent(db).execute()
    return AnalyticsSummary(totals=result.get("totals", {}),
                            products_by_status=result.get("products_by_status", {}))
