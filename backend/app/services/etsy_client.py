"""Etsy Open API v3 client (listings). Honors ETSY_DRY_RUN so the pipeline can
run end-to-end without touching a live shop."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

API_BASE = "https://openapi.etsy.com/v3/application"


class EtsyClient:
    def __init__(self) -> None:
        s = get_settings()
        self.api_key = s.etsy_api_key
        self.shop_id = s.etsy_shop_id
        self.dry_run = s.etsy_dry_run

    @property
    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key}

    async def create_listing(self, *, title: str, description: str, price: float,
                             tags: list[str], file_path: str) -> dict[str, Any]:
        if self.dry_run or not self.api_key:
            fake_id = f"dryrun-{uuid.uuid4().hex[:10]}"
            logger.info("[DRY RUN] would create Etsy listing '%s' (%s tags, $%.2f, file=%s)",
                        title, len(tags), price, file_path)
            return {"listing_id": fake_id, "state": "draft", "dry_run": True,
                    "url": f"https://www.etsy.com/listing/{fake_id}"}

        payload = {
            "quantity": 999,
            "title": title[:140],
            "description": description,
            "price": price,
            "who_made": "i_did",
            "when_made": "2020_2026",
            "taxonomy_id": 2078,  # digital prints/templates
            "type": "download",
            "tags": tags[:13],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{API_BASE}/shops/{self.shop_id}/listings",
                                     headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()


    async def get_listing_stats(self, etsy_listing_id: str) -> dict[str, Any]:
        """Views/favorites for a listing. Dry-run returns deterministic,
        plausibly-growing simulated numbers so the dashboard is exercisable."""
        if self.dry_run or not self.api_key or etsy_listing_id.startswith("dryrun-"):
            import datetime, hashlib
            seed = int(hashlib.md5(etsy_listing_id.encode()).hexdigest()[:6], 16)
            days_live = max(1, (datetime.date.today().toordinal() + seed) % 60)
            views = (seed % 37 + 5) * days_live
            return {"views": views,
                    "favorites": max(1, views // 14),
                    "dry_run": True}

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{API_BASE}/listings/{etsy_listing_id}",
                headers=self._headers)
            resp.raise_for_status()
            data = resp.json()
            return {"views": data.get("views", 0),
                    "favorites": data.get("num_favorers", 0),
                    "dry_run": False}

    async def update_listing(self, etsy_listing_id: str, *,
                             title: str | None = None,
                             description: str | None = None,
                             price: float | None = None,
                             tags: list[str] | None = None) -> dict[str, Any]:
        """Update a live listing. Dry-run logs and echoes the change."""
        changes = {k: v for k, v in {
            "title": title, "description": description,
            "price": price, "tags": tags}.items() if v is not None}

        if self.dry_run or not self.api_key or etsy_listing_id.startswith("dryrun-"):
            logger.info("[DRY RUN] would update listing %s: %s",
                        etsy_listing_id, list(changes))
            return {"listing_id": etsy_listing_id, "updated": list(changes),
                    "dry_run": True}

        payload: dict[str, Any] = {}
        if title is not None:       payload["title"] = title[:140]
        if description is not None: payload["description"] = description
        if price is not None:       payload["price"] = price
        if tags is not None:        payload["tags"] = tags[:13]

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.patch(
                f"{API_BASE}/shops/{self.shop_id}/listings/{etsy_listing_id}",
                headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()
