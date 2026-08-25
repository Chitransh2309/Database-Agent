from typing import Any, Optional
from typing_extensions import TypedDict

from ..intent.models import IntentResult


class PipelineState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────
    nl_query: str

    # ── Populated by classify_intent node ─────────────────────────────────
    intent: Optional[IntentResult]

    # ── Populated by retrieve_schema node ─────────────────────────────────
    schema_context: str
    context_objects: list[str]

    # ── Populated by generate_sql node ───────────────────────────────────
    sql: Optional[str]

    # ── Populated by schema_ops / mongo_ops nodes ─────────────────────────
    ddl: Optional[str]

    # ── Populated by mongo_query node ────────────────────────────────────
    mongo_query_spec: Optional[dict]

    # ── Populated by hybrid_query node ───────────────────────────────────
    hybrid_plan: Optional[dict]

    # ── Populated by execute_sql node (visualization intent only) ─────────
    viz_spec: Optional[dict]

    # ── Populated by execute_sql node ─────────────────────────────────────
    result_rows: list[dict[str, Any]]
    result_columns: list[str]

    # ── Control / output ──────────────────────────────────────────────────
    error: Optional[str]
    message: str
    repair_attempts: int
    # Each entry: {attempt, sql, error, stage} where stage is "syntax" or "execution"
    repair_history: list[dict[str, Any]]
