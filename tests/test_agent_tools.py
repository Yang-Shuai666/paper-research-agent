import json

import pytest

from app.rag.agent_tools import AgentTools
from app.rag.retriever import RetrievedChunk


def make_chunk(
    chunk_id: str,
    file_name: str,
    page: int = 1,
    section: str = "Body",
    score: float = 0.5,
) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        text=f"text of {chunk_id}",
        metadata={
            "file_name": file_name,
            "page": page,
            "section": section,
            "chunk_id": chunk_id,
        },
        score=score,
    )


class FakeStore:
    def __init__(self, documents: dict[str, list[RetrievedChunk]]) -> None:
        self.documents = documents

    def list_documents(self) -> list[dict]:
        return [
            {
                "file_name": name,
                "chunks": len(chunks),
                "pages": len({chunk.metadata["page"] for chunk in chunks}),
                "sections": sorted({chunk.metadata["section"] for chunk in chunks}),
            }
            for name, chunks in sorted(self.documents.items())
        ]

    def get_page(self, file_name: str, page: int) -> dict:
        chunks = [
            chunk
            for chunk in self.documents.get(file_name, [])
            if chunk.metadata["page"] == page
        ]
        return {
            "ids": [chunk.id for chunk in chunks],
            "documents": [chunk.text for chunk in chunks],
            "metadatas": [chunk.metadata for chunk in chunks],
        }


class FakePipeline:
    def __init__(self, documents: dict[str, list[RetrievedChunk]]) -> None:
        self.documents = documents
        self.calls: list[tuple[str, int, dict | None]] = []

    def search(self, query: str, top_k: int = 10, where: dict | None = None):
        self.calls.append((query, top_k, where))
        file_name = (where or {}).get("file_name")
        if file_name:
            chunks = self.documents.get(file_name, [])
        else:
            chunks = [chunk for items in self.documents.values() for chunk in items]
        return chunks[:top_k]


def make_tools() -> tuple[AgentTools, FakePipeline]:
    documents = {
        "a.pdf": [
            make_chunk("a_p1_000", "a.pdf", page=1),
            make_chunk("a_p1_001", "a.pdf", page=1),
            make_chunk("a_p2_002", "a.pdf", page=2),
        ],
        "b.pdf": [
            make_chunk("b_p1_000", "b.pdf", page=1, section="Method"),
        ],
    }
    pipeline = FakePipeline(documents)
    tools = AgentTools(pipeline=pipeline, store=FakeStore(documents))
    return tools, pipeline


def test_compare_papers_retrieves_each_paper_separately() -> None:
    tools, pipeline = make_tools()

    payload = json.loads(
        tools.execute(
            "compare_papers",
            {
                "query": "compare methods",
                "papers": ["a.pdf", "b.pdf", "missing.pdf"],
                "top_k_per_paper": 2,
            },
        )
    )

    assert pipeline.calls == [
        ("compare methods", 2, {"file_name": "a.pdf"}),
        ("compare methods", 2, {"file_name": "b.pdf"}),
    ]
    assert len(payload["papers"]["a.pdf"]) == 2
    assert len(payload["papers"]["b.pdf"]) == 1
    assert payload["missing"] == ["missing.pdf"]
    assert [item["ref"] for item in payload["papers"]["a.pdf"]] == [1, 2]
    assert payload["papers"]["b.pdf"][0]["ref"] == 3
    assert payload["papers"]["b.pdf"][0]["source"] == "b.pdf p1 Method"


def test_compare_papers_resolves_names_without_pdf_suffix() -> None:
    tools, pipeline = make_tools()

    payload = json.loads(
        tools.execute(
            "compare_papers",
            {"query": "methods", "papers": ["a", "b.pdf"], "top_k_per_paper": 1},
        )
    )

    assert pipeline.calls == [
        ("methods", 1, {"file_name": "a.pdf"}),
        ("methods", 1, {"file_name": "b.pdf"}),
    ]
    assert list(payload["papers"]) == ["a.pdf", "b.pdf"]


def test_read_page_returns_sorted_chunks_and_reuses_refs() -> None:
    tools, _ = make_tools()

    first = json.loads(tools.execute("read_page", {"file_name": "a.pdf", "page": 1}))
    second = json.loads(tools.execute("read_page", {"file_name": "a.pdf", "page": 1}))

    assert [chunk["ref"] for chunk in first["chunks"]] == [1, 2]
    assert [chunk["ref"] for chunk in second["chunks"]] == [1, 2]
    assert first["total_chunks"] == 2
    assert len(tools.evidence) == 2


def test_search_library_clamps_top_k_and_deduplicates_evidence() -> None:
    tools, pipeline = make_tools()

    first = json.loads(tools.execute("search_library", {"query": "RAG", "top_k": 999}))
    second = json.loads(tools.execute("search_library", {"query": "RAG"}))

    assert pipeline.calls[0] == ("RAG", 10, None)
    assert len(first["results"]) == 4
    assert [item["ref"] for item in second["results"]] == [1, 2, 3, 4]
    assert len(tools.evidence) == 4


def test_list_papers_reports_indexed_documents() -> None:
    tools, _ = make_tools()

    payload = json.loads(tools.execute("list_papers", {}))

    assert [paper["file_name"] for paper in payload["papers"]] == ["a.pdf", "b.pdf"]
    assert payload["papers"][1]["sections"] == ["Method"]


def test_invalid_tool_arguments_raise() -> None:
    tools, _ = make_tools()

    with pytest.raises(ValueError, match="query"):
        tools.execute("search_library", {"query": " "})
    with pytest.raises(ValueError, match="Unknown tool"):
        tools.execute("delete_everything", {})
