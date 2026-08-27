from typing import Literal
from pydantic import BaseModel, Field

from ..mongo_gen.models import MongoQuerySpec


class HybridExecutionTrace(BaseModel):
    """Structured trace for debugging and research evaluation of hybrid queries."""

    query: str = ""
    classification: str = ""
    execution_strategy: str = ""
    join_mapping: str = ""
    pg_row_count: int = 0
    mongo_row_count: int = 0
    intermediate_id_count: int = 0
    final_row_count: int = 0
    repair_attempts: int = 0
    pg_latency_ms: float = 0.0
    mongo_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)


class HybridQueryPlan(BaseModel):
    sql_query: str = Field(
        description="Valid PostgreSQL SQL for the relational part of the query."
    )
    mongo_spec: MongoQuerySpec = Field(
        description="MongoDB query spec for the document part of the query."
    )

    # ── Per-side join key fields ───────────────────────────────────────────
    pg_join_key: str = Field(
        default="",
        description=(
            "Field name in the PostgreSQL result set used as the correlation/join key. "
            "Leave empty if join_key covers both sides."
        ),
    )
    mongo_join_key: str = Field(
        default="",
        description=(
            "Field name in the MongoDB result set used as the correlation/join key. "
            "Leave empty if join_key covers both sides."
        ),
    )
    join_key: str = Field(
        default="",
        description=(
            "Shared field name present in both result sets when both sides use the same name. "
            "If pg_join_key and mongo_join_key differ, set both of those and leave this empty."
        ),
    )

    # ── Strategy fields ────────────────────────────────────────────────────
    join_strategy: Literal["left_join", "inner_join", "union"] = Field(
        default="inner_join",
        description=(
            "How to combine results: "
            "'left_join' — all PG rows enriched with matching Mongo data; "
            "'inner_join' — only rows present in both; "
            "'union' — concatenate both result sets (use when join_key is empty)."
        ),
    )
    execution_strategy: Literal["parallel_then_fuse", "pg_to_mongo", "mongo_to_pg"] = Field(
        default="parallel_then_fuse",
        description=(
            "parallel_then_fuse — run both queries independently then fuse; "
            "pg_to_mongo — run PostgreSQL first, extract join key values, inject into MongoDB query; "
            "mongo_to_pg — run MongoDB first, extract join key values, inject into PostgreSQL query."
        ),
    )
    explanation: str = Field(
        default="",
        description="One sentence explaining why this hybrid plan was chosen.",
    )
