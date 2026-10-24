import json
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings

from .pipeline import RetrievalPipeline, build_retriever
from .retriever import RetrievedChunk
from .vector_store import ChromaStore, get_store

MAX_TOOL_TOP_K = 10
MAX_COMPARE_PAPERS = 4
MAX_PAGE_CHUNKS = 24


class EvidenceRegistry:
    """Assigns stable [n] numbers to every chunk shown to the agent."""

    def __init__(self) -> None:
        self._chunks: list[RetrievedChunk] = []
        self._refs: dict[str, int] = {}

    def add(self, chunk: RetrievedChunk) -> int:
        existing = self._refs.get(chunk.id)
        if existing is not None:
            return existing
        self._chunks.append(chunk)
        ref = len(self._chunks)
        self._refs[chunk.id] = ref
        return ref

    def add_many(self, chunks: list[RetrievedChunk]) -> list[int]:
        return [self.add(chunk) for chunk in chunks]

    def __len__(self) -> int:
        return len(self._chunks)

    @property
    def chunks(self) -> list[RetrievedChunk]:
        return list(self._chunks)

    def sources(self) -> list[dict[str, Any]]:
        return [
            {
                "ref": ref,
                **chunk.metadata,
                "score": round(float(chunk.score), 4),
            }
            for ref, chunk in enumerate(self._chunks, start=1)
        ]


def _source_label(metadata: dict[str, Any]) -> str:
    parts = [
        metadata.get("file_name"),
        f"p{metadata.get('page')}" if metadata.get("page") else None,
        metadata.get("section"),
    ]
    return " ".join(str(part) for part in parts if part)


