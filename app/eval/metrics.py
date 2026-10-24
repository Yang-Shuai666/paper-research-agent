import math
from collections.abc import Iterable

from app.eval.dataset import Evidence
from app.rag.retriever import RetrievedChunk


def _matches(chunk: RetrievedChunk, evidence: Evidence) -> bool:
    metadata = chunk.metadata
    if metadata.get("file_name") != evidence.file:
        return False
    page = int(metadata.get("page", -1))
    page_start = int(metadata.get("page_start", page))
    page_end = int(metadata.get("page_end", page))
    return any(page_start <= gold_page <= page_end for gold_page in evidence.pages)


def is_relevant(chunk: RetrievedChunk, evidence: Iterable[Evidence]) -> bool:
    return any(_matches(chunk, item) for item in evidence)


def recall_at_k(
    chunks: list[RetrievedChunk],
    evidence: tuple[Evidence, ...],
    k: int,
) -> float | None:
    if not evidence:
        return None
    top_chunks = chunks[:k]
    hits = sum(
        1 for item in evidence if any(_matches(chunk, item) for chunk in top_chunks)
    )
    return hits / len(evidence)


def reciprocal_rank(chunks: list[RetrievedChunk], evidence: tuple[Evidence, ...]) -> float:
    if not evidence:
        return 0.0
    for rank, chunk in enumerate(chunks, start=1):
        if is_relevant(chunk, evidence):
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    chunks: list[RetrievedChunk],
    evidence: tuple[Evidence, ...],
    k: int,
) -> float | None:
    if not evidence:
        return None

    matched: set[int] = set()
    dcg = 0.0
    for rank, chunk in enumerate(chunks[:k], start=1):
        for index, item in enumerate(evidence):
            if index not in matched and _matches(chunk, item):
                matched.add(index)
                dcg += 1.0 / math.log2(rank + 1)
                break

    ideal = sum(1.0 / math.log2(index + 2) for index in range(len(evidence)))
    return dcg / ideal if ideal else None
