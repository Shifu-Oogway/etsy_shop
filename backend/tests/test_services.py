from pathlib import Path

from app.services.etsy_client import EtsyClient
from app.services.file_generator import (generate_excel_template,
                                         generate_notion_template,
                                         generate_pdf_planner)


async def test_etsy_dry_run_never_calls_network():
    client = EtsyClient()
    assert client.dry_run is True
    result = await client.create_listing(title="T", description="D", price=4.99,
                                         tags=["a"], file_path="x.pdf")
    assert result["dry_run"] is True and result["listing_id"].startswith("dryrun-")


def test_pdf_generator(tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    path = generate_pdf_planner("test-planner", {"title": "Planner",
                                                 "pages": [{"title": "P1", "sections": ["S1"]}]})
    assert Path(path).exists() and Path(path).stat().st_size > 0


def test_excel_generator(tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    path = generate_excel_template("test-tracker", {"sheets": [{"name": "S", "headers": ["A"]}]})
    assert Path(path).exists()


def test_notion_generator(tmp_path, monkeypatch):
    import app.services.file_generator as fg
    monkeypatch.setattr(fg, "OUTPUT_DIR", tmp_path)
    path = generate_notion_template("test-hub", {"title": "Hub",
                                                 "blocks": [{"heading": "H", "content": "C"}]})
    assert Path(path).exists() and Path(path).with_suffix(".json").exists()


def test_celery_beat_schedule_configured():
    from app.tasks.celery_app import celery_app
    assert "daily-full-pipeline" in celery_app.conf.beat_schedule
    assert celery_app.conf.beat_schedule["daily-full-pipeline"]["kwargs"]["agent_name"] == "orchestrator"
