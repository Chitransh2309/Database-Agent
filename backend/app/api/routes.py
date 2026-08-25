from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..llm.base import LLMProvider
from ..llm.factory import get_llm_provider
from ..database.postgres_service import PostgresService
from ..database.mongo_service import MongoService
from ..intent.models import IntentResult
from ..intent.classifier import get_classifier

router = APIRouter(prefix="/api")

# ── Dependency singletons (instantiated once per process) ─────────────────

_llm: LLMProvider | None = None
_db: PostgresService | None = None
_mongo: MongoService | None = None


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = get_llm_provider()
    return _llm


def get_db() -> PostgresService:
    global _db
    if _db is None:
        _db = PostgresService()
    return _db


def get_mongo() -> MongoService:
    global _mongo
    if _mongo is None:
        _mongo = MongoService()
    return _mongo


# ── Pydantic request/response models ─────────────────────────────────────

class FieldOption(BaseModel):
    value: str
    label: str


class FieldValidation(BaseModel):
    maxLength: int | None = None
    min: float | None = None
    max: float | None = None
    pattern: str | None = None


class FormField(BaseModel):
    name: str
    label: str
    inputType: str  # text | number | email | select | checkbox | date | textarea | radio
    required: bool = False
    options: list[FieldOption] = Field(default_factory=list)
    default: Any = None
    validation: FieldValidation | None = None


class FormSchemaLLMResponse(BaseModel):
    fields: list[FormField]


class GenerateFormRequest(BaseModel):
    tableSchema: str


class GenerateFormByTableRequest(BaseModel):
    tableName: str


class IntentRequest(BaseModel):
    nlQuery: str


class NLQueryRequest(BaseModel):
    nlQuery: str


class InsertDataRequest(BaseModel):
    tableName: str
    formData: dict[str, Any]
    tableSchema: str = ""  # optional when table already exists


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/connections")
async def health_connections(
    db: PostgresService = Depends(get_db),
    mongo: MongoService = Depends(get_mongo),
):
    """Test live connectivity to PostgreSQL and MongoDB."""
    pg: dict = {}
    try:
        tables = db.get_table_names()
        pg = {"status": "ok", "table_count": len(tables), "tables": tables}
    except Exception as exc:
        pg = {"status": "error", "detail": str(exc)}

    mg: dict = {}
    try:
        collections = mongo.get_collection_names()
        mg = {"status": "ok", "collection_count": len(collections), "collections": collections}
    except Exception as exc:
        mg = {"status": "error", "detail": str(exc)}

    overall = "ok" if pg.get("status") == "ok" and mg.get("status") == "ok" else "degraded"
    return {"overall": overall, "postgresql": pg, "mongodb": mg}


@router.post("/intent", response_model=IntentResult)
async def classify_intent(
    req: IntentRequest,
    llm: LLMProvider = Depends(get_llm),
):
    """
    Classify a natural-language request into a structured IntentResult.
    Returns intent type, target database, referenced entities, and confidence.
    """
    if not req.nlQuery.strip():
        raise HTTPException(status_code=400, detail="nlQuery is required.")

    from ..semantic_twin.twin_service import get_twin_service
    twin_svc = get_twin_service()
    available = [o.name for o in twin_svc.twin.objects]

    classifier = get_classifier(llm)
    return await classifier.classify(req.nlQuery, available_objects=available or None)


@router.post("/generate-form")
async def generate_form(
    req: GenerateFormRequest,
    llm: LLMProvider = Depends(get_llm),
):
    """
    Accept a SQL CREATE TABLE statement and return a list of form field
    descriptors for the React dynamic form.
    """
    if not req.tableSchema.strip():
        raise HTTPException(status_code=400, detail="tableSchema is required.")

    prompt = (
        "Given this SQL CREATE TABLE statement:\n\n"
        f"{req.tableSchema}\n\n"
        "Generate a JSON object with a 'fields' array. Each element describes one form field.\n"
        "Rules:\n"
        "- Skip auto-increment primary key columns.\n"
        "- Map SQL types: INT/BIGINT/FLOAT/DECIMAL -> number, BOOLEAN -> checkbox, DATE/DATETIME -> date, TEXT/LONGTEXT -> textarea, VARCHAR -> text.\n"
        "- For columns named 'email' use inputType 'email'.\n"
        "- For ENUM columns use inputType 'select' and populate options as [{value, label}].\n"
        "- required=true for NOT NULL columns that have no DEFAULT.\n"
        "- Each field: name (column name), label (human-readable title-case), inputType, required, options (empty list if not select/radio), default (null if none), validation (null if none).\n"
        "Return ONLY valid JSON matching the schema."
    )

    result: FormSchemaLLMResponse = await llm.generate_structured(
        prompt=prompt,
        response_schema=FormSchemaLLMResponse,
    )
    return result.fields


def _build_ddl_from_meta(obj) -> str:
    """Reconstruct a synthetic CREATE TABLE string from ObjectMeta column info."""
    cols = []
    for c in obj.columns:
        parts = [c.name, c.sql_type]
        if not c.nullable:
            parts.append("NOT NULL")
        if c.is_pk:
            parts.append("PRIMARY KEY")
        if c.fk_to:
            ref_table = c.fk_to.split(".")[0]
            parts.append(f"REFERENCES {ref_table}")
        cols.append("  " + " ".join(parts))
    return f"CREATE TABLE {obj.name} (\n" + ",\n".join(cols) + "\n)"


