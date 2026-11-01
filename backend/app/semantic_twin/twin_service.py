"""
SemanticTwinService — central orchestrator for Phase 4.

Lifecycle:
  1. refresh() introspects PostgreSQL + MongoDB.
  2. Builds ObjectMeta list with embedding_text for each object.
  3. Encodes all texts with EmbeddingService (Sentence Transformers).
  4. Stores embeddings in a FAISS IndexFlatIP (cosine similarity).
  5. Persists index + metadata to faiss_index/ for faster restarts.
  6. retrieve(query, k) embeds the query and returns top-k ObjectMeta.

Callers (LLM agents) get a compact schema context string via
  twin.get_context_for_objects(retrieved_names)
instead of dumping the entire schema into the prompt.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from .models import DatabaseTwin, ObjectMeta
from .embedding_service import get_embedding_service
from .vector_store import VectorStore
from .sql_introspector import introspect_postgres
from .mongo_introspector import introspect_mongo

_FAISS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "faiss_index")
_INDEX_PATH = os.path.join(_FAISS_DIR, "index.bin")
_META_PATH = os.path.join(_FAISS_DIR, "metadata.json")

_instance: "SemanticTwinService | None" = None


class SemanticTwinService:
    def __init__(self) -> None:
        self.twin = DatabaseTwin()
        self._store: VectorStore | None = None
        self._emb = get_embedding_service()

    # ── Public API ────────────────────────────────────────────────────────

    async def refresh(self) -> DatabaseTwin:
        """
        Re-introspect both databases and rebuild the FAISS index.
        Call after any schema-changing operation (CREATE TABLE / collection).
        """
        from ..database.postgres_service import PostgresService
        from ..database.mongo_service import MongoService

        db = PostgresService()
        mongo = MongoService()

        sql_objects = introspect_postgres(db.engine)
        mongo_objects = introspect_mongo(mongo.db)
        all_objects = sql_objects + mongo_objects

        if all_objects:
            texts = [obj.embedding_text for obj in all_objects]
            # Run CPU-bound encoding off the event loop
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(None, self._emb.encode, texts)

            from .embedding_service import EMBEDDING_DIM
            self._store = VectorStore(dim=EMBEDDING_DIM)
            self._store.add(embeddings, [obj.name for obj in all_objects])
            self._store.save(_INDEX_PATH, _META_PATH)
        else:
            self._store = None

        self.twin = DatabaseTwin(
            objects=all_objects,
            last_refreshed=datetime.now(timezone.utc).isoformat(),
        )
        return self.twin

    async def retrieve(self, query: str, k: int = 5) -> list[ObjectMeta]:
        """
        Embed query and return top-k most relevant ObjectMeta items.
        Falls back to returning all objects when the index is empty.
        """
        if self._store is None or self._store.size == 0:
            return self.twin.objects

        loop = asyncio.get_running_loop()
        q_emb = await loop.run_in_executor(None, self._emb.encode, [query])
        results = self._store.search(q_emb[0], k=k)
        names = {name for name, _ in results}
        return [o for o in self.twin.objects if o.name in names]

    def get_schema_context(self, query: str | None = None) -> str:
        """
        Synchronous helper: return the full schema as a context string.
        Used as a fallback when the async retrieve path is unavailable.
        """
        if not self.twin.objects:
            return "No database objects found. Create tables or collections first."
        return "\n".join(o.to_context_string() for o in self.twin.objects)

    def _try_load_from_disk(self) -> bool:
        """Attempt to restore a previously saved FAISS index from disk."""
        if os.path.exists(_INDEX_PATH) and os.path.exists(_META_PATH):
            try:
                self._store = VectorStore.load(_INDEX_PATH, _META_PATH)
                with open(_META_PATH) as f:
                    meta = json.load(f)
                # Rebuild in-memory twin objects list from metadata names only
                # (full column data requires a fresh introspection)
                return True
            except Exception:
                pass
        return False


def get_twin_service() -> SemanticTwinService:
    global _instance
    if _instance is None:
        _instance = SemanticTwinService()
    return _instance
