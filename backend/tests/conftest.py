"""Test fixtures. The suite runs against in-memory SQLite (EmbeddingVector
falls back to JSON) and a fake AI client, so it needs no services."""
from __future__ import annotations

import asyncio
import json
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ETSY_DRY_RUN", "true")
os.environ.setdefault("NIM_API_KEY", "")  # ensure NIM is disabled in tests

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
import app.models  # noqa: F401


class FakeOllama:
    """Deterministic stand-in for AIClient / OllamaClient with canned JSON."""

    model = "fake"

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        return "ok"

    async def generate_json(self, prompt: str, system: str = "", temperature: float = 0.3):
        p = prompt.lower()
        if "niches" in p or "opportunities" in p:
            return [{"keyword": f"budget planner {i}", "niche": "finance",
                     "score": 0.9 - i * 0.1, "rationale": "test"} for i in range(3)]
        if "product concept" in p or "design one" in p:
            return {"title": "2026 Budget Planner", "description": "A " + "very " * 12 + "useful planner.",
                    "product_type": "pdf_planner", "price": 6.99}
        if "page structure" in p:
            return {"title": "2026 Budget Planner",
                    "pages": [{"title": "Monthly Budget", "sections": ["Income", "Expenses"]},
                              {"title": "Savings", "sections": ["Goals"]}]}
        if "excel template" in p:
            return {"title": "Tracker", "sheets": [{"name": "Data", "headers": ["Date", "Amount"]}]}
        if "notion template" in p:
            return {"title": "Hub", "blocks": [{"heading": "Start", "content": "Welcome"}]}
        if "optimize" in p:
            return {"title": "2026 Budget Planner | Printable PDF",
                    "description": "Optimized description with plenty of relevant detail for buyers.",
                    "tags": [f"tag{i}" for i in range(13)], "keywords": ["budget", "planner"]}
        if "review this etsy listing" in p:
            return {"score": 0.95, "issues": []}
        if "a/b experiment" in p:
            return {"name": "price-test", "hypothesis": "lower price converts better",
                    "variant_a": {"title": "A", "price": 5.99},
                    "variant_b": {"title": "B", "price": 7.99}}
        return {}

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def health(self):
        # Support both old (bool) and new (dict) callers
        return {
            "active_backend": "ollama",
            "nim":    {"available": False, "healthy": False, "model": ""},
            "ollama": {"healthy": True, "model": "fake"},
        }


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def llm():
    return FakeOllama()
