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
  hybrid_query      — when answering the query requires data from BOTH PostgreSQL AND MongoDB
                      to produce a single coherent answer, even without the words "join",
                      "combine", or "merge"

target_db selection rules:
  postgresql  — ALL referenced entities live in PostgreSQL
  mongodb     — ALL referenced entities live in MongoDB
  both        — answering the query requires data from BOTH sources
  none        — schema-agnostic (e.g. database_creation, pure explanation)

ROUTING PRIORITY (apply in order — stop at the first rule that matches):
  1. Identify every table/collection the query references or implies from the schema hint below.
  2. Determine which database(s) contain those entities.
  3. If all entities are in PostgreSQL → target_db=postgresql, intent=query/crud/etc.
  4. If all entities are in MongoDB → target_db=mongodb, intent=query/crud/etc.
  5. If producing the answer REQUIRES data from BOTH databases — even without explicit "join" or
     "combine" words — then target_db=both, intent=hybrid_query.

     Hybrid is required when ANY of these are true:
     - The filtering condition references one DB and the desired output columns come from the other
     - The question asks about entities AND their associated records / events / documents
       where entity data is in one DB and the associated records are in the other
     - The answer needs aggregation from one DB (e.g. event counts, metrics) combined with records from the other
     - Answering accurately is impossible from a single database alone

     Hybrid is NOT required when:
     - The query can be fully answered from one DB (even if the other DB exists)
     - The query mentions a concept loosely linked to both, but one DB alone suffices

  6. If unsure which DB an entity belongs to, prefer the DB where the primary entity lives.

EXAMPLES — always consult the schema hint to determine which DB each entity belongs to:
  Cross-DB (relational entity in PG, activity/events/documents in Mongo):
    "Which <entities> have more <event_type_A> than <event_type_B>?"
    → if event data is in MongoDB and the entity table is in PostgreSQL → hybrid_query, both
  Cross-DB (aggregate filter from PG → detail lookup in Mongo):
    "Find <entities> with high <metric> that also have <status> <documents>."
    → if the metric aggregation lives in PostgreSQL and the documents live in MongoDB → hybrid_query, both
  Cross-DB (enrichment: PG entity + Mongo attribute):
    "Show <entities> together with their <document_type>."
    → both sources needed → hybrid_query, both
  Single-DB (all required data in one source):
    "List all <entities>" where all data is in one DB → query, <that_db>
    "Show all <status> <documents>" where all data is in one DB → query, <that_db>

NEVER use target_db=both or intent=hybrid_query just because both databases exist in the system.
Do NOT require the words "join", "combine", or "merge" for hybrid classification.

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
