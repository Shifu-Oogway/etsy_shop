import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def client(db):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def test_root(client):
    async with client as c:
        resp = await c.get("/")
    assert resp.status_code == 200 and resp.json()["api"] == "/api/v1"


async def test_product_crud(client):
    async with client as c:
        created = await c.post("/api/v1/products", json={
            "title": "API Planner", "product_type": "pdf_planner",
            "description": "x" * 60, "price": 5.99})
        assert created.status_code == 201, created.text
        pid = created.json()["id"]

        got = await c.get(f"/api/v1/products/{pid}")
        assert got.status_code == 200 and got.json()["title"] == "API Planner"

        patched = await c.patch(f"/api/v1/products/{pid}", json={"price": 7.99})
        assert patched.json()["price"] == 7.99

        listed = await c.get("/api/v1/products")
        assert len(listed.json()) == 1

        deleted = await c.delete(f"/api/v1/products/{pid}")
        assert deleted.status_code == 204


async def test_agents_listed(client):
    async with client as c:
        resp = await c.get("/api/v1/agents")
    assert resp.status_code == 200 and len(resp.json()["agents"]) == 9


async def test_unknown_agent_404(client):
    async with client as c:
        resp = await c.post("/api/v1/agents/nonexistent/run", json={})
    assert resp.status_code == 404


async def test_schedules_crud(client):
    async with client as c:
        created = await c.post("/api/v1/schedules", json={
            "name": "nightly", "task_name": "app.tasks.run_agent"})
        assert created.status_code == 201
        sid = created.json()["id"]
        toggled = await c.patch(f"/api/v1/schedules/{sid}/toggle")
        assert toggled.json()["enabled"] is False


async def test_health_reports_dependencies(client, monkeypatch):
    from app.services.ai_client import AIClient

    async def fake_health(self):
        return {
            "active_backend": "none",
            "nim":    {"available": False, "healthy": False, "model": ""},
            "ollama": {"healthy": False, "model": "llama3.1:8b"},
        }

    monkeypatch.setattr(AIClient, "health", fake_health)
    async with client as c:
        resp = await c.get("/api/v1/system/health")
    body = resp.json()
    assert body["checks"]["database"] is True
    assert body["checks"]["active_ai_backend"] == "none"
    assert body["checks"]["ai"]["ollama"]["healthy"] is False
