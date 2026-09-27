from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    api_key: str | None = None
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DEEPSEEK_",
        extra="ignore",
    )


async def generate_answer(
    question: str,
    contexts: list[dict],
    settings: LLMSettings | None = None,
) -> str:
    import httpx

    config = settings or LLMSettings()
    if not config.api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    context_text = "\n\n".join(
        f"[{index + 1}] {item['metadata']}\n{item['document']}"
        for index, item in enumerate(contexts)
    )
    payload = {
        "model": config.model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是论文研究助手。只能依据提供的论文片段回答问题。"
                    "如果片段不足以回答，请明确说明信息不足。"
                    "引用请使用 [数字] 格式。"
                ),
            },
            {
                "role": "user",
                "content": f"论文片段：\n{context_text}\n\n问题：{question}",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{config.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
        )
        response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
