from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schedule import Schedule

router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleBody(BaseModel):
    name: str
    cron: str = "0 6 * * *"
    task_name: str
    enabled: bool = True


@router.get("")
async def list_schedules(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Schedule).order_by(Schedule.id))
    return [{"id": s.id, "name": s.name, "cron": s.cron,
             "task_name": s.task_name, "enabled": s.enabled} for s in rows.scalars()]


@router.post("", status_code=201)
async def create_schedule(body: ScheduleBody, db: AsyncSession = Depends(get_db)):
    schedule = Schedule(**body.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return {"id": schedule.id, "name": schedule.name}


@router.patch("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(404, f"schedule {schedule_id} not found")
    schedule.enabled = not schedule.enabled
    await db.commit()
    return {"id": schedule.id, "enabled": schedule.enabled}


@router.patch("/{schedule_id}")
async def update_schedule(schedule_id: int, body: ScheduleBody,
                          db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(404, f"schedule {schedule_id} not found")
    schedule.name = body.name
    schedule.cron = body.cron
    schedule.task_name = body.task_name
    schedule.enabled = body.enabled
    await db.commit()
    return {"id": schedule.id, "name": schedule.name, "cron": schedule.cron,
            "task_name": schedule.task_name, "enabled": schedule.enabled}


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(404, f"schedule {schedule_id} not found")
    await db.delete(schedule)
    await db.commit()
