from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.experiment_agent import ExperimentAgent
from app.core.database import get_db
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentOut

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentOut])
async def list_experiments(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Experiment).order_by(Experiment.id.desc()).limit(limit).offset(offset))
    return rows.scalars().all()


@router.post("/design/{product_id}")
async def design_experiment(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await ExperimentAgent(db).execute(product_id=product_id)
    await db.commit()
    return dict(result)


@router.post("/{experiment_id}/conclude")
async def conclude_experiment(experiment_id: int, results: dict, db: AsyncSession = Depends(get_db)):
    agent = ExperimentAgent(db)
    result = await agent.conclude(experiment_id, results)
    if not result.ok:
        raise HTTPException(404, result.get("error", "not found"))
    await db.commit()
    return dict(result)
