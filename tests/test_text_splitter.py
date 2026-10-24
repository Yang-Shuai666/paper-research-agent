import pytest

from app.rag.text_splitter import TextSplitter


def test_split_returns_empty_list_for_blank_text() -> None:
    splitter = TextSplitter()

    assert splitter.split(" \n\t ", {"page": 1}, "doc") == []


def test_split_normalizes_whitespace_and_keeps_metadata() -> None:
    splitter = TextSplitter(chunk_size=10, chunk_overlap=0)

    chunks = splitter.split("hello\n\nworld  again", {"page": 3}, "doc_page_3")

    assert [chunk.text for chunk in chunks] == ["hello worl", "d again"]
    assert chunks[0].id == "doc_page_3_0"
    assert chunks[0].metadata == {"page": 3, "chunk_id": "doc_page_3_0"}
    assert chunks[1].metadata["chunk_id"] == "doc_page_3_1"


def test_split_overlaps_consecutive_chunks() -> None:
    splitter = TextSplitter(chunk_size=10, chunk_overlap=3)

    chunks = splitter.split("abcdefghijklmnop", {"page": 1}, "doc")

    assert chunks[0].text == "abcdefghij"
    assert chunks[1].text == "hijklmnop"


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 11)],
)
def test_split_rejects_invalid_sizes(chunk_size: int, chunk_overlap: int) -> None:
    with pytest.raises(ValueError):
        TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
