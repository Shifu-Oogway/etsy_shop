"""Builds the actual product file from a spec produced by the LLM.

The LLM spec is merged on top of the niche-matched library template
(app.services.template_library), so every product meets a detail floor
even when the model output is thin.
"""
from __future__ import annotations

import re
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.models.product import Product, ProductStatus
from app.services.file_generator import GENERATORS
from app.services.mockup_generator import generate_mockups
from app.services.template_library import get_template, merge_spec

SPEC_PROMPTS = {
    "pdf_planner": (
        'Design a DETAILED page structure for a PDF planner titled "{title}" '
        'in the "{niche}" niche. Here is a base structure to improve and '
        'customize for this exact product: {base}. '
        'Make sections specific and actionable (not generic like "Notes"). '
        'Return JSON: {{"title": str, "pages": [{{"title": str, '
        '"sections": [str]}}] (6-8 pages, 3-6 sections each)}}.'
    ),
    "excel_template": (
        'Design a DETAILED Excel template titled "{title}" in the "{niche}" '
        'niche. Here is a base structure to improve and customize: {base}. '
        'Headers must be specific, useful columns a buyer would actually use. '
        'Return JSON: {{"title": str, "sheets": [{{"name": str, '
        '"headers": [str]}}] (3-5 sheets, 4-8 headers each)}}.'
    ),
    "notion_template": (
        'Design a DETAILED Notion template titled "{title}" in the "{niche}" '
        'niche. Here is a base structure to improve and customize: {base}. '
        'Each block needs a clear heading and 1-2 sentences describing exactly '
        'what the section does for the user. '
        'Return JSON: {{"title": str, "blocks": [{{"heading": str, '
        '"content": str}}] (5-8 blocks)}}.'
    ),
}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "product"


class BuilderAgent(BaseAgent):
    name = "builder"

    async def run(self, product_id: int, **_: Any) -> AgentResult:
        product = await self.db.get(Product, product_id)
        if product is None:
            return AgentResult(ok=False, error=f"product {product_id} not found")

        ptype = product.product_type.value
        niche = product.niche

        # Library base for this niche — fed to the LLM as a starting point
        base = get_template(ptype, niche)

        prompt = SPEC_PROMPTS[ptype].format(
            title=product.title,
            niche=niche or "general",
            base=str(base)[:1200],  # keep prompt size sane
        )

        try:
            llm_spec = await self.llm.generate_json(prompt)
        except Exception:
            # LLM unavailable or invalid output — library template alone is
            # still a complete, sellable product.
            llm_spec = {"title": product.title}

        # Merge: LLM detail on top, library floor underneath
        spec = merge_spec(ptype, niche, llm_spec)
        spec.setdefault("title", product.title)

        slug = slugify(product.title)
        path = GENERATORS[ptype](slug, spec)
        images = generate_mockups(slug, product.title, ptype, spec)

        product.spec = {**(product.spec or {}), "build_spec": spec,
                        "images": images}
        product.file_path = path
        product.status = ProductStatus.generated
        await self.db.flush()
        return AgentResult(ok=True, product_id=product.id, file_path=path)
