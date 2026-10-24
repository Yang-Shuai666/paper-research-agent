import pytest

from app.rag.hybrid import reciprocal_rank_fusion
from app.rag.retriever import RetrievedChunk


def make_chunk(chunk_id: str, score: float = 0.0) -> RetrievedChunk:
    return RetrievedChunk(id=chunk_id, text=chunk_id, metadata={}, score=score)


def test_reciprocal_rank_fusion_prioritizes_consistent_results() -> None:
    dense = [make_chunk("a"), make_chunk("b"), make_chunk("c")]
    sparse = [make_chunk("c"), make_chunk("a")]

    fused = reciprocal_rank_fusion([dense, sparse], top_k=3, rrf_k=60)

    assert [chunk.id for chunk in fused] == ["a", "c", "b"]
    assert fused[0].score > fused[-1].score


def test_reciprocal_rank_fusion_handles_empty_lists() -> None:
    assert reciprocal_rank_fusion([], top_k=5) == []
    assert reciprocal_rank_fusion([[]], top_k=5) == []


def test_reciprocal_rank_fusion_applies_weights() -> None:
    dense = [make_chunk("a"), make_chunk("b")]
    sparse = [make_chunk("b"), make_chunk("a")]

    fused = reciprocal_rank_fusion([dense, sparse], top_k=2, rrf_k=60, weights=[3.0, 1.0])

    assert [chunk.id for chunk in fused] == ["a", "b"]


def test_reciprocal_rank_fusion_rejects_mismatched_weights() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([[make_chunk("a")]], top_k=1, weights=[1.0, 1.0])
