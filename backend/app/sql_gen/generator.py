import sqlglot
import sqlglot.errors

from ..llm.base import LLMProvider

_SYSTEM = (
    "You are a PostgreSQL expert. You generate syntactically correct PostgreSQL SQL "
    "using only the tables and columns present in the provided schema. "
    "Never invent table or column names. Return only raw SQL with no explanation."
)

_REPAIR_SYSTEM = (
    "You are a PostgreSQL expert specialising in fixing broken queries. "
    "You will be given a failing SQL statement and its error message. "
    "Return only the corrected SQL — no explanation, no markdown, no code fences."
)


class SQLGenerator:
    """
    Generates and validates PostgreSQL SQL.

    Responsibilities:
    - Build the generation prompt from schema context + NL query
    - Validate syntax with SQLGlot before hitting the database
    - Repair: ask the LLM to fix a failing query given the error message
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    # ── Validation ────────────────────────────────────────────────────────

    @staticmethod
    def validate(sql: str) -> str | None:
        """
        Returns a human-readable error string if the SQL has a syntax problem,
        or None when the statement is syntactically valid PostgreSQL.
        SQLGlot catches syntax issues; semantic issues (bad table/column names)
        are only caught at execution time.
        """
        if not sql.strip():
            return "Empty SQL statement."
        try:
            sqlglot.transpile(sql, read="postgres", write="postgres")
            return None
        except sqlglot.errors.ParseError as exc:
            return str(exc).split("\n")[0]  # first line is the most useful
        except Exception as exc:
            return str(exc)

    # ── Generation ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        nl_query: str,
        schema_context: str,
        repair_history: list[dict] | None,
    ) -> str:
        repair_ctx = ""
        if repair_history:
            repair_ctx = "\n\nPrevious failed attempts — fix all of the listed errors:\n"
            for entry in repair_history:
                repair_ctx += (
                    f"  Attempt {entry['attempt']}:\n"
                    f"    SQL:   {entry['sql']}\n"
                    f"    Error: {entry['error']}\n"
                )

        return (
            f"Database schema:\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            "Rules:\n"
            "- Return ONLY the raw SQL, no explanation, no markdown, no code fences.\n"
            "- Use standard PostgreSQL syntax.\n"
            "- Only reference tables and columns in the schema above.\n"
            "- Add LIMIT 500 to SELECT queries unless the user specifies otherwise."
            f"{repair_ctx}"
        )

    async def generate(
        self,
        nl_query: str,
        schema_context: str,
        repair_history: list[dict] | None = None,
    ) -> tuple[str, str | None]:
        """
        Generate SQL for *nl_query* given *schema_context*.
        Returns (sql, error) where error is None when SQLGlot passes.
        Pass previous *repair_history* to guide the model away from known failures.
        """
        prompt = self._build_prompt(nl_query, schema_context, repair_history)
        raw = await self._llm.generate(prompt, system_instruction=_SYSTEM)
        sql = LLMProvider.strip_code_fences(raw)
        return sql, self.validate(sql)

    # ── Repair ────────────────────────────────────────────────────────────

    async def repair(
        self,
        sql: str,
        error: str,
        schema_context: str,
        nl_query: str,
    ) -> tuple[str, str | None]:
        """
        Ask the LLM to fix *sql* given *error*.
        Returns (repaired_sql, validation_error).
        """
        prompt = (
            f"Failing query:\n{sql}\n\n"
            f"Error: {error}\n\n"
            f"Schema:\n{schema_context}\n\n"
            f"Original request: {nl_query}\n\n"
            "Return only the corrected PostgreSQL SQL."
        )
        raw = await self._llm.generate(prompt, system_instruction=_REPAIR_SYSTEM)
        repaired = LLMProvider.strip_code_fences(raw)
        return repaired, self.validate(repaired)