@router.post("/generate-form-by-table")
async def generate_form_by_table(
    req: GenerateFormByTableRequest,
    llm: LLMProvider = Depends(get_llm),
):
    """
    Look up an existing PostgreSQL table in the Semantic Twin and return
    form field descriptors — no raw DDL input required from the client.
    """
    if not req.tableName.strip():
        raise HTTPException(status_code=400, detail="tableName is required.")

    from ..semantic_twin.twin_service import get_twin_service
    svc = get_twin_service()
    obj = next(
        (o for o in svc.twin.objects if o.name == req.tableName and o.source == "postgresql"),
        None,
    )
    if obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Table '{req.tableName}' not found in schema twin. Call POST /api/schema/refresh first.",
        )

    ddl = _build_ddl_from_meta(obj)

    prompt = (
        "Given this SQL CREATE TABLE statement:\n\n"
        f"{ddl}\n\n"
        "Generate a JSON object with a 'fields' array. Each element describes one form field.\n"
        "Rules:\n"
        "- Skip auto-increment primary key columns.\n"
        "- Map SQL types: INT/BIGINT/FLOAT/DECIMAL -> number, BOOLEAN -> checkbox, DATE/DATETIME -> date, TEXT/LONGTEXT -> textarea, VARCHAR -> text.\n"
        "- For columns named 'email' use inputType 'email'.\n"
        "- For ENUM columns use inputType 'select' and populate options as [{value, label}].\n"
        "- required=true for NOT NULL columns that have no DEFAULT.\n"
        "- Each field: name (column name), label (human-readable title-case), inputType, required, options (empty list if not select/radio), default (null if none), validation (null if none).\n"
        "Return ONLY valid JSON matching the schema."
    )
    result: FormSchemaLLMResponse = await llm.generate_structured(
        prompt=prompt,
        response_schema=FormSchemaLLMResponse,
    )
    return result.fields


@router.post("/nl-query")
async def nl_query(
    req: NLQueryRequest,
    llm: LLMProvider = Depends(get_llm),
    db: PostgresService = Depends(get_db),
    mongo: MongoService = Depends(get_mongo),
):
    """
    Unified natural-language query endpoint backed by the LangGraph planner.

    Flow: classify_intent → retrieve_schema → [route] → generate/execute → response
    """
    if not req.nlQuery.strip():
        raise HTTPException(status_code=400, detail="nlQuery is required.")

    from ..planner.workflow import get_planner
    planner = get_planner(llm, db, mongo)
    state = await planner.run(req.nlQuery)

    if state.get("error") and not state.get("sql"):
        raise HTTPException(status_code=400, detail=state["error"])

    return {
        "sql": state.get("sql"),
        "ddl": state.get("ddl"),
        "mongo_query_spec": state.get("mongo_query_spec"),
        "hybrid_plan": state.get("hybrid_plan"),
        "viz_spec": state.get("viz_spec"),
        "result": state.get("result_rows", []),
        "columns": state.get("result_columns", []),
        "message": state.get("message", ""),
        "context_objects": state.get("context_objects", []),
        "intent": state["intent"].model_dump() if state.get("intent") else None,
        "error": state.get("error"),
        "repair_attempts": state.get("repair_attempts", 0),
        "repair_history": state.get("repair_history", []),
    }


@router.post("/insert-data")
async def insert_data(
    req: InsertDataRequest,
    db: PostgresService = Depends(get_db),
):
    """
    Create the table if it does not exist, then insert one row.
    Returns {"message": "inserted"} on success (matches frontend check).
    """
    if not db.table_exists(req.tableName):
        try:
            db.execute_ddl(req.tableSchema)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Table creation failed: {exc}",
            )

    try:
        db.insert_row(req.tableName, req.formData)
        return {"message": "inserted"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Insert failed: {exc}")


# ── Schema / Semantic Twin endpoints ─────────────────────────────────────

@router.get("/schema")
async def get_schema():
    """Return the current Semantic Twin state (tables, collections, last refresh time)."""
    from ..semantic_twin.twin_service import get_twin_service
    svc = get_twin_service()
    if not svc.twin.last_refreshed:
        return {"message": "Twin not yet built. Call POST /api/schema/refresh first.", "twin": None}
    return svc.twin.summary()


@router.post("/schema/refresh")
async def refresh_schema():
    """
    Re-introspect PostgreSQL and MongoDB and rebuild the FAISS index.
    Call after any CREATE TABLE or collection creation.
    """
    from ..semantic_twin.twin_service import get_twin_service
    svc = get_twin_service()
    try:
        twin = await svc.refresh()
        return {
            "message": f"Twin refreshed. {len(twin.objects)} object(s) indexed.",
            **twin.summary(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {exc}")


@router.get("/schema/objects/{name}")
async def get_schema_object(name: str):
    """Return full metadata for a single table or collection."""
    from ..semantic_twin.twin_service import get_twin_service
    svc = get_twin_service()
    obj = next((o for o in svc.twin.objects if o.name == name), None)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"Object '{name}' not found in twin.")
    return obj
