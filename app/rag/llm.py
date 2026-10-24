from dataclasses import dataclass

from app.config import Settings, get_settings

SYSTEM_PROMPT = (
    "你是论文研究助手。只能依据提供的论文片段回答，禁止使用片段外的知识。"
    "要求：\n"
    "1. 用中文回答，先给结论，再给必要依据。\n"
    "2. 每个事实性陈述后标注来源编号，如 [1] 或 [1][3]；编号必须对应片段编号。\n"
    "3. 如果片段不足以回答，只输出“信息不足：”并说明缺少什么信息，不要猜测。\n"
    "4. 不要输出片段列表之外的引用编号。"
)


@dataclass(frozen=True)
class AnswerResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""


def _format_contexts(contexts: list[dict]) -> str:
    lines = []
    for index, item in enumerate(contexts, start=1):
        metadata = item.get("metadata") or {}
        source = " ".join(
            part
            for part in (
                metadata.get("file_name"),
                f"p{metadata.get('page')}" if metadata.get("page") else None,
                metadata.get("section"),
            )
            if part
        )
        lines.append(f"[{index}] {source}\n{item['document']}")
    return "\n\n".join(lines)


async def generate_answer(
    question: str,
    contexts: list[dict],
    settings: Settings | None = None,
) -> AnswerResult:
    import httpx

    config = settings or get_settings()
    if not config.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    payload = {
        "model": config.deepseek_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"论文片段：\n{_format_contexts(contexts)}\n\n问题：{question}",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{config.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.deepseek_api_key}"},
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    usage = data.get("usage") or {}
    return AnswerResult(
        text=data["choices"][0]["message"]["content"],
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        model=data.get("model") or config.deepseek_model,
    )
