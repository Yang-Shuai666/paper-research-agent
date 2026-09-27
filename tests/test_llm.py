import asyncio

import httpx
import pytest

from app.rag.llm import LLMSettings, generate_answer


def test_generate_answer_uses_deepseek_compatible_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "答案 [1]"}}]},
            request=request,
        )

    original_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    answer = asyncio.run(
        generate_answer(
            "问题是什么？",
            [{"metadata": {"page": 2}, "document": "论文片段"}],
            LLMSettings(api_key="test-key"),
        )
    )

    assert answer == "答案 [1]"
    assert len(requests) == 1
    assert str(requests[0].url) == "https://api.deepseek.com/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert requests[0].content.find(b'"model":"deepseek-chat"') >= 0