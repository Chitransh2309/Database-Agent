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
  hybrid_query      — request that explicitly spans both PostgreSQL and MongoDB data

target_db selection rules:
  postgresql  — SQL tables, relational/structured data
  mongodb     — collections, documents, JSON / NoSQL
  both        — hybrid request spanning both systems
  none        — schema-agnostic (e.g. database_creation, pure explanation)

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
    ) -> IntentResult:
        """
        Classify *nl_query* into a structured IntentResult.

        available_objects — names of all known tables/collections from the Semantic Twin.
        They are passed as a hint so the LLM can identify referenced entities accurately.
        """
        schema_hint = ""
        if available_objects:
            schema_hint = (
                f"\n\nKnown tables/collections in the system: "
                f"{', '.join(available_objects)}"
            )

        prompt = (
            f'User request: "{nl_query}"{schema_hint}\n\n'
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
