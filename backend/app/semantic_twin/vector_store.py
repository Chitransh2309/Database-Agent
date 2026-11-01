import json
import os
import numpy as np
import faiss


class VectorStore:
    """
    FAISS inner-product index for cosine similarity search over
    normalized schema embeddings (output of EmbeddingService.encode).
    """

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self._names: list[str] = []  # positional mapping: row i → object name

    # ── Mutation ──────────────────────────────────────────────────────────

    def add(self, embeddings: np.ndarray, names: list[str]) -> None:
        assert embeddings.ndim == 2 and embeddings.shape[1] == self.dim
        assert len(names) == embeddings.shape[0]
        self.index.add(embeddings.astype(np.float32))
        self._names.extend(names)

    def reset(self) -> None:
        self.index.reset()
        self._names.clear()

    # ── Query ─────────────────────────────────────────────────────────────

    def search(self, query: np.ndarray, k: int) -> list[tuple[str, float]]:
        """Return (name, cosine_score) pairs, highest score first."""
        total = self.index.ntotal
        if total == 0:
            return []
        k = min(k, total)
        scores, indices = self.index.search(
            query.reshape(1, -1).astype(np.float32), k
        )
        return [
            (self._names[int(idx)], float(score))
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0
        ]

    @property
    def size(self) -> int:
        return self.index.ntotal

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, index_path: str, meta_path: str) -> None:
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.index, index_path)
        with open(meta_path, "w") as f:
            json.dump({"dim": self.dim, "names": self._names}, f)

    @classmethod
    def load(cls, index_path: str, meta_path: str) -> "VectorStore":
        with open(meta_path) as f:
            meta = json.load(f)
        store = cls(dim=meta["dim"])
        store.index = faiss.read_index(index_path)
        store._names = meta["names"]
        return store
