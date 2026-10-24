from app.eval.dataset import Evidence
from app.eval.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from app.rag.retriever import RetrievedChunk


def make_chunk(file_name: str, page: int, page_start: int | None = None) -> RetrievedChunk:
    metadata = {"file_name": file_name, "page": page}
    if page_start is not None:
        metadata["page_start"] = page_start
        metadata["page_end"] = page
    return RetrievedChunk(id=f"{file_name}-{page}", text="", metadata=metadata, score=0.0)


def test_recall_and_mrr_use_page_ranges() -> None:
    chunks = [make_chunk("a.pdf", 5), make_chunk("a.pdf", 3), make_chunk("b.pdf", 2)]
    evidence = (Evidence(file="a.pdf", pages=(2, 3)),)

    assert recall_at_k(chunks, evidence, 5) == 1.0
    assert recall_at_k(chunks, evidence, 1) == 0.0
    assert reciprocal_rank(chunks, evidence) == 0.5


def test_chunk_spanning_gold_page_matches() -> None:
    chunks = [make_chunk("a.pdf", 6, page_start=2)]
    evidence = (Evidence(file="a.pdf", pages=(4,)),)

    assert recall_at_k(chunks, evidence, 1) == 1.0


def test_multi_evidence_recall_and_ndcg() -> None:
    chunks = [make_chunk("a.pdf", 3), make_chunk("b.pdf", 2)]
    evidence = (
        Evidence(file="a.pdf", pages=(3,)),
        Evidence(file="b.pdf", pages=(2,)),
    )

    assert recall_at_k(chunks, evidence, 2) == 1.0
    assert reciprocal_rank(chunks, evidence) == 1.0
    assert 0.0 < ndcg_at_k(chunks, evidence, 2) <= 1.0


def test_metrics_ignore_questions_without_evidence() -> None:
    chunks = [make_chunk("a.pdf", 3)]

    assert recall_at_k(chunks, (), 3) is None
    assert ndcg_at_k(chunks, (), 3) is None
