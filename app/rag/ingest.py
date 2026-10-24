import argparse
from pathlib import Path

from app.config import get_settings

from .bm25_index import invalidate_bm25_index
from .document_loader import load_pdf
from .section_splitter import SectionAwareSplitter
from .vector_store import ChromaStore


def ingest_pdf(
    pdf_path: str | Path,
    store: ChromaStore | None = None,
    replace: bool = True,
) -> int:
    settings = get_settings()
    path = Path(pdf_path)
    pages = load_pdf(path)
    splitter = SectionAwareSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    document_id = path.stem.replace(" ", "_")
    chunks = splitter.split_pages(pages, document_id=document_id)

    vector_store = store or ChromaStore()
    if replace:
        vector_store.delete_document(path.name)

    if not chunks:
        invalidate_bm25_index()
        return 0

    vector_store.add_documents(
        documents=[chunk.text for chunk in chunks],
        ids=[chunk.id for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )
    invalidate_bm25_index()
    return len(chunks)


def ingest_directory(directory: str | Path, store: ChromaStore | None = None) -> dict[str, int]:
    vector_store = store or ChromaStore()
    results: dict[str, int] = {}
    for pdf_path in sorted(Path(directory).glob("*.pdf")):
        results[pdf_path.name] = ingest_pdf(pdf_path, store=vector_store)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Import PDFs into the Chroma index.")
    parser.add_argument("pdf_path", nargs="+", type=Path)
    args = parser.parse_args()

    store = ChromaStore()
    for pdf_path in args.pdf_path:
        count = ingest_pdf(pdf_path, store=store)
        print(f"Ingested {count} chunks from {pdf_path}")
    print(f"Collection now holds {store.count()} chunks")


if __name__ == "__main__":
    main()
