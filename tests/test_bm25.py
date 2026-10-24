from app.rag.bm25_index import BM25Index
from app.rag.retriever import RetrievedChunk


def make_chunk(chunk_id: str, file_name: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        text=text,
        metadata={"file_name": file_name, "page": 1},
        score=0.0,
    )


def test_bm25_search_respects_metadata_filter() -> None:
    index = BM25Index(
        [
            make_chunk("a_p1_000", "a.pdf", "alpha beta"),
            make_chunk("b_p1_000", "b.pdf", "alpha gamma"),
            make_chunk("c_p1_000", "c.pdf", "gamma delta"),
            make_chunk("d_p1_000", "d.pdf", "delta epsilon"),
            make_chunk("e_p1_000", "e.pdf", "epsilon zeta"),
        ]
    )

    results = index.search("alpha", top_k=5, where={"file_name": "b.pdf"})

    assert [chunk.id for chunk in results] == ["b_p1_000"]


def test_bm25_search_returns_empty_without_tokens() -> None:
    index = BM25Index([make_chunk("a_p1_000", "a.pdf", "alpha beta")])

    assert index.search("!!!", top_k=5) == []
