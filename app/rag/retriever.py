from dataclasses import dataclass
from typing import Any

from .vector_store import ChromaStore, get_store


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class DenseRetriever:
    def __init__(self, store: ChromaStore | None = None) -> None:
        self.store = store or get_store()

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        result = self.store.search(query, n_results=top_k, where=where)
        chunks: list[RetrievedChunk] = []
        for index, chunk_id in enumerate(result["ids"][0]):
            chunks.append(
                RetrievedChunk(
                    id=chunk_id,
                    text=result["documents"][0][index],
                    metadata=result["metadatas"][0][index] or {},
                    score=1.0 - float(result["distances"][0][index]),
                )
            )
        return chunks
