"""Template library coverage — every niche x type combination must be complete."""
from __future__ import annotations

import pytest

from app.services.template_library import (
    EXCEL_TEMPLATES, NOTION_TEMPLATES, PDF_TEMPLATES,
    get_template, match_niche, merge_spec,
)

NICHES = list(PDF_TEMPLATES.keys())
TYPES = ["pdf_planner", "excel_template", "notion_template"]


def test_all_niches_covered_in_all_types():
    assert set(PDF_TEMPLATES) == set(EXCEL_TEMPLATES) == set(NOTION_TEMPLATES)
    assert len(NICHES) == 10


@pytest.mark.parametrize("niche", NICHES)
def test_pdf_templates_detailed(niche):
    pages = PDF_TEMPLATES[niche]
    assert len(pages) >= 4, f"{niche} pdf has too few pages"
    for page in pages:
        assert page["title"]
        assert len(page["sections"]) >= 2, f"{niche}/{page['title']} too thin"


@pytest.mark.parametrize("niche", NICHES)
def test_excel_templates_detailed(niche):
    sheets = EXCEL_TEMPLATES[niche]
    assert len(sheets) >= 3, f"{niche} excel has too few sheets"
    for sheet in sheets:
        assert sheet["name"]
        assert len(sheet["headers"]) >= 4, f"{niche}/{sheet['name']} too few headers"


@pytest.mark.parametrize("niche", NICHES)
def test_notion_templates_detailed(niche):
    blocks = NOTION_TEMPLATES[niche]
    assert len(blocks) >= 4, f"{niche} notion has too few blocks"
    for block in blocks:
        assert block["heading"]
        assert len(block["content"]) >= 40, f"{niche}/{block['heading']} content too short"


@pytest.mark.parametrize("raw,expected", [
    ("Finance & Budgeting", "finance"),
    ("budget planner", "finance"),
    ("Health & Fitness", "health"),
    ("Productivity", "productivity"),
    ("Business & Freelance", "business"),
    ("Wedding & Events", "wedding"),
    ("Student & Education", "student"),
    ("Travel", "travel"),
    ("Meal Planning", "meal"),
    ("Real Estate", "real estate"),
    ("Content Creator", "content"),
    ("something unknown", "productivity"),  # default
    (None, "productivity"),
    ("", "productivity"),
])
def test_match_niche(raw, expected):
    assert match_niche(raw) == expected


@pytest.mark.parametrize("ptype", TYPES)
@pytest.mark.parametrize("niche", NICHES)
def test_get_template_every_combination(ptype, niche):
    t = get_template(ptype, niche)
    key = {"pdf_planner": "pages", "excel_template": "sheets",
           "notion_template": "blocks"}[ptype]
    assert key in t
    assert len(t[key]) >= 3


def test_merge_spec_fills_thin_llm_output():
    thin = {"title": "My Planner", "pages": [
        {"title": "Cover", "sections": ["Intro"]}]}
    merged = merge_spec("pdf_planner", "finance", thin)
    # Library floor for finance pdf is 6 pages; thin spec had 1
    assert len(merged["pages"]) >= 4
    titles = [p["title"].lower() for p in merged["pages"]]
    assert "cover" in titles  # LLM page kept first


def test_merge_spec_keeps_rich_llm_output():
    rich = {"title": "T", "sheets": [
        {"name": f"Sheet {i}", "headers": ["A", "B", "C", "D"]} for i in range(6)]}
    merged = merge_spec("excel_template", "finance", rich)
    # Rich spec already exceeds floor — original sheets preserved in order
    assert merged["sheets"][0]["name"] == "Sheet 0"
    assert len(merged["sheets"]) >= 6


def test_merge_spec_no_duplicates():
    spec = {"blocks": [{"heading": "💰 Money Dashboard", "content": "Custom version"}]}
    merged = merge_spec("notion_template", "finance", spec)
    headings = [b["heading"].lower() for b in merged["blocks"]]
    assert len(headings) == len(set(headings)), "duplicate blocks after merge"
