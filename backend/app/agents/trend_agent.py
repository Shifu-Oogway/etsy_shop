"""Discovers product niches from REAL market data (Etsy + Google autocomplete),
with the LLM used only to score and structure what buyers actually search for.
Falls back to pure LLM ideation when no network sources are reachable."""
from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.models.trend import Trend
from app.services.trend_sources import gather_market_signals


class TrendAgent(BaseAgent):
    name = "trend"

    SCORE_PROMPT = (
        "You analyze the Etsy digital products market. Below are REAL search "
        "queries gathered from Etsy and Google autocomplete, grouped by seed "
        "keyword:\n{signals}\n\n"
        "Pick the {n} most promising opportunities for digital downloads "
        "(PDF planners, Excel templates, Notion templates). Prefer specific, "
        "purchase-intent queries over broad ones. "
        'Return a JSON array: [{{"keyword": str (the actual search query), '
        '"niche": str, "score": float 0-1, "rationale": str}}].'
    )

    FALLBACK_PROMPT = (
        "You analyze the Etsy digital products market. List {n} currently promising "
        "niches for digital downloads (PDF planners, Excel templates, Notion templates). "
        'Return a JSON array of objects: {{"keyword": str, "niche": str, '
        '"score": float between 0 and 1, "rationale": str}}.'
    )

    async def run(self, n: int = 5, **_: Any) -> AgentResult:
        signals = await gather_market_signals(n_seeds=max(3, n))
        total_real = sum(len(v) for v in signals.values())

        if total_real >= 5:
            prompt = self.SCORE_PROMPT.format(
                signals=json.dumps(signals, indent=1)[:2500], n=n)
            source = "market_data"
        else:
            prompt = self.FALLBACK_PROMPT.format(n=n)
            source = "llm_only"
            await self._log("WARN", "trend sources unreachable — using LLM-only ideation")

        items = await self.llm.generate_json(prompt)
        if not isinstance(items, list):
            items = [items]

        trends: list[Trend] = []
        for item in items[:n]:
            t = Trend(
                keyword=str(item.get("keyword", ""))[:160],
                niche=str(item.get("niche", ""))[:120],
                score=float(item.get("score", 0.0)),
                details={"rationale": item.get("rationale", ""),
                         "source": source,
                         "real_queries": total_real},
            )
            self.db.add(t)
            trends.append(t)
        await self.db.flush()
        return AgentResult(ok=True, trend_ids=[t.id for t in trends],
                           count=len(trends), source=source)
