"""All API routers."""
from app.routers import (agents, analytics, experiments, listings, products,
                         publisher, schedules, system, tests, trends)

ALL_ROUTERS = [
    products.router, listings.router, trends.router, experiments.router,
    analytics.router, publisher.router, agents.router, schedules.router,
    system.router, tests.router,
]
