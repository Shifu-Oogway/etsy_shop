from pydantic import BaseModel


class Message(BaseModel):
    detail: str


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int
