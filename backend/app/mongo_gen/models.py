from typing import Any, Literal
from pydantic import BaseModel, Field


class MongoQuerySpec(BaseModel):
    query_type: Literal["find", "aggregate"]
    collection: str
    filter: dict[str, Any] = Field(default_factory=dict)
    projection: dict[str, Any] = Field(default_factory=dict)
    sort: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=1000)
    pipeline: list[dict[str, Any]] = Field(default_factory=list)
