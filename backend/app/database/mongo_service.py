from typing import Any
from pymongo import MongoClient
from ..config import settings


class MongoService:
    """
    Thin wrapper around PyMongo.
    Only basic operations for Phase 1; expanded in Phase 3.
    """

    def __init__(self) -> None:
        self.client = MongoClient(settings.MONGO_URL)
        self.db = self.client[settings.MONGO_DB_NAME]

    def get_collection_names(self) -> list[str]:
        return self.db.list_collection_names()

    def get_schema_context(self) -> str:
        """Sample documents to infer schema for each collection."""
        collections = self.db.list_collection_names()
        if not collections:
            return "No collections found in MongoDB."

        lines: list[str] = []
        for col in collections:
            sample = self.db[col].find_one()
            if sample:
                fields = ", ".join(k for k in sample.keys() if k != "_id")
                lines.append(f"Collection {col}: fields ({fields})")
            else:
                lines.append(f"Collection {col}: (empty)")
        return "\n".join(lines)

    def find(self, collection: str, query: dict, limit: int = 100) -> list[dict[str, Any]]:
        results = list(self.db[collection].find(query, {"_id": 0}).limit(limit))
        return results

    def find_with_spec(
        self,
        collection: str,
        filter_: dict,
        projection: dict,
        sort: dict,
        limit: int,
    ) -> list[dict[str, Any]]:
        proj = {**projection, "_id": 0} if projection else {"_id": 0}
        sort_list = list(sort.items()) if sort else None
        cursor = self.db[collection].find(filter_, proj).limit(limit)
        if sort_list:
            cursor = cursor.sort(sort_list)
        return list(cursor)

    def aggregate(
        self,
        collection: str,
        pipeline: list[dict],
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        has_limit = any("$limit" in stage for stage in pipeline)
        effective_pipeline = pipeline if has_limit else pipeline + [{"$limit": limit}]
        results = list(self.db[collection].aggregate(effective_pipeline))
        for doc in results:
            doc.pop("_id", None)
        return results

    def collection_exists(self, name: str) -> bool:
        return name in self.db.list_collection_names()

    def create_collection(self, name: str) -> None:
        """
        Explicitly create a MongoDB collection.
        No-ops if the collection already exists (idempotent).
        """
        if not self.collection_exists(name):
            self.db.create_collection(name)

    def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        result = self.db[collection].insert_one(document)
        return str(result.inserted_id)
