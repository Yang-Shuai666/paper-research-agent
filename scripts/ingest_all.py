from app.config import PROJECT_ROOT
from app.rag.ingest import ingest_directory
from app.rag.vector_store import ChromaStore

PAPERS_DIR = PROJECT_ROOT / "data" / "papers"


def main() -> None:
    store = ChromaStore()
    results = ingest_directory(PAPERS_DIR, store=store)
    for file_name, count in results.items():
        print(f"{file_name}: {count} chunks")
    print(f"Collection now holds {store.count()} chunks")


if __name__ == "__main__":
    main()
