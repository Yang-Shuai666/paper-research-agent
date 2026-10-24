from sentence_transformers import SentenceTransformer

from app.config import get_settings

from .device import limit_gpu_memory, resolve_device


class BGEEmbeddingFunction:
    def __init__(self) -> None:
        self.model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self.model is None:
            settings = get_settings()
            device = resolve_device(settings.embedding_device)
            limit_gpu_memory(device, settings.embedding_gpu_memory_fraction)
            self.model = SentenceTransformer(
                str(settings.embedding_model_path),
                device=str(device),
                local_files_only=True,
            )
        return self.model

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self._get_model().encode(
            texts,
            normalize_embeddings=True,
        ).tolist()

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.encode(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.encode(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.encode(input)

    def name(self) -> str:
        return "bge_m3"


embedding = BGEEmbeddingFunction()
