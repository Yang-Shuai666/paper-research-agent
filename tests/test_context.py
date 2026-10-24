from app.rag.context import ContextExpander
from app.rag.retriever import RetrievedChunk


class FakeStore:
    def __init__(self) -> None:
        self.documents: dict[str, str] = {}

    def get_by_ids(self, ids: list[str]) -> dict:
        return {
            "ids": ids,
            "documents": [self.documents.get(chunk_id, chunk_id) for chunk_id in ids],
            "metadatas": [{"chunk_id": chunk_id} for chunk_id in ids],
        }


def make_chunk(chunk_id: str, score: float = 0.0) -> RetrievedChunk:
    return RetrievedChunk(id=chunk_id, text=chunk_id, metadata={}, score=score)


def test_expand_adds_neighbors_within_the_same_page() -> None:
    store = FakeStore()
    expander = ContextExpander(store=store, window=1, max_chunks=10)

    chunks = expander.expand([make_chunk("doc_p1_002", 0.9), make_chunk("doc_p1_005", 0.8)])

    assert [chunk.id for chunk in chunks] == [
        "doc_p1_002",
        "doc_p1_001",
        "doc_p1_003",
        "doc_p1_005",
        "doc_p1_004",
        "doc_p1_006",
    ]
    assert chunks[0].score == 0.9


def test_expand_keeps_pages_in_rank_order_and_respects_budget() -> None:
    store = FakeStore()
    expander = ContextExpander(store=store, window=1, max_chunks=4)

    chunks = expander.expand([make_chunk("doc_p1_002"), make_chunk("doc_p2_003")])

    assert [chunk.id for chunk in chunks] == [
        "doc_p1_002",
        "doc_p1_001",
        "doc_p1_003",
        "doc_p2_003",
    ]


def test_expand_passes_unknown_ids_through() -> None:
    expander = ContextExpander(store=FakeStore(), window=1, max_chunks=10)

    chunks = expander.expand([make_chunk("legacy-doc")])

    assert [chunk.id for chunk in chunks] == ["legacy-doc"]
