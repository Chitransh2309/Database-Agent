from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START

from .state import PipelineState
from ..intent.models import IntentType, TargetDB
from ..intent.classifier import IntentClassifier
from ..llm.base import LLMProvider
from ..database.postgres_service import PostgresService
from ..database.mongo_service import MongoService
from ..sql_gen.generator import SQLGenerator
from ..mongo_gen.generator import MongoGenerator
from ..hybrid.executor import HybridExecutor
from ..schema_ops.ddl_generator import DDLGenerator
from ..viz.generator import VizGenerator
from ..config import settings


class _CollectionSpec(BaseModel):
    collection_name: str = Field(
        description="The exact name of the MongoDB collection to create."
    )


class PlannerService:
    """
    LangGraph workflow:
      classify_intent → retrieve_schema → [route] → execute → END

    Routes:
      query/crud/visualization + PG    → generate_sql → execute_sql
      query/crud/visualization + Mongo → mongo_query
      query/crud/visualization + both  → hybrid_query
      hybrid_query intent              → hybrid_query
      explanation                      → explain_schema
      table/schema/db creation         → schema_ops   (DDL generation + execution)
      collection_creation              → mongo_ops    (collection creation)
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
        self._classifier = IntentClassifier(llm)
        self._sql_gen = SQLGenerator(llm)
        self._mongo_gen = MongoGenerator(llm)
        self._hybrid_exec = HybridExecutor(llm, db, mongo)
        self._ddl_gen = DDLGenerator(llm)
        self._viz_gen = VizGenerator(llm)
        self._graph = self._build_graph()

    # ── Nodes ─────────────────────────────────────────────────────────────

    async def _classify_intent(self, state: PipelineState) -> dict:
        from ..semantic_twin.twin_service import get_twin_service
        twin_svc = get_twin_service()
        objects = twin_svc.twin.objects

        # Build a compact per-source schema view so the classifier can see
        # which columns each entity has and which DB it lives in.
        pg_objs = [o for o in objects if o.source == "postgresql"]
        mg_objs = [o for o in objects if o.source == "mongodb"]

        parts: list[str] = []
        if pg_objs:
            lines = [
                f"  {o.name}({', '.join(c.name for c in o.columns[:10])})"
                for o in pg_objs
            ]
            parts.append("PostgreSQL tables:\n" + "\n".join(lines))
        if mg_objs:
            lines = [
                f"  {o.name}({', '.join(c.name for c in o.columns[:10])})"
                for o in mg_objs
            ]
            parts.append("MongoDB collections:\n" + "\n".join(lines))

        # Surface potential join keys so the LLM knows when hybrid IS valid
        links = twin_svc.twin.cross_db_links()
        if links:
            parts.append("Potential cross-DB join keys:\n" + "\n".join(links))

        schema_hint = "\n\n".join(parts) if parts else None

        intent = await self._classifier.classify(
            state["nl_query"],
            schema_hint=schema_hint,
        )
        return {"intent": intent}

    async def _retrieve_schema(self, state: PipelineState) -> dict:
        from ..semantic_twin.twin_service import get_twin_service
        twin = get_twin_service()
        if not twin.twin.objects:
            return {"schema_context": "", "context_objects": []}
        retrieved = await twin.retrieve(state["nl_query"], k=6)
        names = [o.name for o in retrieved]
        ctx = twin.twin.get_context_for_objects(names)
        return {"schema_context": ctx, "context_objects": names}

    async def _generate_sql(self, state: PipelineState) -> dict:
        """Generate SQL with SQLGlot syntax guard and self-healing repair loop."""
        schema_context = state.get("schema_context", "")
        if not schema_context.strip():
            return {
                "error": "No schema context — no tables found in the database.",
                "message": "No tables in the database yet.",
            }

        nl_query = state["nl_query"]
        repair_history: list[dict] = list(state.get("repair_history") or [])
        repair_attempts: int = state.get("repair_attempts", 0)
        max_attempts: int = settings.MAX_REPAIR_ATTEMPTS

        sql, syntax_error = await self._sql_gen.generate(
            nl_query, schema_context, repair_history or None
        )

        while syntax_error and repair_attempts < max_attempts:
            repair_history.append({
                "attempt": repair_attempts + 1,
                "sql": sql,
                "error": syntax_error,
                "stage": "syntax",
            })
            repair_attempts += 1
            sql, syntax_error = await self._sql_gen.repair(
                sql, syntax_error, schema_context, nl_query
            )

        result: dict = {
            "sql": sql,
            "repair_attempts": repair_attempts,
            "repair_history": repair_history,
        }
        if syntax_error:
            result["error"] = f"Syntax repair failed after {repair_attempts} attempt(s): {syntax_error}"
            result["message"] = "Could not produce valid SQL syntax."
        return result

    async def _execute_sql(self, state: PipelineState) -> dict:
        """Execute SQL; repair and retry on DB errors up to MAX_REPAIR_ATTEMPTS."""
        if state.get("error") or not state.get("sql"):
            return {}

        sql = state["sql"]
        schema_context = state.get("schema_context", "")
        nl_query = state["nl_query"]
        repair_history: list[dict] = list(state.get("repair_history") or [])
        repair_attempts: int = state.get("repair_attempts", 0)
        max_attempts: int = settings.MAX_REPAIR_ATTEMPTS

        while True:
            try:
                result = self._db.execute_query(sql)
                rows = result["rows"]
                columns = result.get("columns", [])

                # Generate viz spec for visualization intent
                viz_spec_dict = None
                intent = state.get("intent")
                if (
                    intent
                    and intent.intent == IntentType.visualization
                    and rows
                    and columns
                ):
                    viz, _ = await self._viz_gen.generate(
                        state["nl_query"], columns, rows[:5]
                    )
                    if viz:
                        viz_spec_dict = viz.model_dump()

                return {
                    "sql": sql,
                    "result_rows": rows,
                    "result_columns": columns,
                    "viz_spec": viz_spec_dict,
                    "message": f"Returned {len(rows)} row(s).",
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }
            except Exception as exc:
                db_error = str(exc)
                if repair_attempts >= max_attempts:
                    return {
                        "sql": sql,
                        "error": db_error,
                        "message": f"Execution failed after {repair_attempts} repair attempt(s).",
                        "repair_attempts": repair_attempts,
                        "repair_history": repair_history,
                    }
                repair_history.append({
                    "attempt": repair_attempts + 1,
                    "sql": sql,
                    "error": db_error,
                    "stage": "execution",
                })
                repair_attempts += 1
                sql, _ = await self._sql_gen.repair(
                    sql, db_error, schema_context, nl_query
                )

    async def _mongo_query(self, state: PipelineState) -> dict:
        """Generate and execute a MongoDB find/aggregate query with repair loop."""
        # Use MongoDB-only context so the generator never sees PostgreSQL table names.
        from ..semantic_twin.twin_service import get_twin_service
        twin_svc = get_twin_service()
        mongo_objects = [o for o in twin_svc.twin.objects if o.source == "mongodb"]
        if mongo_objects:
            schema_context = "\n".join(o.to_context_string() for o in mongo_objects)
        else:
            schema_context = state.get("schema_context", "")

        if not schema_context.strip():
            return {
                "error": "No schema context — no collections found in the database.",
                "message": "No collections in the database yet.",
            }

        nl_query = state["nl_query"]
        repair_history: list[dict] = list(state.get("repair_history") or [])
        repair_attempts: int = state.get("repair_attempts", 0)
        max_attempts: int = settings.MAX_REPAIR_ATTEMPTS

        spec, gen_error = await self._mongo_gen.generate(nl_query, schema_context)
        if gen_error or spec is None:
            return {
                "error": f"MongoDB query generation failed: {gen_error}",
                "message": "Could not generate a MongoDB query.",
            }

        while True:
            try:
                if spec.query_type == "aggregate":
                    rows = self._mongo.aggregate(spec.collection, spec.pipeline, spec.limit)
                else:
                    rows = self._mongo.find_with_spec(
                        spec.collection, spec.filter, spec.projection, spec.sort, spec.limit
                    )
                return {
                    "mongo_query_spec": spec.model_dump(),
                    "result_rows": rows,
                    "result_columns": list(rows[0].keys()) if rows else [],
                    "message": f"Returned {len(rows)} document(s) from '{spec.collection}'.",
                    "repair_attempts": repair_attempts,
                    "repair_history": repair_history,
                }
            except Exception as exc:
                db_error = str(exc)
                if repair_attempts >= max_attempts:
                    return {
                        "mongo_query_spec": spec.model_dump(),
                        "error": db_error,
                        "message": f"MongoDB execution failed after {repair_attempts} repair attempt(s).",
                        "repair_attempts": repair_attempts,
                        "repair_history": repair_history,
                    }
                repair_history.append({
                    "attempt": repair_attempts + 1,
                    "query": spec.model_dump_json(),
                    "error": db_error,
                    "stage": "mongo_execution",
                })
                repair_attempts += 1
                spec, repair_error = await self._mongo_gen.repair(
                    spec.model_dump_json(), db_error, schema_context, nl_query
                )
                if spec is None:
                    return {
                        "error": f"MongoDB repair failed: {repair_error}",
                        "message": "Could not repair the MongoDB query.",
                        "repair_attempts": repair_attempts,
                        "repair_history": repair_history,
                    }

    async def _hybrid_query(self, state: PipelineState) -> dict:
        """Plan and execute a query spanning PostgreSQL + MongoDB; fuse results in Python."""
        schema_context = state.get("schema_context", "")
        if not schema_context.strip():
            return {
                "error": "No schema context — database appears empty.",
                "message": "No tables or collections found.",
            }

        nl_query = state["nl_query"]

        plan, plan_error = await self._hybrid_exec.plan(nl_query, schema_context)
        if plan_error or plan is None:
            return {
                "error": f"Hybrid query planning failed: {plan_error}",
                "message": "Could not generate a hybrid query plan.",
            }

        # Execute PostgreSQL part
        pg_rows: list[dict] = []
        try:
            sql_result = self._db.execute_query(plan.sql_query)
            pg_rows = sql_result["rows"]
        except Exception as exc:
            repaired_sql, _ = await self._sql_gen.repair(
                plan.sql_query, str(exc), schema_context, nl_query
            )
            try:
                sql_result = self._db.execute_query(repaired_sql)
                pg_rows = sql_result["rows"]
                plan = plan.model_copy(update={"sql_query": repaired_sql})
            except Exception as exc2:
                return {
                    "error": f"PostgreSQL part failed: {exc2}",
                    "message": "Hybrid query: PostgreSQL execution failed.",
                    "hybrid_plan": plan.model_dump(),
                }

        # Execute MongoDB part
        mongo_rows: list[dict] = []
        try:
            spec = plan.mongo_spec
            if spec.query_type == "aggregate":
                mongo_rows = self._mongo.aggregate(spec.collection, spec.pipeline, spec.limit)
            else:
                mongo_rows = self._mongo.find_with_spec(
                    spec.collection, spec.filter, spec.projection, spec.sort, spec.limit
                )
        except Exception as exc:
            return {
                "error": f"MongoDB part failed: {exc}",
                "message": "Hybrid query: MongoDB execution failed.",
                "hybrid_plan": plan.model_dump(),
            }

        fused = self._hybrid_exec.fuse(pg_rows, mongo_rows, plan)
        columns = list(fused[0].keys()) if fused else []

        return {
            "hybrid_plan": plan.model_dump(),
            "result_rows": fused,
            "result_columns": columns,
            "message": (
                f"Hybrid query: {len(pg_rows)} PG row(s) + {len(mongo_rows)} Mongo doc(s) "
                f"→ {len(fused)} fused result(s) via '{plan.join_strategy}'."
            ),
        }

    async def _schema_ops(self, state: PipelineState) -> dict:
        """
        Handle NL-driven PostgreSQL DDL:
          - table_creation    → CREATE TABLE IF NOT EXISTS
          - schema_management → ALTER / DROP / RENAME
          - database_creation → informational (fixed-DB architecture)

        Refreshes the Semantic Twin on success so subsequent queries see the new schema.
        """
        intent = state.get("intent")
        intent_type = intent.intent if intent else IntentType.table_creation
        nl_query = state["nl_query"]
        schema_context = state.get("schema_context", "")
        max_attempts = settings.MAX_REPAIR_ATTEMPTS

        if intent_type == IntentType.database_creation:
            return {
                "message": (
                    "Database creation is not supported in this deployment — "
                    "a single PostgreSQL database is shared by all operations. "
                    "You can create tables inside it instead."
                )
            }

        # Choose generator based on intent
        if intent_type == IntentType.table_creation:
            ddl, syntax_error = await self._ddl_gen.generate_create_table(
                nl_query, schema_context
            )
            repair_fn = self._ddl_gen.repair_create_table
        else:
            ddl, syntax_error = await self._ddl_gen.generate_alter(
                nl_query, schema_context
            )
            repair_fn = self._ddl_gen.repair_alter

        # Syntax repair loop
        repair_attempts = 0
        repair_history: list[dict] = []
        while syntax_error and repair_attempts < max_attempts:
            repair_history.append({
                "attempt": repair_attempts + 1,
                "ddl": ddl,
                "error": syntax_error,
                "stage": "syntax",
            })
            repair_attempts += 1
            ddl, syntax_error = await repair_fn(ddl, syntax_error, schema_context, nl_query)

        if syntax_error:
            return {
                "error": f"DDL syntax repair failed after {repair_attempts} attempt(s): {syntax_error}",
                "message": "Could not produce valid DDL syntax.",
                "repair_attempts": repair_attempts,
                "repair_history": repair_history,
            }

        # Execute DDL
        exec_attempts = 0
        while True:
            try:
                self._db.execute_ddl(ddl)
                break
            except Exception as exc:
                db_error = str(exc)
                if exec_attempts >= max_attempts:
                    return {
                        "ddl": ddl,
                        "error": db_error,
                        "message": f"DDL execution failed after {exec_attempts} attempt(s).",
                        "repair_attempts": repair_attempts + exec_attempts,
                        "repair_history": repair_history,
                    }
                repair_history.append({
                    "attempt": repair_attempts + exec_attempts + 1,
                    "ddl": ddl,
                    "error": db_error,
                    "stage": "execution",
                })
                exec_attempts += 1
                ddl, _ = await repair_fn(ddl, db_error, schema_context, nl_query)

        # Refresh Semantic Twin so the new table is indexed
        try:
            from ..semantic_twin.twin_service import get_twin_service
            await get_twin_service().refresh()
        except Exception:
            pass  # twin refresh failure must not break the DDL response

        action = "Table created" if intent_type == IntentType.table_creation else "Schema updated"
        return {
            "ddl": ddl,
            "message": f"{action} successfully.",
            "repair_attempts": repair_attempts + exec_attempts,
            "repair_history": repair_history,
        }

    async def _mongo_ops(self, state: PipelineState) -> dict:
        """
        Handle NL-driven MongoDB collection creation.
        Refreshes the Semantic Twin on success.
        """
        nl_query = state["nl_query"]

        # Extract collection name from the NL query
        try:
            spec: _CollectionSpec = await self._llm.generate_structured(
                prompt=(
                    f"Request: {nl_query}\n\n"
                    "Extract the MongoDB collection name the user wants to create. "
                    "Return ONLY valid JSON."
                ),
                response_schema=_CollectionSpec,
                system_instruction=(
                    "You extract collection names from natural-language database requests. "
                    "Use snake_case. Return only valid JSON."
                ),
            )
            collection_name = spec.collection_name.strip()
        except Exception as exc:
            return {
                "error": f"Could not parse collection name: {exc}",
                "message": "Failed to extract collection name from the request.",
            }

        if not collection_name:
            return {
                "error": "Empty collection name.",
                "message": "Please specify a collection name.",
            }

        try:
            already_existed = self._mongo.collection_exists(collection_name)
            self._mongo.create_collection(collection_name)
        except Exception as exc:
            return {
                "error": str(exc),
                "message": f"Failed to create collection '{collection_name}'.",
            }

        # Refresh Semantic Twin
        try:
            from ..semantic_twin.twin_service import get_twin_service
            await get_twin_service().refresh()
        except Exception:
            pass

        if already_existed:
            msg = f"Collection '{collection_name}' already exists."
        else:
            msg = f"MongoDB collection '{collection_name}' created successfully."

        return {"message": msg}

    async def _explain_schema(self, state: PipelineState) -> dict:
        from ..semantic_twin.twin_service import get_twin_service
        twin = get_twin_service()
        summary = twin.twin.summary()
        pg = summary.get("postgresql_tables", [])
        mg = summary.get("mongodb_collections", [])
        parts: list[str] = []
        if pg:
            parts.append(f"PostgreSQL tables: {', '.join(pg)}")
        if mg:
            parts.append(f"MongoDB collections: {', '.join(mg)}")
        if not parts:
            msg = "The database is empty — no tables or collections found."
        else:
            total = summary.get("total_objects", 0)
            msg = "; ".join(parts) + f". Total: {total} object(s)."
        return {"message": msg}

    # ── Routing ───────────────────────────────────────────────────────────

    def _route(self, state: PipelineState) -> str:
        intent = state.get("intent")
        if intent is None:
            return "explain_schema"

        match intent.intent:
            case IntentType.query | IntentType.crud | IntentType.visualization:
                if intent.target_db == TargetDB.mongodb:
                    return "mongo_query"
                if intent.target_db == TargetDB.both:
                    return "hybrid_query"
                return "generate_sql"
            case IntentType.hybrid_query:
                return "hybrid_query"
            case IntentType.explanation:
                return "explain_schema"
            case (
                IntentType.table_creation
                | IntentType.schema_management
                | IntentType.database_creation
            ):
                return "schema_ops"
            case _:  # collection_creation
                return "mongo_ops"

    # ── Graph assembly ────────────────────────────────────────────────────

    def _build_graph(self):
        builder = StateGraph(PipelineState)

        builder.add_node("classify_intent", self._classify_intent)
        builder.add_node("retrieve_schema", self._retrieve_schema)
        builder.add_node("generate_sql", self._generate_sql)
        builder.add_node("execute_sql", self._execute_sql)
        builder.add_node("mongo_query", self._mongo_query)
        builder.add_node("hybrid_query", self._hybrid_query)
        builder.add_node("explain_schema", self._explain_schema)
        builder.add_node("schema_ops", self._schema_ops)
        builder.add_node("mongo_ops", self._mongo_ops)

        builder.add_edge(START, "classify_intent")
        builder.add_edge("classify_intent", "retrieve_schema")
        builder.add_conditional_edges(
            "retrieve_schema",
            self._route,
            {
                "generate_sql": "generate_sql",
                "mongo_query": "mongo_query",
                "hybrid_query": "hybrid_query",
                "explain_schema": "explain_schema",
                "schema_ops": "schema_ops",
                "mongo_ops": "mongo_ops",
            },
        )
        builder.add_edge("generate_sql", "execute_sql")
        builder.add_edge("execute_sql", END)
        builder.add_edge("mongo_query", END)
        builder.add_edge("hybrid_query", END)
        builder.add_edge("explain_schema", END)
        builder.add_edge("schema_ops", END)
        builder.add_edge("mongo_ops", END)

        return builder.compile()

    # ── Public entry point ────────────────────────────────────────────────

    async def run(self, nl_query: str) -> PipelineState:
        initial: PipelineState = {
            "nl_query": nl_query,
            "intent": None,
            "schema_context": "",
            "context_objects": [],
            "sql": None,
            "ddl": None,
            "mongo_query_spec": None,
            "hybrid_plan": None,
            "viz_spec": None,
            "result_rows": [],
            "result_columns": [],
            "error": None,
            "message": "",
            "repair_attempts": 0,
            "repair_history": [],
        }
        return await self._graph.ainvoke(initial)


# ── Module-level singleton ────────────────────────────────────────────────

_planner: PlannerService | None = None


def get_planner(
    llm: LLMProvider,
    db: PostgresService,
    mongo: MongoService,
) -> PlannerService:
    global _planner
    if _planner is None:
        _planner = PlannerService(llm, db, mongo)
    return _planner
