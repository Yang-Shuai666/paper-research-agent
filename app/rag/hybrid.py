from dataclasses import replace

from .bm25_index import get_bm25_index
from .retriever import DenseRetriever, RetrievedChunk
from .vector_store import ChromaStore, get_store


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievedChunk]],
    top_k: int,
    rrf_k: int = 60,
    weights: list[float] | None = None,
) -> list[RetrievedChunk]:
    scores: dict[str, float] = {}
    chunks: dict[str, RetrievedChunk] = {}
    weights = weights or [1.0] * len(result_lists)
    if len(weights) != len(result_lists):
        raise ValueError("weights must match the number of result lists")

    for results, weight in zip(result_lists, weights, strict=True):
        for rank, chunk in enumerate(results, start=1):
            chunks.setdefault(chunk.id, chunk)
            scores[chunk.id] = scores.get(chunk.id, 0.0) + weight / (rrf_k + rank)

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [replace(chunks[chunk_id], score=score) for chunk_id, score in ranked[:top_k]]


class HybridRetriever:
    def __init__(
        self,
        store: ChromaStore | None = None,
        dense_candidates: int = 20,
        bm25_candidates: int = 20,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 0.25,
    ) -> None:
        self.store = store or get_store()
        self.dense = DenseRetriever(self.store)
        self.bm25 = get_bm25_index(self.store)
        self.dense_candidates = dense_candidates
        self.bm25_candidates = bm25_candidates
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        dense_results = self.dense.search(query, top_k=self.dense_candidates, where=where)
        sparse_results = self.bm25.search(query, top_k=self.bm25_candidates, where=where)
        result_lists = [dense_results]
        weights = [self.dense_weight]
        if sparse_results:
            result_lists.append(sparse_results)
            weights.append(self.sparse_weight)
        return reciprocal_rank_fusion(
            result_lists,
            top_k=top_k,
            rrf_k=self.rrf_k,
            weights=weights,
        )
