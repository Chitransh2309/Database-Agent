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
            if c.description:
                part += f" [{c.description}]"
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

    def cross_db_links(self) -> list[str]:
        """
        Detect MongoDB fields that share a name with PostgreSQL columns and look like
        join keys (field is 'id' itself, or ends with '_id', or matches a PG table name).
        Returns human-readable strings for LLM context.
        """
        # Build a map: column_name -> list of PG table names that contain it
        pg_col_map: dict[str, list[str]] = {}
        pg_table_names: set[str] = set()
        for o in self.objects:
            if o.source == "postgresql":
                pg_table_names.add(o.name)
                for c in o.columns:
                    pg_col_map.setdefault(c.name, []).append(o.name)

        links: list[str] = []
        seen: set[str] = set()
        for o in self.objects:
            if o.source != "mongodb":
                continue
            for c in o.columns:
                field = c.name
                # Only surface fields that plausibly serve as join keys
                is_id_field = (
                    field == "id"
                    or field.endswith("_id")
                    or field in pg_table_names
                    or f"{field}_id" in pg_col_map
                )
                if not is_id_field:
                    continue
                # Check if this field (or the stripped base) matches a PG column
                pg_owners = pg_col_map.get(field, [])
                if not pg_owners:
                    # Try base: "product" from "product_id" -> look for "id" in table "products"
                    base = field[:-3] if field.endswith("_id") else field
                    candidates = [
                        t for t in pg_table_names
                        if t == base or t == base + "s" or t.startswith(base)
                    ]
                    pg_owners = candidates

                if pg_owners:
                    key = f"{o.name}.{field}"
                    if key not in seen:
                        seen.add(key)
                        links.append(
                            f"  '{field}' links MongoDB '{o.name}' ↔ PostgreSQL '{', '.join(pg_owners)}'"
                        )
        return links
