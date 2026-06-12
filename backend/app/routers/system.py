from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.models.event_log import EventLog
from app.services.ai_client import AIClient

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Liveness + dependency check. Failures are reported, never hidden."""
    checks: dict = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    ai_health = await AIClient().health()
    checks["ai"] = ai_health          # full NIM + Ollama status
    checks["active_ai_backend"] = ai_health["active_backend"]

    settings = get_settings()
    checks["etsy_dry_run"] = settings.etsy_dry_run
    ok = checks["database"] is True
    return {"status": "ok" if ok else "degraded", "checks": checks,
            "environment": settings.environment}


@router.get("/events")
async def events(limit: int = 100, level: str | None = None,
                 db: AsyncSession = Depends(get_db)):
    q = select(EventLog).order_by(EventLog.id.desc()).limit(limit)
    if level:
        q = q.where(EventLog.level == level.upper())
    rows = await db.execute(q)
    return [{"id": e.id, "level": e.level, "source": e.source, "message": e.message,
             "context": e.context, "created_at": e.created_at.isoformat()} for e in rows.scalars()]


import asyncio
import json

from fastapi.responses import StreamingResponse

from app.core.database import get_session_factory


@router.get("/events/stream")
async def events_stream(last_id: int = 0):
    """Server-Sent Events — pushes new event_log rows as they appear.
    The dashboard uses this for a live activity feed during pipeline runs."""

    async def generate():
        cursor = last_id
        factory = get_session_factory()
        # initial snapshot marker
        yield f"event: hello\ndata: {json.dumps({'cursor': cursor})}\n\n"
        for _ in range(1800):  # ~1 hour max per connection at 2s polls
            try:
                async with factory() as db:
                    rows = await db.execute(
                        select(EventLog).where(EventLog.id > cursor)
                        .order_by(EventLog.id).limit(50))
                    events = rows.scalars().all()
                for e in events:
                    cursor = e.id
                    payload = {"id": e.id, "level": e.level, "source": e.source,
                               "message": e.message,
                               "created_at": e.created_at.isoformat()}
                    yield f"data: {json.dumps(payload)}\n\n"
                if not events:
                    yield ": keepalive\n\n"
            except asyncio.CancelledError:
                break
            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
