from ..llm.base import LLMProvider
from ..database.postgres_service import PostgresService
from ..database.mongo_service import MongoService
from .models import HybridQueryPlan

_SYSTEM = (
    "You are a database expert skilled in both PostgreSQL and MongoDB. "
    "You plan hybrid queries that retrieve data from both databases and specify how to fuse the results. "
    "Use only tables/collections and fields present in the provided schema. "
    "Return only valid JSON — no explanation, no markdown."
)


class HybridExecutor:
    """
    Plans and executes queries that span PostgreSQL and MongoDB.

    plan()  — asks the LLM to produce a HybridQueryPlan (SQL + MongoQuerySpec + join strategy)
    fuse()  — merges two result lists in Python using the join strategy from the plan
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

    async def plan(
        self,
        nl_query: str,
        schema_context: str,
    ) -> tuple["HybridQueryPlan | None", "str | None"]:
        """
        Ask the LLM to produce a HybridQueryPlan.
        Returns (plan, error). error is None on success.
        """
        prompt = (
            f"Database schema (PostgreSQL + MongoDB combined):\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            "Rules:\n"
            "- Write valid PostgreSQL SQL for the relational portion.\n"
            "- Write a MongoDB query spec for the document portion.\n"
            "- If both results share a common field (e.g. user_id, order_id), set join_key "
            "and choose left_join or inner_join as appropriate.\n"
            "- If there is no natural join field, set join_strategy='union' and join_key=''.\n"
            "- Only reference tables/collections and fields listed in the schema above.\n"
            "- Return ONLY valid JSON."
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

    def fuse(
        self,
        pg_rows: list[dict],
        mongo_rows: list[dict],
        plan: HybridQueryPlan,
    ) -> list[dict]:
        """
        Merge two result lists using the strategy in the plan.

        union      — concatenate (schemas may differ)
        inner_join — only rows where join_key appears in both sets
        left_join  — all PG rows; Mongo fields merged in where join_key matches
        """
        if plan.join_strategy == "union" or not plan.join_key:
            return pg_rows + mongo_rows

        join_key = plan.join_key
        mongo_index: dict[str, dict] = {
            str(doc[join_key]): doc
            for doc in mongo_rows
            if join_key in doc
        }

        if plan.join_strategy == "inner_join":
            result = []
            for row in pg_rows:
                key_val = str(row.get(join_key, ""))
                if key_val in mongo_index:
                    result.append({**row, **mongo_index[key_val]})
            return result

        # left_join (default)
        result = []
        for row in pg_rows:
            key_val = str(row.get(join_key, ""))
            mongo_data = mongo_index.get(key_val, {})
            result.append({**row, **mongo_data})
        return result
