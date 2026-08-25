from typing import Literal
from pydantic import BaseModel, Field

from ..mongo_gen.models import MongoQuerySpec


class HybridQueryPlan(BaseModel):
    sql_query: str = Field(
        description="Valid PostgreSQL SQL for the relational part of the query."
    )
    mongo_spec: MongoQuerySpec = Field(
        description="MongoDB query spec for the document part of the query."
    )
    join_key: str = Field(
        default="",
        description=(
            "Shared field name present in both result sets to join on "
            "(e.g. 'user_id', 'order_id'). Leave empty when there is no natural join key."
        ),
    )
    join_strategy: Literal["left_join", "inner_join", "union"] = Field(
        default="left_join",
        description=(
            "How to combine results: "
            "'left_join' — all PG rows enriched with matching Mongo data; "
            "'inner_join' — only rows present in both; "
            "'union' — concatenate both result sets (use when schemas differ or join_key is empty)."
        ),
    )
    explanation: str = Field(
        default="",
        description="One sentence explaining the hybrid plan.",
    )
