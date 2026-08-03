import pytest
from orchestrator.consensus import ConsensusEngine
from models.schemas import Finding


@pytest.fixture
def consensus_engine():
    # Mock LLMClient
    class MockLLM:
        pass

    return ConsensusEngine(llm=MockLLM())


def test_parse_location(consensus_engine):
    assert consensus_engine._parse_location("src/main.py:10-15") == (
        "src/main.py",
        10,
        15,
    )
    assert consensus_engine._parse_location("src/main.py:10") == ("src/main.py", 10, 10)
    assert consensus_engine._parse_location("unknown") == ("unknown", 0, 0)


def test_overlap(consensus_engine):
    # Same file, overlapping ranges
    assert (
        consensus_engine._overlap("file.py:10-15", "file.py:12-20", tolerance=0) is True
    )
    assert (
        consensus_engine._overlap("file.py:10-15", "file.py:15-20", tolerance=0) is True
    )

    # Same file, no overlap, but within tolerance 5
    assert (
        consensus_engine._overlap("file.py:10-15", "file.py:20-25", tolerance=5) is True
    )

    # Same file, no overlap, outside tolerance
    assert (
        consensus_engine._overlap("file.py:10-15", "file.py:25-30", tolerance=5)
        is False
    )

    # Different files
    assert (
        consensus_engine._overlap("file1.py:10-15", "file2.py:10-15", tolerance=5)
        is False
    )


def test_group_by_location(consensus_engine):
    f1 = Finding(
        agent_name="A1",
        category="bug",
        severity="high",
        code_location="main.py:10-15",
        description="D1",
        explanation="E1",
        confidence=1.0,
    )
    f2 = Finding(
        agent_name="A2",
        category="bug",
        severity="high",
        code_location="main.py:12-18",
        description="D2",
        explanation="E2",
        confidence=1.0,
    )
    f3 = Finding(
        agent_name="A3",
        category="bug",
        severity="high",
        code_location="auth.py:50-55",
        description="D3",
        explanation="E3",
        confidence=1.0,
    )

    groups = consensus_engine._group_by_location([f1, f2, f3], tolerance=5)

    assert len(groups) == 2
    # f1 and f2 should be in the same group because they overlap
    assert len(groups[0]) == 2
    assert f1 in groups[0]
    assert f2 in groups[0]

    # f3 should be in its own group
    assert len(groups[1]) == 1
    assert f3 in groups[1]
