"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import APIKeyMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import ALL_ROUTERS

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info("Starting %s (env=%s, dry_run=%s)",
                settings.app_name, settings.environment, settings.etsy_dry_run)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in ALL_ROUTERS:
        app.include_router(router, prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root():
        return {"app": settings.app_name, "docs": "/docs",
                "api": settings.api_v1_prefix}

    return app


app = create_app()
