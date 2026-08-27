from ..llm.base import LLMProvider
from .models import IntentResult, IntentType, TargetDB

_SYSTEM = (
    "You are an intent classifier for a unified AI database copilot that manages "
    "both PostgreSQL (relational) and MongoDB (document) databases. "
    "Classify the user's natural-language request accurately and return ONLY the JSON."
)

_INTENT_GUIDE = """
Intent selection rules:
  query             — SELECT / read / fetch / show / list / find / count / aggregate data
  crud              — insert / add / update / edit / delete / remove rows or documents
  table_creation    — create / add a new SQL table
  collection_creation — create / add a new MongoDB collection
  database_creation — create a new database
  schema_management — alter / drop / rename / modify existing tables or collections
  visualization     — chart / graph / plot / visualize / dashboard
  explanation       — "what tables exist", "describe X", "explain the schema"
  hybrid_query      — ONLY when the query explicitly requires combining results from BOTH
                      PostgreSQL AND MongoDB in a single response (e.g. "join orders from
                      SQL with reviews from MongoDB")

target_db selection rules:
  postgresql  — ALL referenced entities live in PostgreSQL; use this by default for relational data
  mongodb     — ALL referenced entities live in MongoDB; use this for collections/documents
  both        — ONLY when the response MUST contain joined/correlated data from BOTH sources
  none        — schema-agnostic (e.g. database_creation, pure explanation)

ROUTING PRIORITY (apply in order — stop at the first rule that matches):
  1. Identify every table/collection the query references from the schema hint below.
  2. If all referenced entities are PostgreSQL tables → target_db=postgresql, intent=query/crud/etc.
  3. If all referenced entities are MongoDB collections → target_db=mongodb, intent=query/crud/etc.
  4. If entities from BOTH sources are needed AND the user explicitly asks to JOIN or COMBINE them
     → target_db=both, intent=hybrid_query.
  5. If unsure which DB an entity belongs to, prefer the DB where the primary entity lives.

NEVER use target_db=both or intent=hybrid_query just because both databases exist in the system.
A query about reviews, ratings, logs, or events typically targets MongoDB only.
A query about users, products, orders, employees, or transactions typically targets PostgreSQL only.

requires_schema:
  true  — needs column names / types / relationships to execute
  false — does not need schema detail (e.g. "list all tables", "create a database")
""".strip()


class IntentClassifier:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def classify(
        self,
        nl_query: str,
        available_objects: list[str] | None = None,
        schema_hint: str | None = None,
    ) -> IntentResult:
        """
        Classify *nl_query* into a structured IntentResult.

        schema_hint — pre-formatted multi-line schema context (preferred when available).
        available_objects — fallback flat list of object names when schema_hint is absent.
        """
        if schema_hint:
            hint_text = f"\n\nDatabase schema (use this to identify which DB each entity belongs to):\n{schema_hint}"
        elif available_objects:
            hint_text = (
                f"\n\nKnown tables/collections in the system: "
                f"{', '.join(available_objects)}"
            )
        else:
            hint_text = ""

        prompt = (
            f'User request: "{nl_query}"{hint_text}\n\n'
            f"{_INTENT_GUIDE}\n\n"
            "Return a JSON object with these fields:\n"
            "  intent        — one of the intent values above\n"
            "  target_db     — one of: postgresql, mongodb, both, none\n"
            "  entities      — list of table/collection names referenced (empty list if none)\n"
            "  confidence    — float 0.0–1.0 indicating certainty\n"
            "  requires_schema — boolean\n"
            "  explanation   — one sentence explaining the classification\n"
            "  nl_query      — leave as empty string (will be set by the system)"
        )

        result: IntentResult = await self._llm.generate_structured(
            prompt=prompt,
            response_schema=IntentResult,
            system_instruction=_SYSTEM,
        )
        result.nl_query = nl_query
        return result


# ── Module-level singleton ────────────────────────────────────────────────

_classifier: IntentClassifier | None = None


def get_classifier(llm: LLMProvider) -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier(llm)
    return _classifier
