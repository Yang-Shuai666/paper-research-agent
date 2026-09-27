from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
	text: str
	id: str
	metadata: dict[str, str | int]


class TextSplitter:
	def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
		if chunk_size <= 0:
			raise ValueError("chunk_size must be positive")
		if chunk_overlap < 0 or chunk_overlap >= chunk_size:
			raise ValueError("chunk_overlap must be between 0 and chunk_size")

		self.chunk_size = chunk_size
		self.chunk_overlap = chunk_overlap

	def split(
		self,
		text: str,
		metadata: dict[str, str | int],
		document_id: str,
	) -> list[TextChunk]:
		normalized_text = " ".join(text.split())
		if not normalized_text:
			return []

		chunks: list[TextChunk] = []
		start = 0
		chunk_number = 0
		step = self.chunk_size - self.chunk_overlap

		while start < len(normalized_text):
			end = min(start + self.chunk_size, len(normalized_text))
			chunk_id = f"{document_id}_{chunk_number}"
			chunks.append(
				TextChunk(
					text=normalized_text[start:end],
					id=chunk_id,
					metadata={**metadata, "chunk_id": chunk_id},
				)
			)
			start += step
			chunk_number += 1

		return chunks
