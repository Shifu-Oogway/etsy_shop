"""Optimizes title/description/tags for Etsy search."""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.models.product import Product
from app.models.seo import SEOMetadata


class SEOAgent(BaseAgent):
    name = "seo"

    PROMPT = (
        'Optimize this Etsy digital product for search.\nTitle: "{title}"\n'
        'Description: "{description}"\nNiche: "{niche}"\n'
        "Etsy rules: title max 140 chars, exactly 13 tags, each tag max 20 chars.\n"
        'Return JSON: {{"title": str, "description": str, "tags": [str] (13 items), '
        '"keywords": [str]}}.'
    )

    async def run(self, product_id: int, **_: Any) -> AgentResult:
        product = await self.db.get(Product, product_id)
        if product is None:
            return AgentResult(ok=False, error=f"product {product_id} not found")

        data = await self.llm.generate_json(self.PROMPT.format(
            title=product.title, description=product.description[:500], niche=product.niche))
        tags = [str(t)[:20] for t in data.get("tags", [])][:13]
        seo = SEOMetadata(
            product_id=product.id,
            optimized_title=str(data.get("title", product.title))[:140],
            optimized_description=str(data.get("description", product.description)),
            tags=tags,
            keywords=[str(k) for k in data.get("keywords", [])],
        )
        self.db.add(seo)
        await self.db.flush()
        return AgentResult(ok=True, seo_id=seo.id, tag_count=len(tags))
