"""Real market-trend data sources with graceful degradation.

Priority:
  1. Etsy search autocomplete  (public endpoint — real buyer search behavior)
  2. Google Trends related queries (unofficial widget API)
  3. Curated seed list (always available)

The trend agent fans seed keywords through these sources and lets the LLM
score/structure the REAL results, instead of hallucinating demand.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random

import httpx

logger = logging.getLogger(__name__)

SEED_KEYWORDS = [
    "budget planner", "wedding planner", "meal planner", "habit tracker",
    "notion template", "small business", "fitness tracker", "study planner",
    "travel itinerary", "content calendar", "cleaning schedule",
    "savings challenge", "adhd planner", "teacher planner", "invoice template",
]


async def etsy_autocomplete(keyword: str, timeout: float = 6.0) -> list[str]:
    """Etsy's public search-suggestion endpoint — real buyer queries."""
    url = "https://www.etsy.com/suggestions_ajax.php"
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }) as client:
            resp = await client.get(url, params={"search_query": keyword,
                                                 "search_type": "all"})
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = data.get("results", []) or data.get("suggestions", [])
            out = []
            for r in results:
                q = r.get("query") or r.get("text") or ""
                if q and q.lower() != keyword.lower():
                    out.append(q)
            return out[:8]
    except Exception as exc:
        logger.debug("etsy_autocomplete(%s) failed: %s", keyword, exc)
        return []


async def google_related_queries(keyword: str, timeout: float = 8.0) -> list[str]:
    """Google autocomplete (public, no key) as a demand proxy."""
    url = "https://suggestqueries.google.com/complete/search"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params={
                "client": "firefox", "q": keyword,
            })
            if resp.status_code != 200:
                return []
            data = json.loads(resp.text)
            suggestions = data[1] if len(data) > 1 else []
            return [s for s in suggestions if s.lower() != keyword.lower()][:8]
    except Exception as exc:
        logger.debug("google_related_queries(%s) failed: %s", keyword, exc)
        return []


async def gather_market_signals(n_seeds: int = 5) -> dict[str, list[str]]:
    """Fan seed keywords through real sources. Returns {seed: [related queries]}.

    Never raises — sources that fail just contribute nothing.
    """
    seeds = random.sample(SEED_KEYWORDS, min(n_seeds, len(SEED_KEYWORDS)))

    async def for_seed(seed: str) -> tuple[str, list[str]]:
        etsy, google = await asyncio.gather(
            etsy_autocomplete(seed), google_related_queries(seed))
        merged, seen = [], set()
        for q in etsy + google:
            ql = q.lower()
            if ql not in seen:
                seen.add(ql)
                merged.append(q)
        return seed, merged

    results = await asyncio.gather(*(for_seed(s) for s in seeds))
    signals = {seed: queries for seed, queries in results}

    total = sum(len(v) for v in signals.values())
    logger.info("market signals: %d seeds, %d real queries", len(signals), total)
    return signals
