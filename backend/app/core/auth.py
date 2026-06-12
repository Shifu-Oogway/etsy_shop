"""API-key auth middleware for the dashboard API.

Set DASHBOARD_API_KEY in .env to enable. Empty (the default) = auth disabled,
so local development needs no setup. When enabled, every /api/v1 request must
carry the key in the X-API-Key header (or ?api_key= for SSE/iframe URLs,
which cannot set headers).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

EXEMPT_PATHS = {"/", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = get_settings().dashboard_api_key
        if not key:
            return await call_next(request)          # auth disabled
        if request.method == "OPTIONS":
            return await call_next(request)          # CORS preflight
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        provided = (request.headers.get("x-api-key")
                    or request.query_params.get("api_key", ""))
        if provided != key:
            return JSONResponse(status_code=401,
                                content={"detail": "invalid or missing API key"})
        return await call_next(request)
