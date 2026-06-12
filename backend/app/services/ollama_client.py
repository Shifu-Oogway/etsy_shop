"""Async Ollama client with retries, backoff, and full error surfacing.

Improvements over the previous version:
- exponential backoff with jitter on connection/timeout errors
- structured JSON generation helper that strips markdown fences
- embeddings endpoint support
- a `health()` probe used by /api/v1/system/health
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        s = get_settings()
        self.base_url = (base_url or s.ollama_base_url).rstrip("/")
        self.model = model or s.ollama_model
        self.embedding_model = s.ollama_embedding_model
        self.timeout = s.ollama_timeout_seconds
        self.max_retries = s.ollama_max_retries

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(f"{self.base_url}{path}", json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError) as exc:
                last_exc = exc
                wait = min(2 ** attempt + random.random(), 15)
                logger.warning("Ollama call failed (attempt %s/%s): %s — retrying in %.1fs",
                               attempt, self.max_retries, exc, wait)
                await asyncio.sleep(wait)
        raise OllamaError(f"Ollama request to {path} failed after {self.max_retries} attempts: {last_exc}")

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        data = await self._post("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        })
        return data.get("response", "")

    async def generate_json(self, prompt: str, system: str = "", temperature: float = 0.3) -> Any:
        """Generate and parse JSON; raises OllamaError with the raw text on failure."""
        sys_prompt = (system + "\nRespond ONLY with valid JSON. No prose, no markdown fences.").strip()
        raw = await self.generate(prompt, system=sys_prompt, temperature=temperature)
        cleaned = _FENCE_RE.sub("", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Model returned invalid JSON: {exc}\n--- raw output ---\n{raw}") from exc

    async def embed(self, text: str) -> list[float]:
        data = await self._post("/api/embeddings", {"model": self.embedding_model, "prompt": text})
        return data.get("embedding", [])

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
