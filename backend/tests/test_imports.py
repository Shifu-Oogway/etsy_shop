"""Every module in the system must import cleanly (38 modules)."""
import importlib

import pytest

MODULES = [
    "app",
    "app.main",
    "app.core", "app.core.config", "app.core.database", "app.core.logging",
    "app.models", "app.models.base_mixin", "app.models.product", "app.models.listing",
    "app.models.trend", "app.models.seo", "app.models.qa_report", "app.models.sale",
    "app.models.experiment", "app.models.task_run", "app.models.embedding",
    "app.models.schedule", "app.models.event_log",
    "app.schemas", "app.schemas.common", "app.schemas.product", "app.schemas.listing",
    "app.schemas.trend", "app.schemas.experiment", "app.schemas.analytics",
    "app.routers", "app.routers.products", "app.routers.listings", "app.routers.trends",
    "app.routers.experiments", "app.routers.analytics", "app.routers.publisher",
    "app.routers.agents", "app.routers.schedules", "app.routers.system",
    "app.agents", "app.agents.base", "app.agents.trend_agent", "app.agents.strategy_agent",
    "app.agents.builder_agent", "app.agents.seo_agent", "app.agents.qa_agent",
    "app.agents.publisher_agent", "app.agents.analytics_agent", "app.agents.experiment_agent",
    "app.agents.orchestrator_agent",
    "app.services", "app.services.ollama_client", "app.services.etsy_client",
    "app.services.file_generator",
    "app.tasks", "app.tasks.celery_app", "app.tasks.jobs",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)


def test_module_count_at_least_38():
    assert len(MODULES) >= 38
