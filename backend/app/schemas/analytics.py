from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    totals: dict
    products_by_status: dict
