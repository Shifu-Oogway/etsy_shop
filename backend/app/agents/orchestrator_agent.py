"""Chains the full pipeline: trend -> strategy -> build -> SEO -> QA -> publish.

Accepts optional overrides that flow through to StrategyAgent:
  product_type  — "pdf_planner" | "excel_template" | "notion_template"
  niche         — override niche string
  title         — skip concept generation and use this exact title
  price         — override price (float)
  skip_trends   — skip trend scanning if trends already exist
  trend_id      — use a specific trend instead of the latest
"""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.agents.builder_agent import BuilderAgent
from app.agents.publisher_agent import PublisherAgent
from app.agents.qa_agent import QAAgent
from app.agents.seo_agent import SEOAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.trend_agent import TrendAgent


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    async def run(
        self,
        skip_trends: bool = False,
        trend_id: int | None = None,
        product_type: str | None = None,
        niche: str | None = None,
        title: str | None = None,
        price: float | None = None,
        **_: Any,
    ) -> AgentResult:
        steps: dict[str, Any] = {}

        # ── Trend scan ────────────────────────────────────────────────────────
        if not skip_trends and trend_id is None:
            trends = await TrendAgent(self.db, self.llm).execute(n=5)
            steps["trend"] = dict(trends)
            if not trends.ok:
                return AgentResult(ok=False, failed_step="trend", steps=steps)
            trend_id = (trends.get("trend_ids") or [None])[0]

        # ── Strategy (product concept) ────────────────────────────────────────
        strategy = await StrategyAgent(self.db, self.llm).execute(
            trend_id=trend_id,
            product_type=product_type,
            niche=niche,
            title=title,
            price=price,
        )
        steps["strategy"] = dict(strategy)
        if not strategy.ok:
            return AgentResult(ok=False, failed_step="strategy", steps=steps)
        product_id = strategy["product_id"]

        # ── Build → SEO → QA ──────────────────────────────────────────────────
        for step_name, agent_cls in (
            ("builder", BuilderAgent),
            ("seo",     SEOAgent),
            ("qa",      QAAgent),
        ):
            result = await agent_cls(self.db, self.llm).execute(product_id=product_id)
            steps[step_name] = dict(result)
            if not result.ok:
                return AgentResult(
                    ok=False, failed_step=step_name,
                    steps=steps, product_id=product_id,
                )

        if not steps["qa"].get("passed"):
            return AgentResult(
                ok=False, failed_step="qa_gate", steps=steps,
                product_id=product_id,
                error="QA score below threshold — product not published",
            )

        # ── Publish ───────────────────────────────────────────────────────────
        publish = await PublisherAgent(self.db, self.llm).execute(product_id=product_id)
        steps["publisher"] = dict(publish)
        return AgentResult(
            ok=publish.ok, steps=steps,
            product_id=product_id,
            listing_id=publish.get("listing_id"),
        )
