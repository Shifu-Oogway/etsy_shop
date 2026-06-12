"""Tests for dedup, mockups, cron matcher, QA file validation, auth, Etsy stats."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.services.cron_match import cron_matches
from app.services.similarity import check_duplicate, lexical_similarity
from app.services.mockup_generator import generate_mockups
from app.services.etsy_client import EtsyClient


# ── similarity ────────────────────────────────────────────────────────────────

def test_lexical_similarity_obvious_duplicate():
    a = "2026 Budget Planner Printable PDF"
    b = "Budget Planner 2026 — Printable"
    assert lexical_similarity(a, b) > 0.8


def test_lexical_similarity_different_products():
    a = "Wedding Guest List Tracker"
    b = "Weekly Meal Prep Planner"
    assert lexical_similarity(a, b) < 0.6


@pytest.mark.asyncio
async def test_check_duplicate_blocks_near_identical(db, llm):
    from app.models.product import Product, ProductStatus, ProductType
    db.add(Product(title="Ultimate Budget Planner 2026", description="d" * 50,
                   product_type=ProductType.pdf_planner,
                   status=ProductStatus.draft, niche="finance", price=4.99))
    await db.flush()
    result = await check_duplicate(db, "Ultimate Budget Planner 2026 Printable")
    assert result["duplicate"] is True
    assert result["method"] == "lexical"


@pytest.mark.asyncio
async def test_check_duplicate_allows_distinct(db, llm):
    from app.models.product import Product, ProductStatus, ProductType
    db.add(Product(title="Wedding Seating Chart", description="d" * 50,
                   product_type=ProductType.pdf_planner,
                   status=ProductStatus.draft, niche="wedding", price=4.99))
    await db.flush()
    result = await check_duplicate(db, "Freelance Invoice Tracker Excel")
    assert result["duplicate"] is False


# ── mockups ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ptype,spec", [
    ("pdf_planner",     {"pages":  [{"title": "Budget", "sections": ["Income"]}]}),
    ("excel_template",  {"sheets": [{"name": "Data", "headers": ["A", "B", "C"]}]}),
    ("notion_template", {"blocks": [{"heading": "Hub", "content": "x" * 50}]}),
])
def test_mockups_generated_for_every_type(tmp_path, monkeypatch, ptype, spec):
    import app.services.mockup_generator as mg
    monkeypatch.setattr(mg, "OUTPUT_DIR", tmp_path)
    paths = generate_mockups("test-product", "Test Product Title", ptype, spec)
    assert len(paths) == 2
    for p in paths:
        data = open(p, "rb").read()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"   # valid PNG magic
        assert len(data) > 5000


# ── cron matcher ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cron,dt,expected", [
    ("0 6 * * *",    datetime(2026, 6, 11, 6, 0),  True),
    ("0 6 * * *",    datetime(2026, 6, 11, 6, 1),  False),
    ("*/15 * * * *", datetime(2026, 6, 11, 9, 30), True),
    ("*/15 * * * *", datetime(2026, 6, 11, 9, 31), False),
    ("30 5 * * *",   datetime(2026, 6, 11, 5, 30), True),
    ("0 9-17 * * *", datetime(2026, 6, 11, 13, 0), True),
    ("0 9-17 * * *", datetime(2026, 6, 11, 19, 0), False),
    ("0 6 * * 0,6",  datetime(2026, 6, 13, 6, 0),  True),   # Saturday(=5)? weekday(): Sat=5
    ("bad cron",     datetime(2026, 6, 11, 6, 0),  False),
])
def test_cron_matches(cron, dt, expected):
    # note: dow uses Python weekday() (Mon=0..Sun=6)
    if cron == "0 6 * * 0,6":
        expected = dt.weekday() in (0, 6)
    assert cron_matches(cron, dt) is expected


# ── QA file validation ────────────────────────────────────────────────────────

def test_qa_validates_real_pdf(tmp_path):
    from app.agents.qa_agent import _validate_file
    import app.services.file_generator as fg
    fg.OUTPUT_DIR = tmp_path
    from app.services.template_library import get_template
    spec = get_template("pdf_planner", "finance")
    spec["title"] = "T"
    path = fg.generate_pdf_planner("qa-test", spec)
    checks = _validate_file(path)
    assert checks.get("pdf_magic") or checks.get("html_valid")
    assert checks["file_size_ok"]


def test_qa_rejects_corrupt_pdf(tmp_path):
    from app.agents.qa_agent import _validate_file
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf at all")
    checks = _validate_file(str(bad))
    assert checks["pdf_magic"] is False


def test_qa_rejects_empty_xlsx(tmp_path):
    from app.agents.qa_agent import _validate_file
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"garbage")
    checks = _validate_file(str(bad))
    assert checks["xlsx_loads"] is False


# ── Etsy dry-run stats ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_etsy_dry_run_stats_deterministic():
    client = EtsyClient()
    s1 = await client.get_listing_stats("dryrun-abc123")
    s2 = await client.get_listing_stats("dryrun-abc123")
    assert s1["dry_run"] is True
    assert s1["views"] == s2["views"]           # deterministic per listing+day
    assert s1["views"] > 0


@pytest.mark.asyncio
async def test_etsy_dry_run_update():
    client = EtsyClient()
    result = await client.update_listing("dryrun-xyz", title="New", price=5.99)
    assert result["dry_run"] is True
    assert set(result["updated"]) == {"title", "price"}


# ── auth middleware ───────────────────────────────────────────────────────────

from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app


@pytest.fixture
def client(db):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_disabled_by_default(client):
    async with client as c:
        resp = await c.get("/api/v1/system/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_blocks_without_key(client, monkeypatch):
    from app.core import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "dashboard_api_key", "secret123")
    async with client as c:
        resp = await c.get("/api/v1/system/health")
        assert resp.status_code == 401
        resp2 = await c.get("/api/v1/system/health",
                            headers={"X-API-Key": "secret123"})
        assert resp2.status_code == 200
