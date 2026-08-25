from .models import ColumnMeta, ObjectMeta


def introspect_mongo(mongo_db) -> list[ObjectMeta]:
    """
    Sample documents from each MongoDB collection to infer field names/types.
    Returns ObjectMeta list ready for embedding.
    """
    collections = mongo_db.list_collection_names()
    objects: list[ObjectMeta] = []

    for col_name in collections:
        sample_docs = list(mongo_db[col_name].find({}, {"_id": 0}).limit(10))
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
    """Infer field names and types from a list of sample documents."""
    if not docs:
        return []

    # Collect all field names across all sample docs
    field_types: dict[str, str] = {}
    for doc in docs:
        for key, value in doc.items():
            if key not in field_types:
                field_types[key] = _python_to_type(value)

    return [
        ColumnMeta(name=field, sql_type=ftype)
        for field, ftype in field_types.items()
    ]


def _python_to_type(value) -> str:
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
    field_names = " ".join(c.name for c in columns)
    return f"mongodb collection {name}: {field_names}"
