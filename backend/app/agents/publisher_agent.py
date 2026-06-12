"""Publishes a QA-passed product to Etsy (or dry-runs it)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.agents.base import AgentResult, BaseAgent
from app.models.listing import Listing, ListingStatus
from app.models.product import Product, ProductStatus
from app.models.seo import SEOMetadata
from app.services.etsy_client import EtsyClient


class PublisherAgent(BaseAgent):
    name = "publisher"

    async def run(self, product_id: int, **_: Any) -> AgentResult:
        product = await self.db.get(Product, product_id)
        if product is None:
            return AgentResult(ok=False, error=f"product {product_id} not found")
        if product.status != ProductStatus.qa_passed:
            return AgentResult(ok=False, error=f"product {product_id} is '{product.status.value}', "
                                               "only qa_passed products can be published")

        row = await self.db.execute(
            select(SEOMetadata).where(SEOMetadata.product_id == product.id)
            .order_by(SEOMetadata.id.desc()).limit(1))
        seo = row.scalar_one_or_none()
        title = (seo.optimized_title if seo else product.title)[:140]
        description = seo.optimized_description if seo else product.description
        tags = (seo.tags if seo else [])[:13]

        result = await EtsyClient().create_listing(
            title=title, description=description, price=product.price,
            tags=tags, file_path=product.file_path)

        listing = Listing(
            product_id=product.id,
            etsy_listing_id=str(result.get("listing_id", "")),
            status=ListingStatus.active,
            title=title, tags=tags, price=product.price,
            url=result.get("url", ""),
        )
        self.db.add(listing)
        product.status = ProductStatus.published
        await self.db.flush()
        return AgentResult(ok=True, listing_id=listing.id,
                           etsy_listing_id=listing.etsy_listing_id,
                           dry_run=bool(result.get("dry_run", False)))
