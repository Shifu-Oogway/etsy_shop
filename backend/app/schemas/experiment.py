from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.experiment import ExperimentStatus


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    hypothesis: str
    status: ExperimentStatus
    variants: dict
    results: dict
    created_at: datetime
