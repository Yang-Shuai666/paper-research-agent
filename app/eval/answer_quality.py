import json
import re
from collections import defaultdict

import httpx

from app.config import Settings, get_settings
from app.eval.dataset import EvalQuestion

REFUSAL_RE = re.compile(
    r"信息不足|无法回答|无法确定|未提供|没有(?:提供|给出|提及)|不足以|insufficient|cannot answer",
    re.IGNORECASE,
)
GROUP_ORDER = ["factoid", "method", "multi_hop", "cross_paper", "unanswerable"]

JUDGE_SYSTEM = "你是严格的 RAG 答案评审。只输出 JSON，不要输出其他内容。"

JUDGE_TEMPLATE = """问题：{question}
问题是否可回答：{answerable}
参考答案：{reference}

检索片段：
{contexts}

系统答案：
{answer}

评分标准：
- correctness: 0=错误或答非所问；1=部分正确但缺少关键事实；2=与参考答案一致且完整。不可回答问题若明确说明信息不足并解释缺失信息，记 2 分。
- faithfulness: 0=包含明显片段外信息或与片段矛盾；1=大部分有依据但有少量无依据内容；2=所有事实性陈述都能在片段中找到依据。
- citation_support: 0=没有引用或引用编号无效；1=有引用但部分引用不支撑对应陈述；2=引用编号有效且支撑对应陈述。
- refusal: correct（可回答且给出实质答案，或不可回答且明确说明信息不足）、false_refusal（可回答却拒绝）、missed_refusal（不可回答却编造答案）。
- reason: 一句话中文说明。

只返回 JSON：
{{"correctness": 0, "faithfulness": 0, "citation_support": 0, "refusal": "correct", "reason": ""}}"""


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object in judge response")
    return json.loads(match.group(0))


def format_contexts(chunks) -> str:
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata
        source = " ".join(
            part
            for part in (
                metadata.get("file_name"),
                f"p{metadata.get('page')}" if metadata.get("page") else None,
                metadata.get("section"),
            )
            if part
        )
        lines.append(f"[{index}] {source}\n{chunk.text}")
    return "\n\n".join(lines)


def is_refusal(answer: str) -> bool:
    stripped = answer.strip()
    if "信息不足" in stripped:
        return True
    return bool(REFUSAL_RE.search(stripped)) and len(stripped) < 200


async def judge_answer(
    client: httpx.AsyncClient,
    question: EvalQuestion,
    answer: str,
    contexts: str,
    settings: Settings | None = None,
) -> dict:
    prompt = JUDGE_TEMPLATE.format(
        question=question.question,
        answerable="是" if question.answerable else "否",
        reference=question.reference_answer,
        contexts=contexts,
        answer=answer,
    )
    config = settings or get_settings()
    for attempt in range(2):
        response = await client.post(
            f"{config.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.deepseek_api_key}"},
            json={
                "model": config.deepseek_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        try:
            return parse_json(content)
        except (ValueError, json.JSONDecodeError):
            if attempt == 1:
                return {
                    "correctness": None,
                    "faithfulness": None,
                    "citation_support": None,
                    "refusal": "unknown",
                    "reason": f"judge parse error: {content[:120]}",
                }
    return {}


def average(records: list[dict], key: str) -> float:
    values = [
        record["judge"].get(key)
        for record in records
        if record["judge"].get(key) is not None
    ]
    return sum(values) / len(values) if values else 0.0


def refusal_accuracy(records: list[dict]) -> float:
    if not records:
        return 0.0
    correct = sum(record["judge"].get("refusal") == "correct" for record in records)
    return correct / len(records)


def format_table(records: list[dict]) -> str:
    rows = [
        "| Group | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    groups = defaultdict(list)
    for record in records:
        groups[record["type"]].append(record)

    for group in GROUP_ORDER + sorted(set(groups) - set(GROUP_ORDER)):
        if group not in groups:
            continue
        subset = groups[group]
        complete = sum(record["judge"].get("correctness") == 2 for record in subset) / len(subset)
        rows.append(
            f"| {group} | {len(subset)} | {average(subset, 'correctness'):.2f} | "
            f"{complete:.3f} | {average(subset, 'faithfulness'):.2f} | "
            f"{average(subset, 'citation_support'):.2f} | {refusal_accuracy(subset):.3f} |"
        )

    complete = sum(record["judge"].get("correctness") == 2 for record in records) / len(records)
    rows.append(
        f"| **overall** | **{len(records)}** | **{average(records, 'correctness'):.2f}** | "
        f"**{complete:.3f}** | **{average(records, 'faithfulness'):.2f}** | "
        f"**{average(records, 'citation_support'):.2f}** | **{refusal_accuracy(records):.3f}** |"
    )
    return "\n".join(rows)
