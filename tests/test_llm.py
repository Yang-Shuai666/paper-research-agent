import asyncio

import httpx
import pytest

from app.config import Settings
from app.rag.llm import generate_answer


def test_generate_answer_uses_deepseek_compatible_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "答案 [1]"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4},
            },
            request=request,
        )

    original_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    settings = Settings(
        _env_file=None,
        deepseek_api_key="test-key",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-flash",
    )
    answer = asyncio.run(
        generate_answer(
            "问题是什么？",
            [{"metadata": {"page": 2}, "document": "论文片段"}],
            settings,
        )
    )

    assert answer.text == "答案 [1]"
    assert answer.prompt_tokens == 12
    assert answer.completion_tokens == 4
    assert answer.model == "deepseek-flash"
    assert len(requests) == 1
    assert str(requests[0].url) == "https://api.deepseek.com/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert requests[0].content.find(b'"model":"deepseek-flash"') >= 0
