"""Generates Etsy listing mockup images for products using Pillow.

Each product gets two images:
  1. Hero  — product cover on a styled gradient background
  2. Detail — inside-pages / sheet / blocks preview

Returns [] when Pillow is missing — never blocks the pipeline.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("generated_products")

PALETTES = {
    "pdf_planner":     ((26, 26, 46),  (79, 142, 247)),   # navy → blue
    "excel_template":  ((16, 60, 40),  (62, 207, 142)),   # forest → green
    "notion_template": ((40, 26, 60),  (180, 130, 250)),  # plum → violet
}

W, H = 1200, 900


def _gradient(draw, w, h, c1, c2):
    for y in range(h):
        t = y / h
        rgb = tuple(int(c1[i] + (c2[i] - c1[i]) * t * 0.6) for i in range(3))
        draw.line([(0, y), (w, y)], fill=rgb)


def _load_fonts():
    from PIL import ImageFont
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    big = small = tiny = None
    for path in candidates:
        try:
            big   = ImageFont.truetype(path, 52)
            small = ImageFont.truetype(path, 26)
            tiny  = ImageFont.truetype(path, 18)
            break
        except Exception:
            continue
    if big is None:
        big = small = tiny = ImageFont.load_default()
    return big, small, tiny


def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 <= width:
            cur = f"{cur} {w_}".strip()
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines[:4]


def generate_mockups(slug: str, title: str, product_type: str,
                     spec: dict[str, Any]) -> list[str]:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.warning("Pillow not installed — skipping mockups for %s", slug)
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    c1, c2 = PALETTES.get(product_type, PALETTES["pdf_planner"])
    big, small, tiny = _load_fonts()
    paths: list[str] = []

    # ── Hero image: cover card on gradient ────────────────────────────────────
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    _gradient(d, W, H, c1, c2)

    # paper card with soft shadow
    card = (W//2 - 280, 110, W//2 + 280, H - 110)
    d.rounded_rectangle([card[0]+10, card[1]+14, card[2]+10, card[3]+14],
                        24, fill=(0, 0, 0))
    d.rounded_rectangle(card, 24, fill=(252, 252, 250))

    # accent bar + title on card
    d.rounded_rectangle((card[0]+50, card[1]+70, card[0]+170, card[1]+82),
                        6, fill=c2)
    y = card[1] + 120
    for line in _wrap(title, 18):
        d.text((card[0]+50, y), line, font=big, fill=(26, 26, 46))
        y += 64

    # decorative content lines
    y += 30
    for i in range(7):
        lw = 380 if i % 3 else 300
        d.rounded_rectangle((card[0]+50, y, card[0]+50+lw, y+10), 5,
                            fill=(225, 228, 235))
        y += 34

    label = {"pdf_planner": "PRINTABLE PDF", "excel_template": "EXCEL TEMPLATE",
             "notion_template": "NOTION TEMPLATE"}[product_type]
    d.text((card[0]+50, card[3]-70), label, font=tiny, fill=c2)
    d.text((card[0]+50, card[3]-44), "Instant Digital Download", font=tiny,
           fill=(120, 125, 140))

    hero = OUTPUT_DIR / f"{slug}-mockup-1.png"
    img.save(hero, "PNG")
    paths.append(str(hero))

    # ── Detail image: type-specific inner preview ─────────────────────────────
    img2 = Image.new("RGB", (W, H))
    d2 = ImageDraw.Draw(img2)
    _gradient(d2, W, H, c1, c2)

    if product_type == "excel_template":
        sheets = spec.get("sheets", [])[:1]
        headers = (sheets[0].get("headers", ["A", "B", "C", "D"])
                   if sheets else ["A", "B", "C", "D"])[:6]
        card2 = (90, 130, W-90, H-130)
        d2.rounded_rectangle(card2, 18, fill=(252, 252, 250))
        cols = len(headers)
        cw = (card2[2]-card2[0]-80) // cols
        x0, y0 = card2[0]+40, card2[1]+50
        for ci, htext in enumerate(headers):
            d2.rectangle((x0+ci*cw, y0, x0+(ci+1)*cw-4, y0+44), fill=c2)
            d2.text((x0+ci*cw+10, y0+10), str(htext)[:12], font=tiny,
                    fill=(255, 255, 255))
        for r in range(8):
            ry = y0 + 52 + r*46
            fill = (240, 244, 252) if r % 2 == 0 else (252, 252, 250)
            d2.rectangle((x0, ry, x0+cols*cw-4, ry+42), fill=fill)
    else:
        items = (spec.get("pages") or spec.get("blocks") or [])[:4]
        y = 120
        for it in items:
            name = str(it.get("title") or it.get("heading") or "Section")
            d2.rounded_rectangle((110, y+8, W-100, y+158), 16, fill=(0, 0, 0))
            d2.rounded_rectangle((100, y, W-110, y+150), 16, fill=(252, 252, 250))
            d2.text((140, y+26), name[:42], font=small, fill=(26, 26, 46))
            for li in range(2):
                d2.rounded_rectangle((140, y+78+li*28, 700-li*120, y+88+li*28),
                                     5, fill=(225, 228, 235))
            y += 175

    d2.text((100, H-70), f"{title[:60]}", font=tiny, fill=(255, 255, 255))
    detail = OUTPUT_DIR / f"{slug}-mockup-2.png"
    img2.save(detail, "PNG")
    paths.append(str(detail))

    logger.info("mockups generated for %s: %s", slug, paths)
    return paths
