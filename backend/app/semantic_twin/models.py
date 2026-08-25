from typing import Literal
from pydantic import BaseModel, Field


class ColumnMeta(BaseModel):
    name: str
    sql_type: str
    nullable: bool = True
    is_pk: bool = False
    fk_to: str | None = None  # "referenced_table.column"
    description: str | None = None


class ObjectMeta(BaseModel):
    """Unified representation of a PostgreSQL table or MongoDB collection."""
    name: str
    source: Literal["postgresql", "mongodb"]
    columns: list[ColumnMeta] = Field(default_factory=list)
    description: str | None = None
    embedding_text: str = ""  # compact text fed to the embedding model

    def to_context_string(self) -> str:
        """Return a compact schema string for LLM prompt injection."""
        kind = "table" if self.source == "postgresql" else "collection"
        col_parts: list[str] = []
        for c in self.columns:
            part = f"{c.name} {c.sql_type}"
            if c.is_pk:
                part += " PK"
            if c.fk_to:
                part += f" FK->{c.fk_to}"
            if not c.nullable:
                part += " NOT NULL"
            col_parts.append(part)
        cols = ", ".join(col_parts)
        return f"{self.source} {kind} {self.name}: ({cols})"


class DatabaseTwin(BaseModel):
    objects: list[ObjectMeta] = Field(default_factory=list)
    last_refreshed: str = ""

    def get_context_for_objects(self, names: list[str]) -> str:
        """Return formatted schema context for the given object names."""
        selected = [o for o in self.objects if o.name in set(names)]
        if not selected:
            selected = self.objects  # fallback: use all
        return "\n".join(o.to_context_string() for o in selected)

    def summary(self) -> dict:
        pg = [o.name for o in self.objects if o.source == "postgresql"]
        mg = [o.name for o in self.objects if o.source == "mongodb"]
        return {
            "last_refreshed": self.last_refreshed,
            "postgresql_tables": pg,
            "mongodb_collections": mg,
            "total_objects": len(self.objects),
        }
