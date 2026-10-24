import math
from dataclasses import replace
from functools import lru_cache

from app.config import Settings, get_settings

from .device import limit_gpu_memory, resolve_device
from .retriever import RetrievedChunk


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(value, 60.0), -60.0)))


class CrossEncoderReranker:
    def __init__(
        self,
        model_path: str | None = None,
        settings: Settings | None = None,
        device: str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.device = resolve_device(device or self.settings.embedding_device)
        limit_gpu_memory(self.device, self.settings.embedding_gpu_memory_fraction)

        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(
            model_path or str(self.settings.reranker_model_path),
            device=str(self.device),
            max_length=512,
            local_files_only=True,
        )

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        scores = self.model.predict(
            [(query, chunk.text) for chunk in chunks],
            batch_size=self.settings.rerank_batch_size,
            show_progress_bar=False,
        )
        ranked = sorted(
            zip(chunks, scores, strict=True),
            key=lambda item: (-float(item[1]), item[0].id),
        )
        return [
            replace(chunk, score=_sigmoid(float(score)))
            for chunk, score in ranked[:top_k]
        ]


@lru_cache
def get_reranker() -> CrossEncoderReranker:
    return CrossEncoderReranker()
