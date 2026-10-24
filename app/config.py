from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    embedding_model_path: Path = PROJECT_ROOT / "models" / "bge-m3"
    embedding_device: str = "auto"
    embedding_gpu_memory_fraction: float = Field(default=0.15, ge=0.05, le=1.0)

    chroma_path: Path = PROJECT_ROOT / "data" / "chroma_db"
    chroma_collection: str = "papers_bge_m3"
    chunk_size: int = Field(default=600, ge=200, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=500)

    retrieval_mode: str = "hybrid"
    dense_candidates: int = Field(default=20, ge=5, le=100)
    bm25_candidates: int = Field(default=20, ge=5, le=100)
    rrf_k: int = Field(default=20, ge=1, le=1000)
    dense_weight: float = Field(default=1.0, gt=0, le=10)
    sparse_weight: float = Field(default=0.25, ge=0, le=10)

    enable_query_rewrite: bool = True
    query_rewrite_cache_path: Path = PROJECT_ROOT / "data" / "cache" / "query_rewrites.json"
    query_rewrite_timeout: float = Field(default=30.0, gt=0)

    enable_rerank: bool = True
    reranker_model_path: Path = PROJECT_ROOT / "models" / "bge-reranker-v2-m3"
    rerank_candidates: int = Field(default=12, ge=5, le=100)
    rerank_batch_size: int = Field(default=8, ge=1, le=64)

    enable_context_expansion: bool = True
    context_expansion_window: int = Field(default=2, ge=0, le=10)
    context_expansion_max_chunks: int = Field(default=16, ge=1, le=50)

    @field_validator(
        "embedding_model_path",
        "chroma_path",
        "reranker_model_path",
        "query_rewrite_cache_path",
    )
    @classmethod
    def resolve_relative_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