def _require_str(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{key}` must be a non-empty string")
    return value.strip()


def _clamp_top_k(value: Any, default: int) -> int:
    if value is None:
        value = default
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("`top_k` must be an integer") from error
    return max(1, min(MAX_TOOL_TOP_K, number))


class AgentTools:
    def __init__(
        self,
        pipeline: RetrievalPipeline | None = None,
        store: ChromaStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or get_store()
        self.pipeline = pipeline or build_retriever(settings=self.settings)
        self.evidence = EvidenceRegistry()

    def library_summary(self) -> str:
        try:
            documents = self.store.list_documents()
        except Exception:  # noqa: BLE001 - prompt enrichment is optional
            return ""
        if not documents:
            return "（论文库为空）"
        return "\n".join(
            f"- {item['file_name']}（{item['pages']} 页，{item['chunks']} 个片段）"
            for item in documents
        )

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        handlers = {
            "list_papers": self.list_papers,
            "search_library": self.search_library,
            "read_page": self.read_page,
            "compare_papers": self.compare_papers,
        }
        handler = handlers.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")
        result = handler(**arguments)
        return json.dumps(result, ensure_ascii=False)

    def list_papers(self) -> dict[str, Any]:
        return {"papers": self.store.list_documents()}

    def search_library(self, query: str, top_k: int = 5) -> dict[str, Any]:
        question = _require_str(query, "query")
        chunks = self.pipeline.search(question, top_k=_clamp_top_k(top_k, 5))
        refs = self.evidence.add_many(chunks)
        return {
            "query": question,
            "results": [
                {
                    "ref": ref,
                    "source": _source_label(chunk.metadata),
                    "score": round(float(chunk.score), 4),
                    "text": chunk.text,
                }
                for ref, chunk in zip(refs, chunks, strict=True)
            ],
        }

    def read_page(self, file_name: str, page: int) -> dict[str, Any]:
        name = Path(_require_str(file_name, "file_name")).name
        try:
            page_number = int(page)
        except (TypeError, ValueError) as error:
            raise ValueError("`page` must be an integer") from error
        if page_number < 1:
            raise ValueError("`page` must be positive")

        result = self.store.get_page(name, page_number)
        chunks = []
        for chunk_id, document, metadata in zip(
            result["ids"],
            result["documents"],
            result["metadatas"],
            strict=True,
        ):
            chunks.append(
                RetrievedChunk(
                    id=chunk_id,
                    text=document or "",
                    metadata=metadata or {},
                    score=0.0,
                )
            )
        chunks.sort(key=lambda chunk: chunk.id)
        total_chunks = len(chunks)
        chunks = chunks[:MAX_PAGE_CHUNKS]
        refs = self.evidence.add_many(chunks)
        payload: dict[str, Any] = {
            "file_name": name,
            "page": page_number,
            "total_chunks": total_chunks,
            "chunks": [
                {
                    "ref": ref,
                    "section": chunk.metadata.get("section"),
                    "text": chunk.text,
                }
                for ref, chunk in zip(refs, chunks, strict=True)
            ],
        }
        if not total_chunks:
            payload["note"] = "No indexed text on this page; try another page."
        elif total_chunks > MAX_PAGE_CHUNKS:
            payload["truncated"] = True
        return payload

    def compare_papers(
        self,
        query: str,
        papers: list[str],
        top_k_per_paper: int = 2,
    ) -> dict[str, Any]:
        question = _require_str(query, "query")
        if isinstance(papers, str):
            papers = [papers]
        if not isinstance(papers, list) or not papers:
            raise ValueError("`papers` must be a non-empty list of file names")

        names: list[str] = []
        for item in papers:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("every paper must be a non-empty file name")
            name = Path(item.strip()).name
            if name not in names:
                names.append(name)
        if len(names) > MAX_COMPARE_PAPERS:
            raise ValueError(f"compare at most {MAX_COMPARE_PAPERS} papers at once")

        per_paper_k = _clamp_top_k(top_k_per_paper, 2)
        indexed = {item["file_name"] for item in self.store.list_documents()}
        resolved: dict[str, str] = {}
        for name in names:
            candidate = name
            if candidate not in indexed and not candidate.lower().endswith(".pdf"):
                with_suffix = f"{candidate}.pdf"
                if with_suffix in indexed:
                    candidate = with_suffix
            resolved[name] = candidate
        resolved_names = list(dict.fromkeys(resolved[name] for name in names))
        missing = [name for name in resolved_names if name not in indexed]

        results: dict[str, list[dict[str, Any]]] = {}
        for name in resolved_names:
            if name in missing:
                continue
            chunks = self.pipeline.search(
                question,
                top_k=per_paper_k,
                where={"file_name": name},
            )
            refs = self.evidence.add_many(chunks)
            results[name] = [
                {
                    "ref": ref,
                    "source": _source_label(chunk.metadata),
                    "score": round(float(chunk.score), 4),
                    "text": chunk.text,
                }
                for ref, chunk in zip(refs, chunks, strict=True)
            ]

        payload: dict[str, Any] = {"query": question, "papers": results}
        if missing:
            payload["missing"] = missing
            payload["note"] = "Use list_papers to check indexed file names."
        return payload


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_papers",
            "description": (
                "List the indexed papers with page and chunk counts. "
                "Use it when you need valid file names for compare_papers."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_library",
            "description": (
                "Search the local paper library for passages relevant to a query. "
                "Use for factoid or single-paper questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {
                        "type": "integer",
                        "description": "Number of passages, 1-10",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": (
                "Read every indexed chunk on one page of a paper. "
                "Use when search results look truncated or a list/table spans a page."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Exact PDF file name"},
                    "page": {"type": "integer", "description": "1-based page number"},
                },
                "required": ["file_name", "page"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_papers",
            "description": (
                "Retrieve evidence separately for each named paper. "
                "MUST be used for cross-paper comparison questions; it guarantees "
                "that every paper gets retrieval slots."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to compare"},
                    "papers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "PDF file names, 2-4 papers",
                    },
                    "top_k_per_paper": {
                        "type": "integer",
                        "description": "Passages per paper, 1-10",
                        "default": 2,
                    },
                },
                "required": ["query", "papers"],
            },
        },
    },
]
