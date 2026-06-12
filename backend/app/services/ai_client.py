"""Unified AI client — NVIDIA NIM (primary) with Ollama fallback.

Priority:
  1. NVIDIA NIM  (OpenAI-compatible, https://integrate.api.nvidia.com/v1)
  2. Ollama      (local, http://host.docker.internal:11434)

NIM is used when NIM_API_KEY is set and non-empty.
On any NIM failure (network, auth, timeout) the call falls back to Ollama.
The fallback is logged at WARNING so you always know which backend served.
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

# HTTP status codes that mean "don't retry — the key/request is bad"
_NO_RETRY_CODES = {400, 401, 403, 422}


class AIClientError(RuntimeError):
    pass


# ── NIM backend ────────────────────────────────────────────────────────────────

class NIMClient:
    """OpenAI-compatible NVIDIA NIM client."""

    def __init__(self) -> None:
        s = get_settings()
        self.base_url    = s.nim_base_url.rstrip("/")
        # Accept NIM_API_KEY or NVIDIA_API_KEY — whichever is set
        self.api_key     = s.nim_api_key or s.nvidia_api_key
        self.model       = s.nim_model
        self.timeout     = s.ai_timeout_seconds
        self.max_retries = s.ai_max_retries

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }

    async def _post(self, messages: list[dict], temperature: float) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json={
                            "model":       self.model,
                            "messages":    messages,
                            "temperature": temperature,
                        },
                    )
                    # Don't retry on auth/bad-request errors
                    if resp.status_code in _NO_RETRY_CODES:
                        raise AIClientError(
                            f"NIM returned {resp.status_code}: {resp.text[:200]}"
                        )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

            except AIClientError:
                raise  # propagate immediately — no retry
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = min(2 ** attempt + random.random(), 10)
                    logger.warning("NIM attempt %s/%s failed: %s — retry in %.1fs",
                                   attempt, self.max_retries, exc, wait)
                    await asyncio.sleep(wait)

        raise AIClientError(
            f"NIM request failed after {self.max_retries} attempts: {last_exc}"
        )

    async def generate(self, prompt: str, system: str = "",
                       temperature: float = 0.7) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self._post(messages, temperature)

    async def health(self) -> dict:
        """Returns {"ok": bool, "status": str, "model": str}."""
        if not self.available:
            return {"ok": False, "status": "no_key", "model": self.model}
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                if resp.status_code == 200:
                    return {"ok": True, "status": "healthy", "model": self.model}
                if resp.status_code in (401, 403):
                    return {"ok": False, "status": "invalid_key", "model": self.model}
                return {"ok": False, "status": f"http_{resp.status_code}", "model": self.model}
        except httpx.TimeoutException:
            return {"ok": False, "status": "timeout", "model": self.model}
        except Exception as exc:
            return {"ok": False, "status": "unreachable", "model": self.model}


# ── Ollama backend ─────────────────────────────────────────────────────────────

class OllamaBackend:
    """Direct Ollama backend — used as fallback."""

    def __init__(self) -> None:
        s = get_settings()
        self.base_url        = s.ollama_base_url.rstrip("/")
        self.model           = s.ollama_model
        self.embedding_model = s.ollama_embedding_model
        self.timeout         = s.ai_timeout_seconds
        self.max_retries     = s.ai_max_retries

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
                if attempt < self.max_retries:
                    wait = min(2 ** attempt + random.random(), 10)
                    logger.warning("Ollama attempt %s/%s failed: %s — retry in %.1fs",
                                   attempt, self.max_retries, exc, wait)
                    await asyncio.sleep(wait)
        raise AIClientError(
            f"Ollama {path} failed after {self.max_retries} attempts: {last_exc}"
        )

    async def generate(self, prompt: str, system: str = "",
                       temperature: float = 0.7) -> str:
        data = await self._post("/api/generate", {
            "model":   self.model,
            "prompt":  prompt,
            "system":  system,
            "stream":  False,
            "options": {"temperature": temperature},
        })
        return data.get("response", "")

    async def embed(self, text: str) -> list[float]:
        data = await self._post("/api/embeddings", {
            "model":  self.embedding_model,
            "prompt": text,
        })
        return data.get("embedding", [])

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return {"ok": True, "status": "healthy", "model": self.model}
                return {"ok": False, "status": f"http_{resp.status_code}", "model": self.model}
        except httpx.TimeoutException:
            return {"ok": False, "status": "timeout", "model": self.model}
        except Exception:
            return {"ok": False, "status": "unreachable", "model": self.model}


# ── Unified client ─────────────────────────────────────────────────────────────

class AIClient:
    """NIM-first, Ollama-fallback unified AI client."""

    def __init__(self) -> None:
        self._nim    = NIMClient()
        self._ollama = OllamaBackend()

    async def generate(self, prompt: str, system: str = "",
                       temperature: float = 0.7) -> str:
        if self._nim.available:
            try:
                result = await self._nim.generate(prompt, system=system,
                                                  temperature=temperature)
                logger.debug("generate: served by NIM (%s)", self._nim.model)
                return result
            except AIClientError as exc:
                logger.warning("NIM generate failed — falling back to Ollama: %s", exc)
        result = await self._ollama.generate(prompt, system=system,
                                             temperature=temperature)
        logger.debug("generate: served by Ollama (%s)", self._ollama.model)
        return result

    async def generate_json(self, prompt: str, system: str = "",
                            temperature: float = 0.3) -> Any:
        sys_prompt = (
            system + "\nRespond ONLY with valid JSON. No prose, no markdown fences."
        ).strip()
        raw = await self.generate(prompt, system=sys_prompt, temperature=temperature)
        cleaned = _FENCE_RE.sub("", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIClientError(
                f"Model returned invalid JSON: {exc}\n--- raw ---\n{raw}"
            ) from exc

    async def embed(self, text: str) -> list[float]:
        return await self._ollama.embed(text)

    async def health(self) -> dict[str, Any]:
        nim_h, ollama_h = await asyncio.gather(
            self._nim.health(), self._ollama.health()
        )
        active = "nim" if nim_h["ok"] else ("ollama" if ollama_h["ok"] else "none")
        return {
            "active_backend": active,
            "nim":    nim_h,
            "ollama": ollama_h,
        }


# Backward-compat alias
class OllamaClient(AIClient):
    pass
