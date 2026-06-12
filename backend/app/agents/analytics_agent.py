"""Aggregates sales/listing performance. Uses cast() in its standard,
PostgreSQL-compatible form (the func.cast() variant broke before)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Float, cast, func, select

from datetime import datetime, timezone

from app.agents.base import AgentResult, BaseAgent
from app.models.listing import Listing, ListingStatus
from app.models.product import Product
from app.models.sale import Sale
from app.services.etsy_client import EtsyClient


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    async def run(self, sync_stats: bool = True, **_: Any) -> AgentResult:
        # ── Sync per-listing view/favorite stats from Etsy ──────────────────
        synced = 0
        if sync_stats:
            etsy = EtsyClient()
            rows = await self.db.execute(
                select(Listing).where(Listing.status == ListingStatus.active)
                .order_by(Listing.id.desc()).limit(100))
            for listing in rows.scalars():
                if not listing.etsy_listing_id:
                    continue
                try:
                    stats = await etsy.get_listing_stats(listing.etsy_listing_id)
                    listing.stats = {**stats,
                                     "last_synced": datetime.now(timezone.utc).isoformat()}
                    synced += 1
                except Exception as exc:
                    await self._log("WARN", f"stats sync failed for listing "
                                            f"{listing.id}: {exc}")
            await self.db.flush()

        total_products = (await self.db.execute(select(func.count(Product.id)))).scalar() or 0
        total_listings = (await self.db.execute(select(func.count(Listing.id)))).scalar() or 0
        total_sales = (await self.db.execute(select(func.count(Sale.id)))).scalar() or 0
        revenue = (await self.db.execute(
            select(func.coalesce(func.sum(cast(Sale.amount, Float)), 0.0)))).scalar() or 0.0

        by_status = dict((await self.db.execute(
            select(Product.status, func.count(Product.id)).group_by(Product.status))).all())

        return AgentResult(
            ok=True,
            totals={"products": total_products, "listings": total_listings,
                    "sales": total_sales, "revenue": round(float(revenue), 2)},
            products_by_status={getattr(k, "value", str(k)): v for k, v in by_status.items()},
            stats_synced=synced,
        )
