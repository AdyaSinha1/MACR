import json
import os
from typing import Any, Dict, List, cast

import faiss
import numpy as np
from structlog import get_logger

from memory.embeddings import EmbeddingService
from models.schemas import FinalReport

logger = get_logger()


class FaissMemoryStore:
    """Manages the FAISS vector index for retrieving past code reviews."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        index_file: str = "data/.faiss_index",
        meta_file: str = "data/.faiss_meta.json",
    ) -> None:
        self.embedding_service = embedding_service
        self.dimension = getattr(embedding_service, "dimension", 768)

        self.index_file = index_file
        self.meta_file = meta_file

        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)

        self.metadata: List[Dict[str, Any]] = []

        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
            self.metadata = self._load_metadata()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load stored metadata from disk."""
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, "r") as file:
                    data: Any = json.load(file)
                    return cast(List[Dict[str, Any]], data)
            except Exception as error:
                logger.error(
                    "Failed to load FAISS metadata",
                    error=str(error),
                )

        return []

    def _save_index(self) -> None:
        """Persist FAISS index and metadata."""
        faiss.write_index(self.index, self.index_file)

        with open(self.meta_file, "w") as file:
            json.dump(self.metadata, file)

    def store_review(self, report: FinalReport) -> None:
        """Embeds and stores a completed review."""
        if not report.findings:
            return

        summary_text = "\n".join(
            f"[{finding.severity.upper()}] {finding.description}"
            for finding in report.findings
        )

        embedding = self.embedding_service.get_embedding(summary_text)

        vector = np.array([embedding], dtype=np.float32)

        self.index.add(vector)

        self.metadata.append(
            {
                "file_path": report.file_path,
                "findings_count": len(report.findings),
                "total_confidence": report.total_confidence,
                "summary": summary_text,
            }
        )

        self._save_index()

        logger.info(
            "Stored review in FAISS memory",
            file_path=report.file_path,
        )

    def retrieve_similar(
        self,
        query_text: str,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past reviews."""
        if self.index.ntotal == 0:
            return []

        embedding = self.embedding_service.get_embedding(query_text)

        query_vector = np.array([embedding], dtype=np.float32)

        _, indices = self.index.search(query_vector, k)

        results: List[Dict[str, Any]] = []

        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])

        return results
