from pathlib import Path

from app.agents import (AGENT_REGISTRY, AnalyticsAgent, BuilderAgent,
                        ExperimentAgent, OrchestratorAgent, PublisherAgent,
                        QAAgent, SEOAgent, StrategyAgent, TrendAgent)
from app.models.product import ProductStatus


async def test_registry_has_nine_agents():
    assert len(AGENT_REGISTRY) == 9


async def test_trend_agent(db, llm):
    result = await TrendAgent(db, llm).execute(n=3)
    assert result.ok and result["count"] == 3


async def test_strategy_agent(db, llm):
    await TrendAgent(db, llm).execute(n=3)
    result = await StrategyAgent(db, llm).execute()
    assert result.ok and result["product_id"]


async def test_builder_agent_creates_file(db, llm, tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    await TrendAgent(db, llm).execute(n=1)
    pid = (await StrategyAgent(db, llm).execute())["product_id"]
    result = await BuilderAgent(db, llm).execute(product_id=pid)
    assert result.ok and Path(result["file_path"]).exists()


async def test_seo_agent_thirteen_tags(db, llm):
    await TrendAgent(db, llm).execute(n=1)
    pid = (await StrategyAgent(db, llm).execute())["product_id"]
    result = await SEOAgent(db, llm).execute(product_id=pid)
    assert result.ok and result["tag_count"] == 13


async def test_qa_agent_passes_good_product(db, llm, tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    await TrendAgent(db, llm).execute(n=1)
    pid = (await StrategyAgent(db, llm).execute())["product_id"]
    await BuilderAgent(db, llm).execute(product_id=pid)
    await SEOAgent(db, llm).execute(product_id=pid)
    result = await QAAgent(db, llm).execute(product_id=pid)
    assert result.ok and result["passed"] and result["score"] >= 0.75


async def test_publisher_refuses_unvalidated_product(db, llm):
    await TrendAgent(db, llm).execute(n=1)
    pid = (await StrategyAgent(db, llm).execute())["product_id"]
    result = await PublisherAgent(db, llm).execute(product_id=pid)
    assert not result.ok and "qa_passed" in result["error"]


async def test_full_pipeline_via_orchestrator(db, llm, tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    result = await OrchestratorAgent(db, llm).execute()
    assert result.ok, result.get("error")
    assert result["listing_id"]
    from app.models.product import Product
    product = await db.get(Product, result["product_id"])
    assert product.status == ProductStatus.published


async def test_analytics_agent(db, llm, tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    await OrchestratorAgent(db, llm).execute()
    result = await AnalyticsAgent(db, llm).execute()
    assert result.ok
    assert result["totals"]["products"] == 1
    assert result["totals"]["listings"] == 1


async def test_experiment_agent(db, llm):
    await TrendAgent(db, llm).execute(n=1)
    pid = (await StrategyAgent(db, llm).execute())["product_id"]
    result = await ExperimentAgent(db, llm).execute(product_id=pid)
    assert result.ok and result["experiment_id"]


async def test_agent_errors_are_captured_not_raised(db, llm):
    result = await BuilderAgent(db, llm).execute(product_id=999999)
    assert not result.ok and "not found" in result["error"]
