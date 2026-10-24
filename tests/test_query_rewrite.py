import json

from app.config import Settings
from app.rag.query_rewrite import QueryRewriter


def make_settings(**overrides) -> Settings:
    return Settings(_env_file=None, deepseek_api_key=None, **overrides)


def test_rewrite_returns_english_query_unchanged(tmp_path) -> None:
    rewriter = QueryRewriter(settings=make_settings(), cache_path=tmp_path / "cache.json")
    assert rewriter.rewrite("What is MAIC?") == "What is MAIC?"


def test_rewrite_uses_cached_translation(tmp_path) -> None:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"MAIC 是什么？": "What is MAIC?"}, ensure_ascii=False),
        encoding="utf-8",
    )
    rewriter = QueryRewriter(settings=make_settings(), cache_path=cache_path)

    assert rewriter.rewrite("MAIC 是什么？") == "What is MAIC?"


def test_rewrite_without_api_key_falls_back_to_original(tmp_path) -> None:
    rewriter = QueryRewriter(settings=make_settings(), cache_path=tmp_path / "cache.json")

    assert rewriter.rewrite("MAIC 是什么？") == "MAIC 是什么？"
