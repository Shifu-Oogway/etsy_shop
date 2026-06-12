"""Async SQLAlchemy engine/session plus a portable vector column type.

`EmbeddingVector` compiles to pgvector's VECTOR on PostgreSQL and to JSON on
SQLite, so the full model graph (and the test suite) works without a running
Postgres instance while production keeps real vector search.
"""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from sqlalchemy import JSON, types
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

try:  # pgvector is required in production, optional for sqlite-based tests
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    Vector = None


class Base(DeclarativeBase):
    pass


class EmbeddingVector(types.TypeDecorator):
    """VECTOR(dim) on PostgreSQL, JSON list elsewhere."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and Vector is not None:
            return value
        return list(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return list(value)


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().normalized_database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
