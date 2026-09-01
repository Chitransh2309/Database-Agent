import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_instance: "EmbeddingService | None" = None


class EmbeddingService:
    """
    Wraps Sentence Transformers for schema object embedding.
    Model is loaded lazily on first use (~90 MB download on first run).
    Uses cosine similarity (normalized L2 → inner product = cosine).
    """

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return float32 normalized embeddings, shape (N, EMBEDDING_DIM)."""
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32)
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).astype(np.float32)


def get_embedding_service() -> EmbeddingService:
    global _instance
    if _instance is None:
        _instance = EmbeddingService()
    return _instance
