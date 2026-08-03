import hashlib
import json
import os
from typing import Dict, List, cast

from sentence_transformers import SentenceTransformer
from structlog import get_logger

logger = get_logger()


class EmbeddingService:
    """Generates embeddings using sentence-transformers and caches them locally."""

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        cache_file: str = "data/.embeddings_cache.json",
    ):
        logger.info(
            "Initializing EmbeddingService",
            model=model_name,
        )

        os.makedirs(
            os.path.dirname(cache_file),
            exist_ok=True,
        )

        self.model = SentenceTransformer(model_name)

        dimension = self.model.get_sentence_embedding_dimension()

        if not dimension:
            logger.warning("Failed to get embedding dimension. " "Defaulting to 768.")
            self.dimension = 768
        else:
            self.dimension = dimension

        self.cache_file = cache_file
        self.cache: Dict[str, List[float]] = self._load_cache()

    def _load_cache(self) -> Dict[str, List[float]]:
        """Load cached embeddings from disk."""

        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as file:
                    data = json.load(file)

                return cast(
                    Dict[str, List[float]],
                    data,
                )

            except Exception as exc:
                logger.error(
                    "Failed to load embeddings cache",
                    error=str(exc),
                )

        return {}

    def _save_cache(self) -> None:
        """Save embeddings cache to disk."""

        try:
            with open(self.cache_file, "w") as file:
                json.dump(self.cache, file)

        except Exception as exc:
            logger.error(
                "Failed to save embeddings cache",
                error=str(exc),
            )

    def _hash_text(self, text: str) -> str:
        """Generate a deterministic hash for text."""

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get_embedding(self, text: str) -> List[float]:
        """Return vector embedding for given text."""

        if not text.strip():
            logger.warning("Empty text provided. Returning zero vector.")

            return [0.0] * self.dimension

        text_hash = self._hash_text(text)

        if text_hash in self.cache:
            return self.cache[text_hash]

        logger.debug("Computing new embedding")

        embedding = cast(
            List[float],
            self.model.encode(text).tolist(),
        )

        self.cache[text_hash] = embedding

        self._save_cache()

        return embedding
