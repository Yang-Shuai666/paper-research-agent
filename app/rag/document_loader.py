from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz


@dataclass(frozen=True)
class DocumentPage:
    text: str
    metadata: dict[str, str | int]


def load_pdf(path: str | Path) -> list[DocumentPage]:
    pdf_path = Path(path)
    pages: list[DocumentPage] = []

    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if not text:
                continue

            pages.append(
                DocumentPage(
                    text=text,
                    metadata={
                        "file_name": pdf_path.name,
                        "page": page_number,
                        "source_path": str(pdf_path),
                    },
                )
            )

    return pages