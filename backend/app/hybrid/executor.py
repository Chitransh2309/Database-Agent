import re
import time
from typing import Any

from ..llm.base import LLMProvider
from ..database.postgres_service import PostgresService
from ..database.mongo_service import MongoService
from ..sql_gen.generator import SQLGenerator
from ..mongo_gen.generator import MongoGenerator
from ..mongo_gen.models import MongoQuerySpec
from .models import HybridQueryPlan, HybridExecutionTrace

_SYSTEM = (
    "You are a database expert skilled in both PostgreSQL and MongoDB. "
    "You plan hybrid queries that retrieve data from both databases and specify how to fuse the results. "
    "Use only tables/collections and fields present in the provided schema. "
    "Return only valid JSON — no explanation, no markdown."
)

_PLAN_RULES = """
Rules for building the hybrid plan:

EXECUTION STRATEGY — choose one:
  "pg_to_mongo":
    Use when PostgreSQL calculates a subset first (e.g. entities above an aggregate threshold,
    recent transactions) and MongoDB must filter by those result IDs.
    The executor extracts join key values from the PG result and injects them into the Mongo query.
    Write the full PG SQL to produce the source subset.
    Write the Mongo spec WITHOUT a join key filter — executor adds it automatically.
  "mongo_to_pg":
    Use when MongoDB filters or aggregates first (e.g. entities matching a document-side condition
    or array aggregation) and PostgreSQL must retrieve details for those IDs.
    The executor extracts join key values from Mongo and injects them into the PG SQL.
    Write the Mongo spec to produce the filtered subset.
    Write the PG SQL to return ALL rows from the target table — DO NOT filter by join key.
    The executor adds the IN(...) filter automatically.
    CRITICAL: Do NOT put ANY(%s), = %s, IN (%s), or any parameter placeholder in the SQL.
              The SQL must be complete and executable as-is before executor injection.
  "parallel_then_fuse":
    Use only when both queries are fully independent and share a join key in both outputs.

JOIN KEYS — always set ALL that apply:
  pg_join_key: field name in PostgreSQL result for correlation (e.g. the shared entity ID column). REQUIRED.
  mongo_join_key: field name in MongoDB result for correlation (e.g. the shared entity ID field). REQUIRED.
  join_key: same as both keys when they share a name (set this AND both above).
  Always set pg_join_key and mongo_join_key explicitly — never leave them empty.
  For aggregate pipelines: always include the join key as a NAMED field in $group output.
  Do NOT rely on _id — it is removed from results.
  In $group, use: "<join_key_field>": {"$first": "$<join_key_field>"}
  Replace <join_key_field> with the actual field name from the schema.

STRING MATCHING — CRITICAL:
  Use UPPER() or ILIKE for all status/category/type comparisons to avoid case mismatch:
    UPPER(o.status) = 'COMPLETED'     (always safe)
    o.status ILIKE 'completed'        (PostgreSQL case-insensitive)
  Apply the same to MongoDB: use exact case as documented in the schema (e.g. "Open").

ABOVE-AVERAGE / HIGH-VALUE / TOP-PERFORMING SUBSET:
  Interpret phrases like "high purchases", "high-value", "top spenders", "most active",
  "above average <metric>" as: entities whose aggregate metric exceeds the average across all entities.
  Use execution_strategy="pg_to_mongo".
  General SQL pattern — replace ALL <placeholders> with actual column names from the schema:
    SELECT e.<pk_col>, e.<label_col>, SUM(t.<amount_col>) AS total_<metric>
    FROM <entity_table> e
    JOIN <fact_table> t ON e.<pk_col> = t.<fk_col>
    WHERE UPPER(t.<status_col>) = '<COMPLETED_VALUE>'
    GROUP BY e.<pk_col>, e.<label_col>
    HAVING SUM(t.<amount_col>) > (
      SELECT AVG(agg) FROM (
        SELECT SUM(<amount_col>) AS agg FROM <fact_table>
        WHERE UPPER(<status_col>) = '<COMPLETED_VALUE>'
        GROUP BY <fk_col>
      ) sub
    )
  Derive <entity_table>, <fact_table>, <pk_col>, <fk_col>, <amount_col>, <status_col>,
  and the completed-status literal from the schema context — never use these placeholder names literally.
  The MongoDB spec should retrieve documents WITHOUT filtering by the join key — executor injects it.

NESTED ARRAY / SUB-DOCUMENT AGGREGATION:
  When a collection field is an array of sub-documents, use query_type="aggregate".
  General pattern for conditional metric comparison across array sub-document categories
  — replace ALL <placeholders> with actual field names from the schema:
    [
      {"$unwind": "$<array_field>"},
      {"$group": {
        "_id": "$<entity_id_field>",
        "<entity_id_field>": {"$first": "$<entity_id_field>"},
        "<category_A>_total": {"$sum": {"$cond": [{"$eq": ["$<array_field>.<type_field>", "<value_A>"]}, "$<array_field>.<metric_field>", 0]}},
        "<category_B>_total": {"$sum": {"$cond": [{"$eq": ["$<array_field>.<type_field>", "<value_B>"]}, "$<array_field>.<metric_field>", 0]}}
      }},
      {"$match": {"$expr": {"$gt": ["$<category_A>_total", "$<category_B>_total"]}}},
      {"$project": {"_id": 0, "<entity_id_field>": 1, "<category_A>_total": 1, "<category_B>_total": 1}}
    ]
  Derive <array_field>, <entity_id_field>, <type_field>, <metric_field>, <value_A>, <value_B>
  entirely from the schema context — never use placeholder names literally in the generated query.
  Use execution_strategy="mongo_to_pg" to then fetch entity details from PostgreSQL.

JOIN STRATEGY:
  Use "inner_join" when both sides must have the key (most hybrid queries).
  Use "left_join" when you want all PG rows enriched with optional Mongo data.
  Use "union" only when there is no natural join key.

Only reference tables/collections and fields listed in the schema above.
Return ONLY valid JSON.
""".strip()


