"""Product deduplication — semantic when embeddings are available, lexical always.

check_duplicate() compares a candidate title against recent products:
  1. Lexical: difflib ratio on normalized titles (always works, no deps)
  2. Semantic: cosine similarity of Ollama embeddings (when reachable);
     the embedding is also persisted for future checks.
"""
from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding
from app.models.product import Product

logger = logging.getLogger(__name__)

LEXICAL_THRESHOLD = 0.82
SEMANTIC_THRESHOLD = 0.92


def _normalize(title: str) -> str:
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    t = re.sub(r"\b(20\d\d|printable|digital|download|template|pdf|excel|notion)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def lexical_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


async def check_duplicate(db: AsyncSession, title: str, llm=None,
                          limit: int = 200) -> dict:
    """Returns {"duplicate": bool, "match": str|None, "score": float, "method": str}."""
    rows = await db.execute(
        select(Product.id, Product.title).order_by(Product.id.desc()).limit(limit))
    existing = rows.all()

    # 1) lexical — always
    best_score, best_title = 0.0, None
    for _, ex_title in existing:
        s = lexical_similarity(title, ex_title)
        if s > best_score:
            best_score, best_title = s, ex_title
    if best_score >= LEXICAL_THRESHOLD:
        return {"duplicate": True, "match": best_title,
                "score": round(best_score, 3), "method": "lexical"}

    # 2) semantic — best effort
    if llm is not None and existing:
        try:
            vec = await llm.embed(title)
            if vec:
                ids = [pid for pid, _ in existing]
                emb_rows = await db.execute(
                    select(Embedding).where(Embedding.ref_type == "product",
                                            Embedding.ref_id.in_(ids)))
                for emb in emb_rows.scalars():
                    sim = _cosine(vec, list(emb.vector or []))
                    if sim >= SEMANTIC_THRESHOLD:
                        match = next((t for pid, t in existing
                                      if pid == emb.ref_id), None)
                        return {"duplicate": True, "match": match,
                                "score": round(sim, 3), "method": "semantic"}
        except Exception as exc:
            logger.debug("semantic dedup skipped: %s", exc)

    return {"duplicate": False, "match": best_title,
            "score": round(best_score, 3), "method": "lexical"}


async def store_embedding(db: AsyncSession, product_id: int, title: str,
                          llm=None) -> None:
    """Persist a title embedding for future semantic dedup. Best effort."""
    if llm is None:
        return
    try:
        vec = await llm.embed(title)
        if vec:
            db.add(Embedding(ref_type="product", ref_id=product_id,
                             vector=vec, meta={"title": title}))
            await db.flush()
    except Exception as exc:
        logger.debug("store_embedding skipped: %s", exc)
