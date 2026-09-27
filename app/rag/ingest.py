import argparse
from pathlib import Path

from .document_loader import load_pdf
from .text_splitter import TextSplitter
from .vector_store import ChromaStore


def ingest_pdf(pdf_path: str | Path, store: ChromaStore | None = None) -> int:
    path = Path(pdf_path)
    pages = load_pdf(path)
    splitter = TextSplitter()
    chunks = []

    document_id = path.stem.replace(" ", "_")
    for page in pages:
        chunks.extend(
            splitter.split(
                text=page.text,
                metadata=page.metadata,
                document_id=f"{document_id}_page_{page.metadata['page']}",
            )
        )

    if not chunks:
        return 0

    vector_store = store or ChromaStore()
    vector_store.add_documents(
        documents=[chunk.text for chunk in chunks],
        ids=[chunk.id for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a PDF into the Chroma index.")
    parser.add_argument("pdf_path", type=Path)
    args = parser.parse_args()

    count = ingest_pdf(args.pdf_path)
    print(f"Ingested {count} chunks from {args.pdf_path}")


if __name__ == "__main__":
    main()