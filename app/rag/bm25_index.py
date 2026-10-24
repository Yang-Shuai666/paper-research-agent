import logging
import re

import jieba
from rank_bm25 import BM25Okapi

from .retriever import RetrievedChunk
from .vector_store import ChromaStore, get_store

jieba.setLogLevel(logging.WARNING)

ENGLISH_TOKEN_RE = re.compile(r"[a-z0-9_]+")
CHINESE_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = ENGLISH_TOKEN_RE.findall(lowered)
    for segment in CHINESE_TOKEN_RE.findall(lowered):
        tokens.extend(token for token in jieba.lcut(segment) if token.strip())
    return tokens


def _matches_where(metadata: dict, where: dict | None) -> bool:
    if not where:
        return True
    if "$and" in where:
        return all(_matches_where(metadata, condition) for condition in where["$and"])
    return all(metadata.get(key) == value for key, value in where.items())


class BM25Index:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.corpus = [tokenize(chunk.text) for chunk in chunks]
        self.bm25 = BM25Okapi(self.corpus) if self.corpus else None

    @classmethod
    def from_store(cls, store: ChromaStore | None = None) -> "BM25Index":
        store = store or get_store()
        result = store.get_all()
        chunks = [
            RetrievedChunk(
                id=chunk_id,
                text=document or "",
                metadata=result["metadatas"][index] or {},
                score=0.0,
            )
            for index, (chunk_id, document) in enumerate(
                zip(result["ids"], result["documents"], strict=True)
            )
        ]
        return cls(chunks)

    def search(
        self,
        query: str,
        top_k: int = 20,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        if self.bm25 is None:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
        results: list[RetrievedChunk] = []
        for index in ranked:
            score = float(scores[index])
            if score <= 0:
                break
            chunk = self.chunks[index]
            if not _matches_where(chunk.metadata, where):
                continue
            results.append(
                RetrievedChunk(
                    id=chunk.id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    score=score,
                )
            )
            if len(results) >= top_k:
                break
        return results


_index: BM25Index | None = None
_index_count = -1


def get_bm25_index(store: ChromaStore | None = None) -> BM25Index:
    global _index, _index_count
    store = store or get_store()
    count = store.count()
    if _index is None or count != _index_count:
        _index = BM25Index.from_store(store)
        _index_count = count
    return _index


def invalidate_bm25_index() -> None:
    global _index, _index_count
    _index = None
    _index_count = -1
