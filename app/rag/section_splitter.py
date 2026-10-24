import re
from dataclasses import dataclass

from .document_loader import DocumentPage
from .text_splitter import TextChunk

HEADING_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*|[IVX]+\.?|[A-Z]\.|[A-Z])\s+[A-Z][A-Za-z0-9 ,:&\-]{2,90}$"
)
ALL_CAPS_HEADING_RE = re.compile(r"^[A-Z][A-Z0-9 ,:&\-]{3,70}$")
REFERENCE_RE = re.compile(
    r"^\s*(?:[IVX]+\.\s*)?(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\b"
)
SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass(frozen=True)
class _Segment:
    section: str
    text: str


def _is_heading(line: str) -> bool:
    if len(line) > 100 or line.endswith((".", ",", ";", ":")):
        return False
    if HEADING_RE.match(line):
        return True
    return bool(ALL_CAPS_HEADING_RE.match(line) and len(line.split()) <= 8)


APPENDIX_RE = re.compile(r"^(?:Appendix\b|[A-Z]\s+[A-Z][A-Za-z]+(?:\s+[A-Za-z]+){1,4})")


def _looks_like_prose(line: str) -> bool:
    return (
        bool(line)
        and not line.endswith(".")
        and "et al." not in line
        and not re.search(r"\b(?:19|20)\d{2}\b", line)
        and "DOI" not in line
    )


def _has_appendix_heading(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if APPENDIX_RE.match(line) and _looks_like_prose(line):
            return True
        if (
            re.fullmatch(r"[A-Z]", line)
            and index + 1 < len(lines)
            and re.match(r"^[A-Z][A-Za-z]+(?:\s+[A-Za-z]+){0,4}$", lines[index + 1])
            and _looks_like_prose(lines[index + 1])
        ):
            return True
    return False


def _page_segments(text: str) -> list[_Segment]:
    segments: list[_Segment] = []
    section = "Body"
    lines: list[str] = []

    def flush() -> None:
        if lines:
            segments.append(_Segment(section=section, text=" ".join(lines)))

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_heading(line):
            flush()
            section = line[:80]
            lines = [line]
        else:
            lines.append(line)
    flush()
    return segments


def _tail_sentences(sentences: list[str], overlap: int) -> tuple[list[str], int]:
    tail: list[str] = []
    length = 0
    for sentence in reversed(sentences):
        if tail and length + len(sentence) + 1 > overlap:
            break
        tail.insert(0, sentence)
        length += len(sentence) + 1
    return tail, length


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += step
    return chunks


def _chunk_sentences(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
) -> list[str]:
    sentences = [sentence.strip() for sentence in SENTENCE_RE.split(text) if sentence.strip()]
    chunks: list[str] = []
    buffer: list[str] = []
    length = 0

    for sentence in sentences:
        if len(sentence) > chunk_size:
            if buffer:
                chunks.append(" ".join(buffer))
                buffer, length = [], 0
            chunks.extend(_hard_split(sentence, chunk_size, chunk_overlap))
            continue

        if buffer and length + len(sentence) + 1 > chunk_size:
            chunks.append(" ".join(buffer))
            buffer, length = _tail_sentences(buffer, chunk_overlap)
            if length + len(sentence) + 1 > chunk_size:
                buffer, length = [], 0

        buffer.append(sentence)
        length += len(sentence) + 1

    if buffer:
        chunks.append(" ".join(buffer))

    if len(chunks) > 1 and len(chunks[-1]) < min_chunk_size:
        tail = chunks.pop()
        chunks[-1] = f"{chunks[-1]} {tail}"
    return chunks


class SectionAwareSplitter:
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        min_chunk_size: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be between 0 and chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_pages(self, pages: list[DocumentPage], document_id: str) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        in_references = False
        chunk_number = 0

        for page in pages:
            if in_references:
                if not _has_appendix_heading(page.text):
                    continue
                in_references = False

            kept_lines: list[str] = []
            for line in page.text.splitlines():
                if REFERENCE_RE.match(line.strip()):
                    in_references = True
                    break
                kept_lines.append(line)
            if not kept_lines:
                continue

            page_number = int(page.metadata["page"])
            for segment in _page_segments("\n".join(kept_lines)):
                normalized = " ".join(segment.text.split())
                if len(normalized) < 20:
                    continue

                for text in _chunk_sentences(
                    normalized,
                    self.chunk_size,
                    self.chunk_overlap,
                    self.min_chunk_size,
                ):
                    chunk_id = f"{document_id}_p{page_number}_{chunk_number:03d}"
                    metadata = {
                        **page.metadata,
                        "page": page_number,
                        "page_start": page_number,
                        "page_end": page_number,
                        "section": segment.section,
                        "chunk_id": chunk_id,
                    }
                    chunks.append(TextChunk(text=text, id=chunk_id, metadata=metadata))
                    chunk_number += 1

        return chunks
