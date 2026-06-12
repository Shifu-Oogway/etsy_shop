"""Application configuration.

All settings come from environment variables (or .env). Defaults are safe for
local development. IMPORTANT (institutional knowledge): the async SQLAlchemy /
Alembic stack requires the `postgresql+asyncpg://` scheme — a plain
`postgresql://` URL will fail at runtime, and that failure is easy to miss if
startup output is suppressed. `normalized_database_url` repairs this
automatically and logs a warning instead of failing silently.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "AI Etsy System"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://etsy:etsy@localhost:5432/etsy"
    sync_database_url: str = ""  # derived if empty (used by Alembic offline / Celery)

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # --- Dashboard auth (empty = disabled) ---
    dashboard_api_key: str = ""

    # --- NVIDIA NIM (primary AI backend) ---
    # Accepts either NIM_API_KEY or NVIDIA_API_KEY (both are checked)
    nim_api_key: str = ""
    nvidia_api_key: str = ""                                      # alias used by NVIDIA's own docs
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nim_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # --- Ollama (fallback AI backend) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embedding_model: str = "nomic-embed-text"

    # --- Shared AI settings ---
    ai_timeout_seconds: float = 120.0
    ai_max_retries: int = 3

    # Legacy aliases so old env vars still work
    @property
    def ollama_timeout_seconds(self) -> float:
        return self.ai_timeout_seconds

    @property
    def ollama_max_retries(self) -> int:
        return self.ai_max_retries

    # --- Etsy ---
    etsy_api_key: str = ""
    etsy_shop_id: str = ""
    etsy_dry_run: bool = True  # never publish for real unless explicitly disabled

    # --- Pipeline ---
    max_products_per_day: int = 5
    qa_min_score: float = 0.75

    @property
    def normalized_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            logger.warning(
                "DATABASE_URL uses 'postgresql://'; rewriting to 'postgresql+asyncpg://' "
                "for the async engine. Update your .env to silence this warning."
            )
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def normalized_sync_database_url(self) -> str:
        if self.sync_database_url:
            return self.sync_database_url
        return self.normalized_database_url.replace("+asyncpg", "")

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
