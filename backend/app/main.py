from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Build the Semantic Twin on startup so the first query is already
    schema-aware. Fails gracefully if databases are empty or unreachable.
    """
    try:
        from .semantic_twin.twin_service import get_twin_service
        svc = get_twin_service()
        twin = await svc.refresh()
        print(f"[startup] Semantic Twin built: {len(twin.objects)} object(s) indexed.")
    except Exception as exc:
        print(f"[startup] Warning: Semantic Twin build skipped — {exc}")
    yield


app = FastAPI(
    title="Unified AI Database Copilot",
    version="1.0.0",
    description="LLM-powered natural-language interface for PostgreSQL and MongoDB.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
