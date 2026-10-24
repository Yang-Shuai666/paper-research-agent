import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings

from .agent_tools import TOOL_SCHEMAS, AgentTools
from .citations import extract_citations

DEFAULT_MAX_STEPS = 6
MAX_MAX_STEPS = 6

AGENT_SYSTEM_PROMPT = (
    "你是论文研究 Agent，可以调用工具检索本地论文库。规则：\n"
    "1. 事实型或单篇论文问题可直接调用 search_library；如果片段明显被截断，"
    "用 read_page 读取相关整页。页面返回 truncated，或流程/列表在页尾仍未结束时，"
    "继续读取相邻页。\n"
    "2. 涉及两篇及以上论文的对比问题，必须调用 compare_papers，"
    "让每篇论文都获得独立的检索名额。文件名已在系统提示中列出，可直接使用，"
    "无需先调用 list_papers。\n"
    "3. 工具结果中的 ref 编号就是证据编号。最终回答必须在事实性陈述后引用这些编号，"
    "如 [2] 或 [1][3]；不要编造编号。\n"
    "4. 只能依据工具返回的论文内容回答，禁止使用外部知识。"
    "信息不足时输出“信息不足：”并说明缺少什么信息。\n"
    "5. 证据足够时立即回答，不要用相同或高度相似的查询重复检索。"
    "先给结论，再给依据，用中文简洁回答。最多进行 6 步工具调用。\n"
    "6. 对“包含哪些步骤/模块/阶段”的问题，必须完整列出原文列出的全部项，"
    "不要只概括前几项；图标题、表标题和正文中的清单都要计入。"
)

FINAL_INSTRUCTION = (
    "工具调用已达上限。请只基于上面的工具结果给出最终回答，"
    "引用证据编号 [n]；如果证据不足，明确说明“信息不足：”。"
)


@dataclass(frozen=True)
class AgentResult:
    text: str
    sources: list[dict[str, Any]]
    steps: list[dict[str, Any]]
    citations: dict[str, list[int]]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    stop_reason: str = "answer"
    elapsed_ms: float = 0.0


def _summarize(tool_name: str, result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    if "error" in result:
        return f"error: {result['error']}"
    if tool_name == "list_papers":
        return f"{len(result.get('papers') or [])} papers"
    if tool_name == "search_library":
        return f"{len(result.get('results') or [])} passages"
    if tool_name == "read_page":
        return f"{len(result.get('chunks') or [])} chunks from p{result.get('page')}"
    if tool_name == "compare_papers":
        parts = [
            f"{paper}: {len(items)}"
            for paper, items in (result.get("papers") or {}).items()
        ]
        if result.get("missing"):
            parts.append(f"missing: {', '.join(result['missing'])}")
        return "; ".join(parts)
    return ""


async def _chat(
    client: httpx.AsyncClient,
    settings: Settings,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.deepseek_model,
        "temperature": 0.0,
        "messages": messages,
    }
    if tools is not None:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    response = await client.post(
        f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def _add_usage(data: dict[str, Any], totals: dict[str, int]) -> None:
    usage = data.get("usage") or {}
    totals["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
    totals["completion_tokens"] += int(usage.get("completion_tokens") or 0)


def _finish(
    text: str,
    tools: AgentTools,
    steps: list[dict[str, Any]],
    usage: dict[str, int],
    model: str,
    stop_reason: str,
    started: float,
) -> AgentResult:
    valid, invalid = extract_citations(text, len(tools.evidence))
    return AgentResult(
        text=text,
        sources=tools.evidence.sources(),
        steps=steps,
        citations={"valid": valid, "invalid": invalid},
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        model=model,
        stop_reason=stop_reason,
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )


async def run_agent(
    question: str,
    *,
    tools: AgentTools | None = None,
    settings: Settings | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    client: httpx.AsyncClient | None = None,
) -> AgentResult:
    config = settings or get_settings()
    if not config.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    agent_tools = tools or AgentTools(settings=config)
    max_steps = max(1, min(MAX_MAX_STEPS, max_steps))

    system_prompt = AGENT_SYSTEM_PROMPT
    summary = agent_tools.library_summary() if hasattr(agent_tools, "library_summary") else ""
    if summary:
        system_prompt = f"{system_prompt}\n\n当前论文库：\n{summary}"

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    steps: list[dict[str, Any]] = []
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    model = config.deepseek_model
    started = time.perf_counter()

    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=120)
    try:
        while True:
            data = await _chat(active_client, config, messages, tools=TOOL_SCHEMAS)
            _add_usage(data, usage)
            model = data.get("model") or model
            choice = data["choices"][0]
            message = choice.get("message") or {}
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                text = (message.get("content") or "").strip()
                if not text:
                    text = "信息不足：未能从论文库中检索到足够信息。"
                return _finish(
                    text,
                    agent_tools,
                    steps,
                    usage,
                    model,
                    "answer",
                    started,
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )

            for call in tool_calls:
                tool_name = (call.get("function") or {}).get("name") or "unknown"
                call_id = call.get("id") or f"call_{len(steps) + 1}"

                if len(steps) >= max_steps:
                    content = json.dumps(
                        {"error": "Tool step budget exhausted; answer with existing evidence."},
                        ensure_ascii=False,
                    )
                    messages.append(
                        {"role": "tool", "tool_call_id": call_id, "content": content}
                    )
                    continue

                raw_arguments = (call.get("function") or {}).get("arguments") or "{}"
                tool_started = time.perf_counter()
                error: Exception | None = None
                arguments: dict[str, Any] = {}
                try:
                    parsed_arguments = (
                        json.loads(raw_arguments)
                        if isinstance(raw_arguments, str)
                        else raw_arguments
                    )
                    if not isinstance(parsed_arguments, dict):
                        raise TypeError("Tool arguments must be a JSON object")
                    arguments = parsed_arguments
                    content = await asyncio.to_thread(
                        agent_tools.execute,
                        tool_name,
                        arguments,
                    )
                except Exception as exc:  # noqa: BLE001 - report tool errors back to the model
                    error = exc
                    content = json.dumps({"error": str(exc)}, ensure_ascii=False)

                try:
                    parsed_result: Any = json.loads(content)
                except json.JSONDecodeError:
                    parsed_result = content

                steps.append(
                    {
                        "step": len(steps) + 1,
                        "tool": tool_name,
                        "arguments": arguments,
                        "summary": _summarize(tool_name, parsed_result),
                        "latency_ms": round((time.perf_counter() - tool_started) * 1000, 1),
                        "ok": error is None,
                        "result": parsed_result,
                    }
                )
                messages.append(
                    {"role": "tool", "tool_call_id": call_id, "content": content}
                )

            if len(steps) >= max_steps:
                break

        messages.append({"role": "user", "content": FINAL_INSTRUCTION})
        data = await _chat(active_client, config, messages)
        _add_usage(data, usage)
        model = data.get("model") or model
        content = ((data["choices"][0].get("message") or {}).get("content") or "").strip()
        if not content:
            messages.append(
                {
                    "role": "user",
                    "content": "请直接输出最终中文答案，不要调用工具，不要留空。",
                }
            )
            data = await _chat(active_client, config, messages)
            _add_usage(data, usage)
            model = data.get("model") or model
            content = (
                (data["choices"][0].get("message") or {}).get("content") or ""
            ).strip()
        text = content or "信息不足：工具调用达到上限，未得到最终回答。"
        return _finish(
            text,
            agent_tools,
            steps,
            usage,
            model,
            "max_steps",
            started,
        )
    finally:
        if owns_client:
            await active_client.aclose()
