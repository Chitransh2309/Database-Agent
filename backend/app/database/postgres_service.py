from typing import Any
from sqlalchemy import create_engine, text, inspect as sa_inspect
from ..config import settings


class PostgresService:
    """
    Thin wrapper around SQLAlchemy for PostgreSQL.
    LLM code must never call this directly — go through the API routes.
    """

    def __init__(self) -> None:
        self.engine = create_engine(settings.POSTGRES_URL, pool_pre_ping=True)

    # ── Schema introspection ──────────────────────────────────────────────

    def get_table_names(self) -> list[str]:
        inspector = sa_inspect(self.engine)
        return inspector.get_table_names()

    def get_schema_context(self) -> str:
        """
        Return a compact schema description for all tables.
        Used to build LLM context for NL→SQL generation.
        """
        inspector = sa_inspect(self.engine)
        tables = inspector.get_table_names()
        if not tables:
            return "No tables found in the database."

        lines: list[str] = []
        for table in tables:
            columns = inspector.get_columns(table)
            pk_cols = {c["name"] for c in inspector.get_pk_constraint(table).get("constrained_columns", [])}
            fk_map = {
                fk["constrained_columns"][0]: fk["referred_table"]
                for fk in inspector.get_foreign_keys(table)
                if fk["constrained_columns"]
            }
            col_parts: list[str] = []
            for col in columns:
                note = ""
                if col["name"] in pk_cols:
                    note = " PK"
                elif col["name"] in fk_map:
                    note = f" FK->{fk_map[col['name']]}"
                nullable = "" if col.get("nullable", True) else " NOT NULL"
                col_parts.append(f"{col['name']} {col['type']}{nullable}{note}")
            lines.append(f"Table {table}: ({', '.join(col_parts)})")
        return "\n".join(lines)

    def get_columns(self, table_name: str) -> list[dict]:
        inspector = sa_inspect(self.engine)
        return inspector.get_columns(table_name)

    def table_exists(self, table_name: str) -> bool:
        inspector = sa_inspect(self.engine)
        return table_name in inspector.get_table_names()

    # ── Query execution ───────────────────────────────────────────────────

    def execute_query(self, sql: str) -> dict[str, Any]:
        """Execute a read-only SELECT and return columns + rows."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchmany(500)]
        return {"columns": columns, "rows": rows}

    def execute_ddl(self, sql: str) -> None:
        """Execute a DDL statement inside a transaction."""
        with self.engine.begin() as conn:
            conn.execute(text(sql))

    def insert_row(self, table_name: str, data: dict[str, Any]) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        with self.engine.begin() as conn:
            conn.execute(text(sql), data)
