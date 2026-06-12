"""All nine agents."""
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.base import AgentResult, BaseAgent
from app.agents.builder_agent import BuilderAgent
from app.agents.experiment_agent import ExperimentAgent
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.publisher_agent import PublisherAgent
from app.agents.qa_agent import QAAgent
from app.agents.seo_agent import SEOAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.trend_agent import TrendAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    a.name: a for a in (
        TrendAgent, StrategyAgent, BuilderAgent, SEOAgent, QAAgent,
        PublisherAgent, AnalyticsAgent, ExperimentAgent, OrchestratorAgent,
    )
}

__all__ = ["AGENT_REGISTRY", "AgentResult", "BaseAgent", "AnalyticsAgent",
           "BuilderAgent", "ExperimentAgent", "OrchestratorAgent",
           "PublisherAgent", "QAAgent", "SEOAgent", "StrategyAgent", "TrendAgent"]
