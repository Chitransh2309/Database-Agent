from sqlalchemy import inspect as sa_inspect
from .models import ColumnMeta, ObjectMeta


def introspect_postgres(engine) -> list[ObjectMeta]:
    """
    Reflect all tables in the connected PostgreSQL database.
    Returns ObjectMeta list ready for embedding.
    """
    inspector = sa_inspect(engine)
    tables = inspector.get_table_names()
    objects: list[ObjectMeta] = []

    for table_name in tables:
        columns_info = inspector.get_columns(table_name)
        pk_cols: set[str] = set(
            inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        )
        fk_map: dict[str, str] = {}
        for fk in inspector.get_foreign_keys(table_name):
            if fk["constrained_columns"] and fk["referred_columns"]:
                local_col = fk["constrained_columns"][0]
                ref = f"{fk['referred_table']}.{fk['referred_columns'][0]}"
                fk_map[local_col] = ref

        columns: list[ColumnMeta] = []
        for col in columns_info:
            columns.append(
                ColumnMeta(
                    name=col["name"],
                    sql_type=str(col["type"]),
                    nullable=col.get("nullable", True),
                    is_pk=col["name"] in pk_cols,
                    fk_to=fk_map.get(col["name"]),
                )
            )

        emb_text = _build_embedding_text("postgresql", table_name, columns)
        objects.append(
            ObjectMeta(
                name=table_name,
                source="postgresql",
                columns=columns,
                embedding_text=emb_text,
            )
        )

    return objects


def _build_embedding_text(source: str, name: str, columns: list[ColumnMeta]) -> str:
    # Include column names AND types so semantic search matches on both field semantics
    # and data-type keywords (e.g. "rating INTEGER" scores higher for "highest rated" queries).
    col_parts = []
    for c in columns:
        part = c.name
        if c.sql_type:
            part += f" {c.sql_type.lower()}"
        if c.is_pk:
            part += " primary_key"
        if c.fk_to:
            ref_table = c.fk_to.split(".")[0]
            part += f" references_{ref_table}"
        if not c.nullable:
            part += " required"
        col_parts.append(part)
    cols = " | ".join(col_parts)
    return f"{source} table {name} columns: {cols}"
