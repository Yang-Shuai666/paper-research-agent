import re
from functools import lru_cache

from app.config import get_settings

from .retriever import RetrievedChunk
from .vector_store import ChromaStore, get_store

CHUNK_ID_RE = re.compile(r"^(?P<prefix>.+_p\d+_)(?P<number>\d+)$")


class ContextExpander:
    """Adds neighboring chunks from the same page to improve answer completeness."""

    def __init__(
        self,
        store: ChromaStore | None = None,
        window: int = 2,
        max_chunks: int = 16,
    ) -> None:
        self.store = store or get_store()
        self.window = window
        self.max_chunks = max_chunks

    def expand(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []

        scores = {chunk.id: chunk.score for chunk in chunks}
        pages: dict[str, list[RetrievedChunk]] = {}
        page_order: list[str] = []
        passthrough: list[RetrievedChunk] = []

        for chunk in chunks:
            match = CHUNK_ID_RE.match(chunk.id)
            if not match:
                passthrough.append(chunk)
                continue
            prefix = match.group("prefix")
            if prefix not in pages:
                pages[prefix] = []
                page_order.append(prefix)
            pages[prefix].append(chunk)

        wanted_ids: list[str] = []
        for prefix in page_order:
            selected_numbers: list[int] = []
            for chunk in pages[prefix]:
                match = CHUNK_ID_RE.match(chunk.id)
                number = int(match.group("number")) if match else 0
                if number not in selected_numbers:
                    selected_numbers.append(number)

            ordered_numbers: list[int] = []
            for number in selected_numbers:
                candidates = [number]
                for offset in range(1, self.window + 1):
                    candidates.extend((number - offset, number + offset))
                for candidate in candidates:
                    if candidate >= 0 and candidate not in ordered_numbers:
                        ordered_numbers.append(candidate)

            for number in ordered_numbers:
                chunk_id = f"{prefix}{number:03d}"
                if chunk_id not in wanted_ids:
                    wanted_ids.append(chunk_id)
                if len(wanted_ids) >= self.max_chunks:
                    break
            if len(wanted_ids) >= self.max_chunks:
                break

        if wanted_ids:
            result = self.store.get_by_ids(wanted_ids)
            by_id = {
                chunk_id: RetrievedChunk(
                    id=chunk_id,
                    text=document or "",
                    metadata=metadata or {},
                    score=scores.get(chunk_id, 0.0),
                )
                for chunk_id, document, metadata in zip(
                    result["ids"],
                    result["documents"],
                    result["metadatas"],
                    strict=True,
                )
            }
            chunks_out = [by_id[chunk_id] for chunk_id in wanted_ids if chunk_id in by_id]
        else:
            chunks_out = []

        chunks_out.extend(passthrough)
        return chunks_out[: self.max_chunks]


@lru_cache
def get_expander() -> ContextExpander:
    settings = get_settings()
    return ContextExpander(
        window=settings.context_expansion_window,
        max_chunks=settings.context_expansion_max_chunks,
    )
