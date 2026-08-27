from .models import ColumnMeta, ObjectMeta


def introspect_mongo(mongo_db) -> list[ObjectMeta]:
    """
    Sample documents from each MongoDB collection to infer field names/types.
    Returns ObjectMeta list ready for embedding.
    """
    collections = mongo_db.list_collection_names()
    objects: list[ObjectMeta] = []

    for col_name in collections:
        sample_docs = list(mongo_db[col_name].find({}, {"_id": 0}).limit(20))
        columns = _infer_fields(sample_docs)
        emb_text = _build_embedding_text(col_name, columns)
        objects.append(
            ObjectMeta(
                name=col_name,
                source="mongodb",
                columns=columns,
                embedding_text=emb_text,
            )
        )

    return objects


def _infer_fields(docs: list[dict]) -> list[ColumnMeta]:
    """
    Infer field names and types from sample documents.
    For low-cardinality string fields, collect sample values to help the LLM
    use correct casing (e.g. 'Open' not 'open').
    """
    if not docs:
        return []

    field_types: dict[str, str] = {}
    field_values: dict[str, set] = {}

    for doc in docs:
        for key, value in doc.items():
            if key not in field_types:
                field_types[key] = _describe_value(value)
            if isinstance(value, str):
                field_values.setdefault(key, set()).add(value)

    columns = []
    for field, ftype in field_types.items():
        description: str | None = None
        sample_vals = field_values.get(field, set())
        # Show sample values for low-cardinality string fields (≤8 distinct values)
        if ftype == "STRING" and 1 < len(sample_vals) <= 8:
            description = "values: " + ", ".join(sorted(sample_vals))
        columns.append(ColumnMeta(name=field, sql_type=ftype, description=description))

    return columns


def _describe_value(value) -> str:
    """
    Return a rich type description for a value, including nested structure for
    arrays-of-objects and plain objects. This lets the LLM understand nested
    fields like devices[{type, sessions}] and generate correct aggregation pipelines.
    """
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "FLOAT"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            # Array of objects — show sub-field names and types from the first element
            sub_parts = ", ".join(
                f"{k}: {_describe_value_simple(v)}"
                for k, v in value[0].items()
            )
            return f"ARRAY[{{{sub_parts}}}]"
        elif value:
            return f"ARRAY[{_describe_value_simple(value[0])}]"
        return "ARRAY"
    if isinstance(value, dict):
        sub_parts = ", ".join(
            f"{k}: {_describe_value_simple(v)}"
            for k, v in value.items()
        )
        return f"OBJECT{{{sub_parts}}}"
    return "UNKNOWN"


def _describe_value_simple(value) -> str:
    """Flat type name only (no recursion). Used for nested-field descriptions."""
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "FLOAT"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, list):
        return "ARRAY"
    if isinstance(value, dict):
        return "OBJECT"
    return "UNKNOWN"


def _build_embedding_text(name: str, columns: list[ColumnMeta]) -> str:
    col_parts = [f"{c.name} {c.sql_type.lower()}" for c in columns]
    cols = " | ".join(col_parts)
    return f"mongodb collection {name} fields: {cols}"
