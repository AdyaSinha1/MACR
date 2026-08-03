import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any
from structlog import get_logger

from models.schemas import FinalReport
from memory.embeddings import EmbeddingService

logger = get_logger()

class FaissMemoryStore:
    """Manages the FAISS vector index for retrieving past code reviews."""
    
    def __init__(self, embedding_service: EmbeddingService, index_file: str = "data/.faiss_index", meta_file: str = "data/.faiss_meta.json"):
        self.embedding_service = embedding_service
        self.dimension = getattr(embedding_service, 'dimension', 768)
        self.index_file = index_file
        self.meta_file = meta_file
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
            self.metadata = self._load_metadata()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

    def _load_metadata(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load FAISS metadata", error=str(e))
        return []

    def _save_index(self):
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, 'w') as f:
            json.dump(self.metadata, f)

    def store_review(self, report: FinalReport):
        """Embeds and stores the summary of a completed code review."""
        if not report.findings:
            return
            
        summary_text = "\n".join([f"[{f.severity.upper()}] {f.description}" for f in report.findings])
        embedding = self.embedding_service.get_embedding(summary_text)
        
        # Add to FAISS index (requires 2D numpy array)
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Store corresponding metadata
        self.metadata.append({
            "file_path": report.file_path,
            "findings_count": len(report.findings),
            "total_confidence": report.total_confidence,
            "summary": summary_text
        })
        self._save_index()
        logger.info("Stored review in FAISS memory", file_path=report.file_path)

    def retrieve_similar(self, query_text: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves the top k most similar past reviews based on semantic similarity."""
        if self.index.ntotal == 0:
            return []
            
        embedding = self.embedding_service.get_embedding(query_text)
        distances, indices = self.index.search(np.array([embedding], dtype=np.float32), k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results
