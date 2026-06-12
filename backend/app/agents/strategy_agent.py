"""Picks which trend to act on and defines the product concept.

Accepts optional overrides:
  product_type  — force a specific type instead of letting the LLM choose
  niche         — override the trend niche
  title         — skip LLM concept generation entirely and use this title
  price         — override price
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.agents.base import AgentResult, BaseAgent
from app.models.product import Product, ProductStatus, ProductType
from app.models.trend import Trend
from app.services.similarity import check_duplicate, store_embedding

VALID_TYPES = list(ProductType.__members__.keys())


class StrategyAgent(BaseAgent):
    name = "strategy"

    PROMPT = (
        "Given this market trend — keyword: '{keyword}', niche: '{niche}' — design ONE "
        "digital product concept{type_hint}. Return JSON: {{\"title\": str (max 120 chars), "
        "\"description\": str, \"product_type\": one of [\"pdf_planner\", "
        "\"excel_template\", \"notion_template\"], \"price\": float between 2.99 and 14.99}}."
    )

    async def run(
        self,
        trend_id: int | None = None,
        product_type: str | None = None,
        niche: str | None = None,
        title: str | None = None,
        price: float | None = None,
        force: bool = False,
        **_: Any,
    ) -> AgentResult:
        # Validate product_type override
        if product_type and product_type not in VALID_TYPES:
            return AgentResult(
                ok=False,
                error=f"unknown product_type '{product_type}'. Valid: {VALID_TYPES}",
            )

        # Get trend for context (used even when title is overridden)
        if trend_id is not None:
            trend = await self.db.get(Trend, trend_id)
        else:
            row = await self.db.execute(select(Trend).order_by(Trend.score.desc()).limit(1))
            trend = row.scalar_one_or_none()

        if trend is None and title is None:
            return AgentResult(
                ok=False,
                error="no trends available and no title given — run the trend agent first",
            )

        keyword = trend.keyword if trend else (title or "digital product")
        resolved_niche = niche or (trend.niche if trend else "general")

        # If title is provided, skip LLM concept generation
        if title:
            concept = {
                "title":        title,
                "description":  f"A {product_type or 'pdf_planner'} for {resolved_niche}.",
                "product_type": product_type or "pdf_planner",
                "price":        price or 4.99,
            }
        else:
            type_hint = (
                f" — the product MUST be of type '{product_type}'"
                if product_type else ""
            )
            prompt = self.PROMPT.format(
                keyword=keyword,
                niche=resolved_niche,
                type_hint=type_hint,
            )
            concept = await self.llm.generate_json(prompt)

        # Apply overrides on top of whatever the LLM returned
        if product_type:
            concept["product_type"] = product_type
        if price is not None:
            concept["price"] = price

        ptype = concept.get("product_type", "pdf_planner")
        if ptype not in ProductType.__members__:
            ptype = product_type or "pdf_planner"

        # ── Deduplication gate ────────────────────────────────────────────
        candidate_title = str(concept.get("title", keyword))[:255]
        dup = await check_duplicate(self.db, candidate_title, llm=self.llm)
        if dup["duplicate"] and not force:
            return AgentResult(
                ok=False,
                error=(f"duplicate product blocked: '{candidate_title}' is "
                       f"{dup['score']:.0%} similar to existing '{dup['match']}' "
                       f"({dup['method']}). Pass force=true to override."),
                duplicate_of=dup["match"], similarity=dup["score"],
            )

        product = Product(
            title=str(concept.get("title", keyword))[:255],
            description=str(concept.get("description", "")),
            product_type=ProductType[ptype],
            status=ProductStatus.draft,
            niche=resolved_niche,
            price=max(2.99, min(14.99, float(concept.get("price", 4.99)))),
            spec={"trend_id": trend.id if trend else None},
        )
        self.db.add(product)
        await self.db.flush()
        await store_embedding(self.db, product.id, product.title, llm=self.llm)
        return AgentResult(ok=True, product_id=product.id, product_type=ptype)
