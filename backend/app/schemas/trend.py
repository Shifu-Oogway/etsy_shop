from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    niche: str
    score: float
    source: str
    details: dict
    created_at: datetime