class HybridExecutor:
    """
    Plans and executes queries spanning PostgreSQL + MongoDB.

    execute()  — full pipeline: plan → run PG/Mongo (sequential or parallel) → fuse → trace
    plan()     — ask LLM for a HybridQueryPlan
    fuse()     — merge two result lists with one-to-many support and key normalization
    """

    def __init__(
        self,
        llm: LLMProvider,
        db: PostgresService,
        mongo: MongoService,
    ) -> None:
        self._llm = llm
        self._db = db
        self._mongo = mongo
        self._sql_gen = SQLGenerator(llm) if llm else None
        self._mongo_gen = MongoGenerator(llm) if llm else None

    # ── Public API ─────────────────────────────────────────────────────────

    async def plan(
        self,
        nl_query: str,
        schema_context: str,
    ) -> tuple["HybridQueryPlan | None", "str | None"]:
        """Ask the LLM to produce a HybridQueryPlan. Returns (plan, error)."""
        prompt = (
            f"Database schema (PostgreSQL + MongoDB combined):\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            f"{_PLAN_RULES}"
        )
        try:
            result: HybridQueryPlan = await self._llm.generate_structured(
                prompt=prompt,
                response_schema=HybridQueryPlan,
                system_instruction=_SYSTEM,
            )
            return result, None
        except Exception as exc:
            return None, str(exc)

    async def execute(
        self,
        nl_query: str,
        schema_context: str,
        repair_history: list[dict] | None = None,
        repair_attempts: int = 0,
        max_repair: int = 3,
    ) -> dict[str, Any]:
        """
        Full hybrid execution pipeline.

        Returns a dict with result_rows, result_columns, hybrid_plan, hybrid_trace,
        message, repair_attempts, repair_history, and optionally error.
        """
        t_start = time.perf_counter()
        trace = HybridExecutionTrace(query=nl_query)
        repair_history = list(repair_history or [])

        # ── Plan ───────────────────────────────────────────────────────────
        plan, plan_error = await self.plan(nl_query, schema_context)
        if plan_error or plan is None:
            trace.errors.append(f"plan_error: {plan_error}")
            return {
                "error": f"Hybrid query planning failed: {plan_error}",
                "message": "Could not generate a hybrid query plan.",
                "hybrid_trace": trace.model_dump(),
                "repair_attempts": repair_attempts,
                "repair_history": repair_history,
            }

        # Sanitize: strip any LLM-generated parameter placeholders from the SQL
        clean_sql = self._strip_param_placeholders(plan.sql_query)
        if clean_sql != plan.sql_query:
            plan = plan.model_copy(update={"sql_query": clean_sql})

        pg_key = plan.pg_join_key or plan.join_key
        mongo_key = plan.mongo_join_key or plan.join_key
        trace.execution_strategy = plan.execution_strategy
        trace.join_mapping = f"PG.{pg_key} ↔ Mongo.{mongo_key}"

        pg_rows: list[dict] = []
        mongo_rows: list[dict] = []
        intermediate_ids: list = []

        # ── Execute by strategy ────────────────────────────────────────────
        if plan.execution_strategy == "pg_to_mongo":
            # Step 1: run PG to get the "source" subset
            t_pg = time.perf_counter()
            pg_rows, pg_error, plan, repair_history, repair_attempts = await self._run_pg(
                plan, schema_context, nl_query, repair_history, repair_attempts, max_repair
            )
            trace.pg_latency_ms = (time.perf_counter() - t_pg) * 1000
            trace.pg_row_count = len(pg_rows)
            if pg_error:
                trace.errors.append(f"pg_error: {pg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": pg_error,
                    "message": "Hybrid: PostgreSQL step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

            # Step 2: extract intermediate IDs from PG result
            intermediate_ids = self._extract_ids(pg_rows, pg_key)
            trace.intermediate_id_count = len(intermediate_ids)

            # Step 3: inject IDs into Mongo spec and run Mongo
            injected_spec = self._inject_ids_into_mongo_spec(
                plan.mongo_spec, mongo_key, intermediate_ids
            )
            plan = plan.model_copy(update={"mongo_spec": injected_spec})

            t_mg = time.perf_counter()
            mongo_rows, mg_error = self._run_mongo(plan.mongo_spec)
            trace.mongo_latency_ms = (time.perf_counter() - t_mg) * 1000
            trace.mongo_row_count = len(mongo_rows)
            if mg_error:
                trace.errors.append(f"mongo_error: {mg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": mg_error,
                    "message": "Hybrid: MongoDB step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

        elif plan.execution_strategy == "mongo_to_pg":
            # Step 1: run Mongo to get the "source" subset
            t_mg = time.perf_counter()
            mongo_rows, mg_error = self._run_mongo(plan.mongo_spec)
            trace.mongo_latency_ms = (time.perf_counter() - t_mg) * 1000
            trace.mongo_row_count = len(mongo_rows)
            if mg_error:
                trace.errors.append(f"mongo_error: {mg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": mg_error,
                    "message": "Hybrid: MongoDB step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

            # Step 2: extract intermediate IDs from Mongo result
            intermediate_ids = self._extract_ids(mongo_rows, mongo_key)
            trace.intermediate_id_count = len(intermediate_ids)

            # Step 3: inject IDs into PG SQL and run PG
            injected_sql = self._inject_ids_into_sql(plan.sql_query, pg_key, intermediate_ids)
            plan = plan.model_copy(update={"sql_query": injected_sql})

            t_pg = time.perf_counter()
            pg_rows, pg_error, plan, repair_history, repair_attempts = await self._run_pg(
                plan, schema_context, nl_query, repair_history, repair_attempts, max_repair
            )
            trace.pg_latency_ms = (time.perf_counter() - t_pg) * 1000
            trace.pg_row_count = len(pg_rows)
            if pg_error:
                trace.errors.append(f"pg_error: {pg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": pg_error,
                    "message": "Hybrid: PostgreSQL step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

        else:  # parallel_then_fuse
            t_pg = time.perf_counter()
            pg_rows, pg_error, plan, repair_history, repair_attempts = await self._run_pg(
                plan, schema_context, nl_query, repair_history, repair_attempts, max_repair
            )
            trace.pg_latency_ms = (time.perf_counter() - t_pg) * 1000
            trace.pg_row_count = len(pg_rows)
            if pg_error:
                trace.errors.append(f"pg_error: {pg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": pg_error,
                    "message": "Hybrid: PostgreSQL step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

            t_mg = time.perf_counter()
            mongo_rows, mg_error = self._run_mongo(plan.mongo_spec)
            trace.mongo_latency_ms = (time.perf_counter() - t_mg) * 1000
            trace.mongo_row_count = len(mongo_rows)
            if mg_error:
                trace.errors.append(f"mongo_error: {mg_error}")
                trace.total_latency_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "error": mg_error,
                    "message": "Hybrid: MongoDB step failed.",
                    "hybrid_plan": plan.model_dump(),
                    "hybrid_trace": trace.model_dump(),
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }

        # ── Validate ───────────────────────────────────────────────────────
        t_fuse = time.perf_counter()
        warnings = self._validate_plan(plan, pg_rows, mongo_rows)
        trace.validation_warnings = warnings

        # ── Fuse ───────────────────────────────────────────────────────────
        fused = self.fuse(pg_rows, mongo_rows, plan)
        trace.fusion_latency_ms = (time.perf_counter() - t_fuse) * 1000
        trace.final_row_count = len(fused)
        trace.repair_attempts = repair_attempts
        trace.total_latency_ms = (time.perf_counter() - t_start) * 1000

        columns = list(fused[0].keys()) if fused else []

        return {
            "hybrid_plan": plan.model_dump(),
            "result_rows": fused,
            "result_columns": columns,
            "hybrid_trace": trace.model_dump(),
            "message": (
                f"Hybrid query ({plan.execution_strategy}): "
                f"{len(pg_rows)} PG row(s) + {len(mongo_rows)} Mongo doc(s) "
                f"→ {len(fused)} fused result(s) via '{plan.join_strategy}'."
            ),
            "repair_attempts": repair_attempts,
            "repair_history": repair_history,
        }

    def fuse(
        self,
        pg_rows: list[dict],
        mongo_rows: list[dict],
        plan: HybridQueryPlan,
    ) -> list[dict]:
        """
        Merge two result lists using the strategy from the plan.

        Supports one-to-many relationships (one customer → multiple tickets).
        Normalizes join key types (int 3 matches string "3" matches float 3.0).

        union      — concatenate (no join key)
        inner_join — only rows where join_key appears in both sets
        left_join  — all PG rows; each row expanded for every matching Mongo doc
        """
        pg_key = plan.pg_join_key or plan.join_key
        mongo_key = plan.mongo_join_key or plan.join_key

        if plan.join_strategy == "union" or not pg_key:
            return pg_rows + mongo_rows

        # Build one-to-many index on the Mongo side
        mongo_index: dict[str, list[dict]] = {}
        for doc in mongo_rows:
            k = doc.get(mongo_key)
            if k is None:
                continue
            norm_k = self._normalize_key(k)
            mongo_index.setdefault(norm_k, []).append(doc)

        if plan.join_strategy == "inner_join":
            result: list[dict] = []
            for row in pg_rows:
                pg_val = self._normalize_key(row.get(pg_key, ""))
                for mdoc in mongo_index.get(pg_val, []):
                    result.append({**row, **mdoc})
            return result

        # left_join
        result = []
        for row in pg_rows:
            pg_val = self._normalize_key(row.get(pg_key, ""))
            mongo_docs = mongo_index.get(pg_val, [])
            if mongo_docs:
                for mdoc in mongo_docs:
                    result.append({**row, **mdoc})
            else:
                result.append({**row})
        return result

    # ── Static helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _strip_param_placeholders(sql: str) -> str:
        """
        Remove LLM-generated parameter placeholders (%s, ?, :param, ANY(%s)) that would
        break SQLAlchemy. For mongo_to_pg plans, the LLM may wrongly add a parameterized
        join-key condition; the executor injects the actual IN(...) filter separately.
        """
        # AND field = ANY(%s)  →  remove entire clause
        sql = re.sub(r'\bAND\s+\S+\s*=\s*ANY\s*\(\s*%s\s*\)', '', sql, flags=re.IGNORECASE)
        # WHERE field = ANY(%s)  →  WHERE TRUE (preserve SQL structure)
        sql = re.sub(r'\bWHERE\s+\S+\s*=\s*ANY\s*\(\s*%s\s*\)', 'WHERE TRUE', sql, flags=re.IGNORECASE)
        # AND field IN (%s)  →  remove
        sql = re.sub(r'\bAND\s+\S+\s+IN\s*\(\s*%s\s*\)', '', sql, flags=re.IGNORECASE)
        # WHERE field IN (%s)  →  WHERE TRUE
        sql = re.sub(r'\bWHERE\s+\S+\s+IN\s*\(\s*%s\s*\)', 'WHERE TRUE', sql, flags=re.IGNORECASE)
        # AND field = %s / = ? / = :param  →  remove
        sql = re.sub(r'\bAND\s+\S+\s*=\s*(%s|\?|:\w+)', '', sql, flags=re.IGNORECASE)
        # WHERE field = %s / = ? / = :param  →  WHERE TRUE
        sql = re.sub(r'\bWHERE\s+\S+\s*=\s*(%s|\?|:\w+)', 'WHERE TRUE', sql, flags=re.IGNORECASE)
        return sql.strip()

    @staticmethod
    def _normalize_key(value: Any) -> str:
        """
        Normalize a join key value to a consistent string for comparison.
        Handles int/float/str mismatches: 3, 3.0, "3" all map to "3".
        """
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def _extract_ids(rows: list[dict], key_field: str) -> list:
        """
        Extract unique join key values from a list of dicts, preserving original type.
        Deduplication is done using normalized string comparison.
        """
        seen: set[str] = set()
        ids: list = []
        for row in rows:
            val = row.get(key_field)
            if val is None:
                continue
            norm = HybridExecutor._normalize_key(val)
            if norm not in seen:
                seen.add(norm)
                ids.append(val)
        return ids

    @staticmethod
    def _inject_ids_into_mongo_spec(
        spec: MongoQuerySpec, join_key: str, ids: list
    ) -> MongoQuerySpec:
        """
        Add {join_key: {$in: ids}} to the Mongo spec.
        For aggregate pipelines, prepends a $match stage.
        When ids is empty, returns a spec with an impossible filter (yields 0 docs).
        """
        if not ids:
            return spec.model_copy(
                update={"filter": {"__hybrid_no_match__": True}, "pipeline": []}
            )

        if spec.query_type == "find":
            new_filter = {**spec.filter, join_key: {"$in": ids}}
            return spec.model_copy(update={"filter": new_filter})
        else:  # aggregate
            match_stage: dict = {"$match": {join_key: {"$in": ids}}}
            # Remove any pre-existing $match on the same key to avoid conflicts
            cleaned = [
                s for s in spec.pipeline
                if not (
                    len(s) == 1
                    and "$match" in s
                    and join_key in s["$match"]
                )
            ]
            new_pipeline = [match_stage] + cleaned
            return spec.model_copy(update={"pipeline": new_pipeline})

    @staticmethod
    def _inject_ids_into_sql(sql: str, join_key: str, ids: list) -> str:
        """
        Wrap the SQL in a subquery and filter rows where join_key IN (ids).
        Handles any SQL shape including CTEs (WITH ...).
        When ids is empty, returns a query that yields 0 rows.
        """
        sql_stripped = sql.strip().rstrip(";")

        if not ids:
            return f"SELECT * FROM ({sql_stripped}) AS __hybrid_base WHERE FALSE"

        id_parts: list[str] = []
        for v in ids:
            if isinstance(v, bool):
                id_parts.append("TRUE" if v else "FALSE")
            elif isinstance(v, int):
                id_parts.append(str(v))
            elif isinstance(v, float):
                id_parts.append(str(int(v)) if v.is_integer() else str(v))
            else:
                escaped = str(v).replace("'", "''")
                id_parts.append(f"'{escaped}'")
        id_list = ", ".join(id_parts)

        return (
            f"SELECT * FROM (\n{sql_stripped}\n) AS __hybrid_base\n"
            f"WHERE __hybrid_base.{join_key} IN ({id_list})"
        )

    # ── Validation ─────────────────────────────────────────────────────────

    def _validate_plan(
        self,
        plan: HybridQueryPlan,
        pg_rows: list[dict],
        mongo_rows: list[dict],
    ) -> list[str]:
        """
        Validate that correlation keys are present in the result sets.
        Returns a list of warning strings (non-fatal); empty means all good.
        """
        warnings: list[str] = []
        pg_key = plan.pg_join_key or plan.join_key
        mongo_key = plan.mongo_join_key or plan.join_key

        if not pg_key and not mongo_key:
            warnings.append(
                "No join key specified — results will be union-combined. "
                "Set join_key, pg_join_key, or mongo_join_key if a correlation exists."
            )
            return warnings

        if pg_rows and pg_key:
            sample = pg_rows[0]
            if pg_key not in sample:
                warnings.append(
                    f"pg_join_key '{pg_key}' absent from PostgreSQL result. "
                    f"Available columns: {list(sample.keys())}."
                )

        if mongo_rows and mongo_key:
            sample = mongo_rows[0]
            if mongo_key not in sample:
                warnings.append(
                    f"mongo_join_key '{mongo_key}' absent from MongoDB result. "
                    f"Available fields: {list(sample.keys())}. "
                    "Hint: if using $group, preserve the key with "
                    f'e.g. "{mongo_key}": {{"$first": "${mongo_key}"}} in the $group stage.'
                )

        return warnings

    # ── Private execution helpers ──────────────────────────────────────────

    async def _run_pg(
        self,
        plan: HybridQueryPlan,
        schema_context: str,
        nl_query: str,
        repair_history: list[dict],
        repair_attempts: int,
        max_repair: int,
    ) -> tuple[list[dict], "str | None", HybridQueryPlan, list[dict], int]:
        """Execute the PG SQL with repair loop. Returns (rows, error, plan, history, attempts)."""
        sql = plan.sql_query
        while True:
            try:
                result = self._db.execute_query(sql)
                updated_plan = plan.model_copy(update={"sql_query": sql})
                return result["rows"], None, updated_plan, repair_history, repair_attempts
            except Exception as exc:
                db_error = str(exc)
                if repair_attempts >= max_repair or self._sql_gen is None:
                    return (
                        [],
                        f"PostgreSQL execution failed after {repair_attempts} repair(s): {db_error}",
                        plan,
                        repair_history,
                        repair_attempts,
                    )
                repair_history.append({
                    "attempt": repair_attempts + 1,
                    "sql": sql,
                    "error": db_error,
                    "stage": "hybrid_pg",
                })
                repair_attempts += 1
                repaired_sql, repair_error = await self._sql_gen.repair(
                    sql, db_error, schema_context, nl_query
                )
                if repair_error or repaired_sql is None:
                    return (
                        [],
                        f"PostgreSQL repair failed: {repair_error}",
                        plan,
                        repair_history,
                        repair_attempts,
                    )
                sql = repaired_sql

    def _run_mongo(
        self,
        spec: MongoQuerySpec,
    ) -> tuple[list[dict], "str | None"]:
        """Execute a MongoQuerySpec. Returns (rows, error)."""
        try:
            if spec.query_type == "aggregate":
                rows = self._mongo.aggregate(spec.collection, spec.pipeline, spec.limit)
            else:
                rows = self._mongo.find_with_spec(
                    spec.collection, spec.filter, spec.projection, spec.sort, spec.limit
                )
            return rows, None
        except Exception as exc:
            return [], str(exc)
