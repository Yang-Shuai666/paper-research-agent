from app.rag.vector_store import ChromaStore


def main() -> None:
    store = ChromaStore()
    before = store.count()
    store.reset()
    print(f"Reset collection '{store.collection_name}' ({before} chunks removed)")


if __name__ == "__main__":
    main()
