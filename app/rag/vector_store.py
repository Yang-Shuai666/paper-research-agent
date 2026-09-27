import chromadb
from pathlib import Path

from .embedding import embedding


class ChromaStore:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(Path(__file__).resolve().parents[2] / "data" / "chroma_db")
        )

        self.collection = self.client.get_or_create_collection(
            name="papers_bge_m3",
            embedding_function=embedding,
        )

    def add_documents(self, documents, ids, metadatas=None):
        self.collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query, n_results=3):
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

    def delete_document(self, file_name: str) -> None:
        self.collection.delete(where={"file_name": file_name})