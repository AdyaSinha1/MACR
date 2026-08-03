import pytest
from memory.faiss_store import FaissMemoryStore
from models.schemas import FinalReport, Finding


class MockEmbeddingService:
    dimension = 4

    def get_embedding(self, text):
        return [0.1, 0.2, 0.3, 0.4]


@pytest.fixture
def temp_faiss_store(tmp_path):
    index_file = str(tmp_path / "test.index")
    meta_file = str(tmp_path / "test_meta.json")
    embedding_service = MockEmbeddingService()
    # Initialize FaissMemoryStore with a temporary path
    store = FaissMemoryStore(
        embedding_service, index_file=index_file, meta_file=meta_file
    )
    return store


def test_store_and_retrieve_review(temp_faiss_store):
    f1 = Finding(
        agent_name="A",
        category="bug",
        severity="high",
        code_location="x:1",
        description="desc",
        explanation="exp",
        confidence=1.0,
    )
    report = FinalReport(
        file_path="main.py", findings=[f1], agent_agreement=1.0, total_confidence=1.0
    )

    # Initially empty
    assert temp_faiss_store.index.ntotal == 0
    assert len(temp_faiss_store.metadata) == 0

    # Store review
    temp_faiss_store.store_review(report)

    assert temp_faiss_store.index.ntotal == 1
    assert len(temp_faiss_store.metadata) == 1
    assert temp_faiss_store.metadata[0]["file_path"] == "main.py"

    # Retrieve
    results = temp_faiss_store.retrieve_similar("query text", k=1)

    assert len(results) == 1
    assert results[0]["file_path"] == "main.py"
    assert results[0]["findings_count"] == 1
