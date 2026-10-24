from functools import lru_cache
from typing import Any

import chromadb

from app.config import get_settings

from .embedding import embedding


class ChromaStore:
    def __init__(self, path: str | None = None, collection_name: str | None = None) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=path or str(settings.chroma_path))
        self.collection_name = collection_name or settings.chroma_collection
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents, ids, metadatas=None) -> None:
        self.collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query: str, n_results: int = 3, where: dict | None = None) -> dict:
        kwargs: dict[str, Any] = {
            "query_texts": [query],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        return self.collection.query(**kwargs)

    def delete_document(self, file_name: str) -> None:
        self.collection.delete(where={"file_name": file_name})

    def count(self) -> int:
        return self.collection.count()

    def get_all(self) -> dict:
        return self.collection.get(include=["documents", "metadatas"])

    def get_by_ids(self, ids: list[str]) -> dict:
        return self.collection.get(ids=ids, include=["documents", "metadatas"])

    def get_page(self, file_name: str, page: int) -> dict:
        return self.collection.get(
            where={"$and": [{"file_name": file_name}, {"page": page}]},
            include=["documents", "metadatas"],
        )

    def list_documents(self) -> list[dict[str, Any]]:
        result = self.collection.get(include=["metadatas"])
        documents: dict[str, dict[str, Any]] = {}
        for metadata in result["metadatas"] or []:
            file_name = metadata.get("file_name")
            if not file_name:
                continue
            entry = documents.setdefault(
                str(file_name),
                {
                    "file_name": str(file_name),
                    "chunks": 0,
                    "pages": set(),
                    "sections": set(),
                },
            )
            entry["chunks"] += 1
            if metadata.get("page") is not None:
                entry["pages"].add(int(metadata["page"]))
            if metadata.get("section"):
                entry["sections"].add(str(metadata["section"]))

        return [
            {
                "file_name": entry["file_name"],
                "chunks": entry["chunks"],
                "pages": len(entry["pages"]),
                "sections": sorted(entry["sections"]),
            }
            for entry in sorted(documents.values(), key=lambda item: item["file_name"])
        ]

    def reset(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self._get_or_create_collection()


@lru_cache
def get_store() -> ChromaStore:
    return ChromaStore()
