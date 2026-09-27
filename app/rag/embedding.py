import os
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer


class BGEEmbeddingFunction:
    def __init__(self):
        self.model = None

    def _get_model(self) -> SentenceTransformer:
        if self.model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_path = Path(
                os.getenv(
                    "EMBEDDING_MODEL_PATH",
                    str(Path(__file__).resolve().parents[2] / "models" / "bge-m3"),
                )
            )
            self.model = SentenceTransformer(
                str(model_path),
                device=device,
                local_files_only=True,
            )
        return self.model

    def encode(self, texts):
        return self._get_model().encode(
            texts,
            normalize_embeddings=True,
        ).tolist()

    def __call__(self, input):
        return self.encode(input)

    def embed_documents(self, input):
        return self.encode(input)

    def embed_query(self, input):
        return self.encode(input)

    def name(self):
        return "bge_m3"


embedding = BGEEmbeddingFunction()