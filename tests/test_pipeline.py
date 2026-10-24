from app.rag.pipeline import RetrievalPipeline
from app.rag.retriever import RetrievedChunk


def make_chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(id=chunk_id, text=chunk_id, metadata={}, score=0.0)


class FakeRetriever:
    def __init__(self) -> None:
        self.query = ""
        self.top_k = 0
        self.where: dict | None = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        self.query = query
        self.top_k = top_k
        self.where = where
        return [make_chunk("a"), make_chunk("b"), make_chunk("c")][:top_k]


class FakeRewriter:
    def rewrite(self, query: str) -> str:
        return f"rewritten: {query}"


class FakeReranker:
    def __init__(self) -> None:
        self.query = ""

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        self.query = query
        return list(reversed(chunks))[:top_k]


def test_pipeline_rewrites_query_before_retrieval() -> None:
    retriever = FakeRetriever()
    pipeline = RetrievalPipeline(retriever, rewriter=FakeRewriter())

    pipeline.search("问题", top_k=2)

    assert retriever.query == "rewritten: 问题"
    assert retriever.top_k == 2


def test_pipeline_fetches_more_candidates_before_reranking() -> None:
    retriever = FakeRetriever()
    reranker = FakeReranker()
    pipeline = RetrievalPipeline(
        retriever,
        rewriter=FakeRewriter(),
        reranker=reranker,
        candidate_k=10,
    )

    chunks = pipeline.search("query", top_k=2)

    assert retriever.query == "rewritten: query"
    assert reranker.query == "query"
    assert retriever.top_k == 10
    assert [chunk.id for chunk in chunks] == ["c", "b"]


def test_pipeline_propagates_metadata_filter() -> None:
    retriever = FakeRetriever()
    pipeline = RetrievalPipeline(retriever)

    pipeline.search("query", top_k=2, where={"file_name": "paper.pdf"})

    assert retriever.where == {"file_name": "paper.pdf"}
