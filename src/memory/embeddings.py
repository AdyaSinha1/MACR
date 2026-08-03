import hashlib
import json
import os
from typing import List, Dict
from structlog import get_logger
from sentence_transformers import SentenceTransformer

logger = get_logger()


class EmbeddingService:
    """Generates embeddings using sentence-transformers and caches them locally."""

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        cache_file: str = "data/.embeddings_cache.json",
    ):
        logger.info("Initializing EmbeddingService", model=model_name)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        self.model = SentenceTransformer(model_name)

        dimension = self.model.get_sentence_embedding_dimension()
        if not dimension:
            logger.warning(
                "Failed to get sentence embedding dimension dynamically. Defaulting to 768."
            )
            self.dimension = 768
        else:
            self.dimension = dimension

        self.cache_file = cache_file
        self.cache: Dict[str, List[float]] = self._load_cache()

    def _load_cache(self) -> Dict[str, List[float]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load embeddings cache", error=str(e))
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.error("Failed to save embeddings cache", error=str(e))

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get_embedding(self, text: str) -> List[float]:
        """Returns the vector embedding for a given text, using cache if available."""
        if not text.strip():
            logger.warning(
                "Empty text provided for embedding, returning zero vector")
            return [0.0] * self.dimension

        text_hash = self._hash_text(text)
        if text_hash in self.cache:
            return self.cache[text_hash]

        logger.debug("Computing new embedding")
        # Ensure it's a standard Python list of floats for JSON serialization
        embedding = self.model.encode(text).tolist()
        self.cache[text_hash] = embedding
        self._save_cache()
        return embedding
