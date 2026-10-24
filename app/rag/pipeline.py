import logging

from app.config import Settings, get_settings

from .hybrid import HybridRetriever
from .query_rewrite import QueryRewriter, get_rewriter
from .reranker import CrossEncoderReranker, get_reranker
from .retriever import DenseRetriever, RetrievedChunk

logger = logging.getLogger(__name__)

BaseRetriever = DenseRetriever | HybridRetriever


class RetrievalPipeline:
    def __init__(
        self,
        retriever: BaseRetriever,
        rewriter: QueryRewriter | None = None,
        reranker: CrossEncoderReranker | None = None,
        candidate_k: int = 20,
    ) -> None:
        self.retriever = retriever
        self.rewriter = rewriter
        self.reranker = reranker
        self.candidate_k = candidate_k

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        search_query = self.rewriter.rewrite(query) if self.rewriter else query
        fetch_k = max(top_k, self.candidate_k) if self.reranker else top_k
        chunks = self.retriever.search(search_query, top_k=fetch_k, where=where)
        if self.reranker:
            # The translated query improves recall; the original query preserves
            # intent for the multilingual cross-encoder.
            chunks = self.reranker.rerank(query, chunks, top_k=top_k)
        return chunks[:top_k]


def build_retriever(
    mode: str | None = None,
    *,
    enable_rewrite: bool | None = None,
    enable_rerank: bool | None = None,
    settings: Settings | None = None,
) -> RetrievalPipeline:
    settings = settings or get_settings()
    selected = (mode or settings.retrieval_mode).lower()

    retriever: BaseRetriever
    if selected == "dense":
        retriever = DenseRetriever()
    elif selected == "hybrid":
        retriever = HybridRetriever(
            dense_candidates=settings.dense_candidates,
            bm25_candidates=settings.bm25_candidates,
            rrf_k=settings.rrf_k,
            dense_weight=settings.dense_weight,
            sparse_weight=settings.sparse_weight,
        )
    else:
        raise ValueError(f"Unknown retrieval mode: {selected}")

    rewrite = settings.enable_query_rewrite if enable_rewrite is None else enable_rewrite
    rerank = settings.enable_rerank if enable_rerank is None else enable_rerank
    rewriter = get_rewriter() if rewrite else None
    reranker: CrossEncoderReranker | None = None
    if rerank:
        try:
            reranker = get_reranker()
        except Exception as error:  # noqa: BLE001 - reranking is optional
            logger.warning("Reranker unavailable, continuing without it: %s", error)

    return RetrievalPipeline(
        retriever,
        rewriter=rewriter,
        reranker=reranker,
        candidate_k=settings.rerank_candidates,
    )
