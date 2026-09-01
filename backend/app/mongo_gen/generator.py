from ..llm.base import LLMProvider
from .models import MongoQuerySpec

_SYSTEM = (
    "You are a MongoDB expert. You generate correct MongoDB query specifications "
    "using only the collections and fields present in the provided schema. "
    "Never invent collection or field names. "
    "Use dot notation for nested fields (e.g. 'address.city'). "
    "Return only valid JSON — no explanation, no markdown."
)

_REPAIR_SYSTEM = (
    "You are a MongoDB expert specialising in fixing broken queries. "
    "You will be given a failing MongoDB query spec and its error message. "
    "Return only the corrected JSON — no explanation, no markdown."
)


class MongoGenerator:
    """
    Generates and repairs MongoDB query specifications from natural language.

    Produces a MongoQuerySpec that is either:
    - query_type='find'      — filter / projection / sort / limit
    - query_type='aggregate' — aggregation pipeline
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def _build_prompt(self, nl_query: str, schema_context: str) -> str:
        return (
            f"MongoDB schema context:\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            "Rules:\n"
            "- Use only collections and fields listed in the schema above.\n"
            "- For simple lookups/filters, use query_type='find'.\n"
            "- For grouping, counting, computed fields, or multi-stage transformations, "
            "use query_type='aggregate'.\n"
            "- Use dot notation for nested document fields (e.g. 'address.city').\n"
            "- Set limit to 100 unless the user specifies otherwise.\n"
            "- Return ONLY valid JSON matching the required schema."
        )

    async def generate(
        self,
        nl_query: str,
        schema_context: str,
    ) -> tuple["MongoQuerySpec | None", "str | None"]:
        """
        Returns (spec, error). error is None on success.
        """
        prompt = self._build_prompt(nl_query, schema_context)
        try:
            spec: MongoQuerySpec = await self._llm.generate_structured(
                prompt=prompt,
                response_schema=MongoQuerySpec,
                system_instruction=_SYSTEM,
            )
            return spec, None
        except Exception as exc:
            return None, str(exc)

    async def repair(
        self,
        spec_json: str,
        error: str,
        schema_context: str,
        nl_query: str,
    ) -> tuple["MongoQuerySpec | None", "str | None"]:
        """
        Ask the LLM to fix a query spec given an execution error.
        Returns (repaired_spec, error).
        """
        prompt = (
            f"Failing MongoDB query:\n{spec_json}\n\n"
            f"Error: {error}\n\n"
            f"Schema:\n{schema_context}\n\n"
            f"Original request: {nl_query}\n\n"
            "Return only the corrected MongoDB query JSON."
        )
        try:
            spec: MongoQuerySpec = await self._llm.generate_structured(
                prompt=prompt,
                response_schema=MongoQuerySpec,
                system_instruction=_REPAIR_SYSTEM,
            )
            return spec, None
        except Exception as exc:
            return None, str(exc)
