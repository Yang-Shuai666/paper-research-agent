from fastapi.testclient import TestClient

from app.main import app
from app.rag.agent import AgentResult

client = TestClient(app)


def test_agent_endpoint_returns_trace(monkeypatch) -> None:
    async def fake_run_agent(query: str, *, max_steps: int = 4) -> AgentResult:
        assert query == "对比两篇论文"
        assert max_steps == 2
        return AgentResult(
            text="答案 [1]",
            sources=[{"ref": 1, "file_name": "paper.pdf", "page": 3}],
            steps=[
                {
                    "step": 1,
                    "tool": "compare_papers",
                    "arguments": {"query": "对比", "papers": ["paper.pdf"]},
                    "summary": "paper.pdf: 1",
                    "latency_ms": 12.5,
                    "ok": True,
                    "result": {},
                }
            ],
            citations={"valid": [1], "invalid": []},
            prompt_tokens=100,
            completion_tokens=20,
            model="deepseek-flash",
            stop_reason="answer",
            elapsed_ms=1234.5,
        )

    monkeypatch.setattr("app.main.run_agent", fake_run_agent)

    response = client.post("/agent/ask", json={"query": "对比两篇论文", "max_steps": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "答案 [1]"
    assert body["citations"] == {"valid": [1], "invalid": []}
    assert body["steps"][0]["tool"] == "compare_papers"
    assert body["usage"] == {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "model": "deepseek-flash",
    }
    assert body["stop_reason"] == "answer"


def test_agent_endpoint_validates_step_budget() -> None:
    response = client.post("/agent/ask", json={"query": "问题", "max_steps": 0})

    assert response.status_code == 422
