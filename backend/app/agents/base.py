"""Base class shared by all nine agents."""
from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import EventLog
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AgentResult(dict):
    @property
    def ok(self) -> bool:
        return bool(self.get("ok", False))


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, db: AsyncSession, llm: OllamaClient | None = None) -> None:
        self.db = db
        self.llm = llm or OllamaClient()

    @abstractmethod
    async def run(self, **kwargs: Any) -> AgentResult: ...

    async def execute(self, **kwargs: Any) -> AgentResult:
        """Run with full error capture. Tracebacks are stored, never swallowed."""
        try:
            result = await self.run(**kwargs)
            await self._log("INFO", f"{self.name} completed", {"keys": sorted(result.keys())})
            return result
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("%s failed: %s\n%s", self.name, exc, tb)
            await self._log("ERROR", f"{self.name} failed: {exc}", {"traceback": tb})
            return AgentResult(ok=False, error=str(exc), traceback=tb)

    async def _log(self, level: str, message: str, context: dict | None = None) -> None:
        self.db.add(EventLog(level=level, source=f"agent.{self.name}",
                             message=message, context=context or {}))
        await self.db.flush()
