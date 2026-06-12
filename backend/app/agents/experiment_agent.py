"""Designs and evaluates pricing/title A-B experiments."""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.models.experiment import Experiment, ExperimentStatus
from app.models.product import Product


class ExperimentAgent(BaseAgent):
    name = "experiment"

    PROMPT = (
        'Design an A/B experiment for this Etsy product: "{title}" at ${price}. '
        'Return JSON: {{"name": str, "hypothesis": str, '
        '"variant_a": {{"title": str, "price": float}}, '
        '"variant_b": {{"title": str, "price": float}}}}.'
    )

    async def run(self, product_id: int, **_: Any) -> AgentResult:
        product = await self.db.get(Product, product_id)
        if product is None:
            return AgentResult(ok=False, error=f"product {product_id} not found")

        design = await self.llm.generate_json(
            self.PROMPT.format(title=product.title, price=product.price))
        exp = Experiment(
            name=str(design.get("name", f"exp-product-{product.id}"))[:160],
            hypothesis=str(design.get("hypothesis", "")),
            status=ExperimentStatus.running,
            variants={"a": design.get("variant_a", {}), "b": design.get("variant_b", {}),
                      "product_id": product.id},
        )
        self.db.add(exp)
        await self.db.flush()
        return AgentResult(ok=True, experiment_id=exp.id)

    async def conclude(self, experiment_id: int, results: dict) -> AgentResult:
        exp = await self.db.get(Experiment, experiment_id)
        if exp is None:
            return AgentResult(ok=False, error=f"experiment {experiment_id} not found")
        exp.results = results
        exp.status = ExperimentStatus.completed
        await self.db.flush()
        return AgentResult(ok=True, experiment_id=exp.id)
