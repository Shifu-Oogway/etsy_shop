from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENT_REGISTRY
from app.core.database import get_db
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents():
    return {"agents": sorted(AGENT_REGISTRY.keys())}


@router.post("/{agent_name}/run")
async def run_agent(agent_name: str, payload: dict | None = None,
                    db: AsyncSession = Depends(get_db)):
    """Run an agent synchronously (useful for debugging from the dashboard)."""
    agent_cls = AGENT_REGISTRY.get(agent_name)
    if agent_cls is None:
        raise HTTPException(404, f"unknown agent '{agent_name}'")
    result = await agent_cls(db).execute(**(payload or {}))
    await db.commit()
    return dict(result)


@router.post("/{agent_name}/enqueue")
async def enqueue_agent(agent_name: str, payload: dict | None = None):
    """Run an agent asynchronously via Celery."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(404, f"unknown agent '{agent_name}'")
    task = celery_app.send_task("app.tasks.run_agent",
                                kwargs={"agent_name": agent_name, "payload": payload or {}})
    return {"task_id": task.id, "agent": agent_name, "status": "queued"}
