import sqlglot
import sqlglot.errors

from ..llm.base import LLMProvider

_CREATE_SYSTEM = (
    "You are a PostgreSQL DBA. You write syntactically correct PostgreSQL CREATE TABLE statements. "
    "Return only the raw DDL SQL — no explanation, no markdown, no code fences."
)

_ALTER_SYSTEM = (
    "You are a PostgreSQL DBA specialising in schema changes. "
    "Write a precise ALTER TABLE, DROP TABLE, or RENAME statement. "
    "Return only the raw DDL SQL — no explanation, no markdown, no code fences."
)


class DDLGenerator:
    """
    Generates and validates PostgreSQL DDL (CREATE TABLE, ALTER, DROP, RENAME).

    Validation uses the same SQLGlot approach as SQLGenerator so syntax errors
    are caught before touching the database.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    # ── Validation ────────────────────────────────────────────────────────

    @staticmethod
    def validate(sql: str) -> str | None:
        """Returns a human-readable error string or None when syntax is valid."""
        if not sql.strip():
            return "Empty DDL statement."
        try:
            sqlglot.transpile(sql, read="postgres", write="postgres")
            return None
        except sqlglot.errors.ParseError as exc:
            return str(exc).split("\n")[0]
        except Exception as exc:
            return str(exc)

    # ── CREATE TABLE ──────────────────────────────────────────────────────

    async def generate_create_table(
        self,
        nl_query: str,
        schema_context: str,
    ) -> tuple[str, "str | None"]:
        """
        Generate a CREATE TABLE IF NOT EXISTS statement.
        Returns (ddl, error). error is None when SQLGlot passes.
        """
        prompt = (
            f"Existing schema:\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            "Rules:\n"
            "- Use CREATE TABLE IF NOT EXISTS.\n"
            "- Pick appropriate PostgreSQL types: SERIAL for auto-increment PK, "
            "TEXT, INTEGER, NUMERIC(p,s), BOOLEAN, TIMESTAMP WITH TIME ZONE, etc.\n"
            "- Add a SERIAL PRIMARY KEY column when no natural key is specified.\n"
            "- Do NOT recreate any table already listed in the schema above.\n"
            "- Return only the raw DDL SQL."
        )
        raw = await self._llm.generate(prompt, system_instruction=_CREATE_SYSTEM)
        ddl = LLMProvider.strip_code_fences(raw)
        return ddl, self.validate(ddl)

    async def repair_create_table(
        self,
        ddl: str,
        error: str,
        schema_context: str,
        nl_query: str,
    ) -> tuple[str, "str | None"]:
        prompt = (
            f"Failing DDL:\n{ddl}\n\n"
            f"Error: {error}\n\n"
            f"Schema:\n{schema_context}\n\n"
            f"Original request: {nl_query}\n\n"
            "Return only the corrected CREATE TABLE SQL."
        )
        raw = await self._llm.generate(prompt, system_instruction=_CREATE_SYSTEM)
        repaired = LLMProvider.strip_code_fences(raw)
        return repaired, self.validate(repaired)

    # ── ALTER / DROP / RENAME ─────────────────────────────────────────────

    async def generate_alter(
        self,
        nl_query: str,
        schema_context: str,
    ) -> tuple[str, "str | None"]:
        """
        Generate ALTER TABLE, DROP TABLE, or RENAME statement.
        Returns (ddl, error). error is None when SQLGlot passes.
        """
        prompt = (
            f"Existing schema:\n{schema_context}\n\n"
            f"Request: {nl_query}\n\n"
            "Rules:\n"
            "- Only reference tables listed in the schema above.\n"
            "- Generate a single DDL statement (ALTER TABLE … or DROP TABLE … or "
            "ALTER TABLE … RENAME TO …).\n"
            "- Return only the raw DDL SQL."
        )
        raw = await self._llm.generate(prompt, system_instruction=_ALTER_SYSTEM)
        ddl = LLMProvider.strip_code_fences(raw)
        return ddl, self.validate(ddl)

    async def repair_alter(
        self,
        ddl: str,
        error: str,
        schema_context: str,
        nl_query: str,
    ) -> tuple[str, "str | None"]:
        prompt = (
            f"Failing DDL:\n{ddl}\n\n"
            f"Error: {error}\n\n"
            f"Schema:\n{schema_context}\n\n"
            f"Original request: {nl_query}\n\n"
            "Return only the corrected DDL SQL."
        )
        raw = await self._llm.generate(prompt, system_instruction=_ALTER_SYSTEM)
        repaired = LLMProvider.strip_code_fences(raw)
        return repaired, self.validate(repaired)
