import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.rag.agent import run_agent
from app.rag.agent_tools import EvidenceRegistry
from app.rag.retriever import RetrievedChunk


class FakeTools:
    def __init__(self, fail: bool = False) -> None:
        self.evidence = EvidenceRegistry()
        self.calls: list[tuple[str, dict]] = []
        self.fail = fail

    def library_summary(self) -> str:
        return "- paper.pdf（1 页，1 个片段）"

    def execute(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        if self.fail:
            raise ValueError("tool exploded")
        self.evidence.add(
            RetrievedChunk(
                id="paper_p1_000",
                text="evidence text",
                metadata={"file_name": "paper.pdf", "page": 1, "section": "Body"},
                score=0.9,
            )
        )
        return json.dumps(
            {
                "query": arguments.get("query"),
                "results": [
                    {
                        "ref": 1,
                        "source": "paper.pdf p1 Body",
                        "score": 0.9,
                        "text": "evidence text",
                    }
                ],
            },
            ensure_ascii=False,
        )


def install_transport(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    original_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        deepseek_api_key="test-key",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-flash",
    )


def tool_call_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": "deepseek-flash",
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "search_library",
                                    "arguments": '{"query": "RAG"}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        },
        request=request,
    )


def test_agent_executes_tool_and_returns_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return tool_call_response(request)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "答案 [1]"}}],
                "usage": {"prompt_tokens": 15, "completion_tokens": 3},
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    tools = FakeTools()

    result = asyncio.run(
        run_agent("问题是什么？", tools=tools, settings=make_settings(), max_steps=4)
    )

    assert result.text == "答案 [1]"
    assert result.citations == {"valid": [1], "invalid": []}
    assert result.sources[0]["ref"] == 1
    assert result.sources[0]["file_name"] == "paper.pdf"
    assert result.stop_reason == "answer"
    assert result.prompt_tokens == 25
    assert result.completion_tokens == 5
    assert tools.calls == [("search_library", {"query": "RAG"})]

    assert len(result.steps) == 1
    step = result.steps[0]
    assert step["tool"] == "search_library"
    assert step["summary"] == "1 passages"
    assert step["ok"] is True

    first_request, second_request = requests
    assert first_request["tool_choice"] == "auto"
    assert first_request["tools"][0]["function"]["name"] == "list_papers"
    assert "paper.pdf" in first_request["messages"][0]["content"]
    assert [message["role"] for message in second_request["messages"]] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]
    tool_message = second_request["messages"][-1]
    assert tool_message["tool_call_id"] == "call_1"
    assert json.loads(tool_message["content"])["results"][0]["ref"] == 1


def test_agent_stops_after_max_steps_and_forces_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if "tools" in requests[-1]:
            return tool_call_response(request)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "最终答案 [1]"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 4},
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    tools = FakeTools()

    result = asyncio.run(
        run_agent("需要多步的问题", tools=tools, settings=make_settings(), max_steps=2)
    )

    assert len(requests) == 3
    assert "tools" in requests[0]
    assert "tools" in requests[1]
    assert "tools" not in requests[2]
    assert result.stop_reason == "max_steps"
    assert len(result.steps) == 2
    assert result.text == "最终答案 [1]"
    assert requests[2]["messages"][-1]["content"].startswith("工具调用已达上限")


def test_agent_reports_tool_errors_to_the_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return tool_call_response(request)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "信息不足：工具失败。"}}],
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    tools = FakeTools(fail=True)

    result = asyncio.run(
        run_agent("问题", tools=tools, settings=make_settings(), max_steps=4)
    )

    assert result.steps[0]["ok"] is False
    assert "tool exploded" in result.steps[0]["summary"]
    tool_message = requests[1]["messages"][-1]
    assert "tool exploded" in tool_message["content"]
