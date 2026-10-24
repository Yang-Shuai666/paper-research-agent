from app.rag.document_loader import DocumentPage
from app.rag.section_splitter import SectionAwareSplitter


def make_page(text: str, page: int) -> DocumentPage:
    return DocumentPage(
        text=text,
        metadata={"file_name": "paper.pdf", "page": page, "source_path": "paper.pdf"},
    )


def test_split_pages_tracks_sections_and_skips_references() -> None:
    pages = [
        make_page("1 Introduction\nThis is the introduction. It has two sentences.", 1),
        make_page(
            "2 Method\nWe propose a method. It works well.\nReferences\n[1] Someone. 2020.",
            2,
        ),
        make_page("3 Results\nThe results are strong.", 3),
    ]

    chunks = SectionAwareSplitter(
        chunk_size=80, chunk_overlap=10, min_chunk_size=10
    ).split_pages(pages, document_id="paper")

    assert chunks
    assert any(chunk.metadata["section"] == "1 Introduction" for chunk in chunks)
    assert any(chunk.metadata["section"] == "2 Method" for chunk in chunks)
    assert all("References" not in chunk.text for chunk in chunks)
    assert all(chunk.metadata["page"] <= 2 for chunk in chunks)
    assert all(chunk.metadata["page_start"] == chunk.metadata["page_end"] for chunk in chunks)


def test_split_pages_resumes_after_reference_list() -> None:
    pages = [
        make_page("References\n[1] A. Author. 2020. A paper.", 1),
        make_page("[2] B. Author. 2021. Another paper. et al.", 2),
        make_page("A Related Work\nThis appendix discusses related work in prose.", 3),
    ]

    chunks = SectionAwareSplitter(
        chunk_size=100, chunk_overlap=10, min_chunk_size=10
    ).split_pages(pages, document_id="paper")

    assert chunks
    assert all(chunk.metadata["page"] == 3 for chunk in chunks)
    assert any(chunk.metadata["section"] == "A Related Work" for chunk in chunks)


def test_lowercase_references_in_body_does_not_start_reference_section() -> None:
    pages = [
        make_page(
            "1 Introduction\nWe provide references for LLMs to verify outputs. "
            "This sentence is still body text.",
            1,
        )
    ]

    chunks = SectionAwareSplitter(
        chunk_size=100, chunk_overlap=10, min_chunk_size=10
    ).split_pages(pages, document_id="paper")

    assert chunks
    assert "references for LLMs" in chunks[0].text


def test_split_pages_builds_sentence_chunks_with_unique_ids() -> None:
    text = (
        "1 Background\n"
        "Sentence one is here. Sentence two follows it. Sentence three adds detail. "
        "Sentence four continues. Sentence five ends the section."
    )
    pages = [make_page(text, 1)]

    chunks = SectionAwareSplitter(
        chunk_size=60, chunk_overlap=15, min_chunk_size=10
    ).split_pages(pages, document_id="paper")

    assert len(chunks) > 1
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(chunk.metadata["chunk_id"] == chunk.id for chunk in chunks)
    assert all(chunk.metadata["section"] == "1 Background" for chunk in chunks)
