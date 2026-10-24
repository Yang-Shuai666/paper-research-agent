import argparse
import asyncio
import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import PROJECT_ROOT, get_settings
from app.eval.answer_quality import (
    average,
    format_contexts,
    format_table,
    is_refusal,
    judge_answer,
    percentile,
    refusal_accuracy,
)
from app.eval.dataset import EvalQuestion, load_questions
from app.rag.agent import run_agent
from app.rag.agent_tools import AgentTools
from app.rag.citations import extract_citations
from app.rag.context import get_expander
from app.rag.llm import generate_answer
from app.rag.pipeline import build_retriever
from app.rag.vector_store import get_store

DEFAULT_IDS = ["q05", "q06", "q13", "q17", "q23", "q24", "q25", "q26", "q27", "q30"]


def question_type(question: EvalQuestion) -> str:
    return "unanswerable" if not question.answerable else question.type


async def run_single_shot(
    client: httpx.AsyncClient,
    question: EvalQuestion,
    retriever,
    expander,
    top_k: int,
    settings,
) -> dict:
    started = time.perf_counter()
    chunks = retriever.search(question.question, top_k=top_k)
    if expander:
        chunks = expander.expand(chunks)
    retrieval_ms = (time.perf_counter() - started) * 1000

    generation_started = time.perf_counter()
    result = await generate_answer(
        question.question,
        [{"document": chunk.text, "metadata": chunk.metadata} for chunk in chunks],
    )
    generation_ms = (time.perf_counter() - generation_started) * 1000
    valid, invalid = extract_citations(result.text, len(chunks))
    judge = await judge_answer(
        client,
        question,
        result.text,
        format_contexts(chunks),
        settings,
    )

    return {
        "id": question.id,
        "type": question_type(question),
        "question": question.question,
        "answer": result.text,
        "sources": [
            {
                "file": chunk.metadata.get("file_name"),
                "page": chunk.metadata.get("page"),
                "section": chunk.metadata.get("section"),
            }
            for chunk in chunks
        ],
        "context_count": len(chunks),
        "valid_citations": valid,
        "invalid_citations": invalid,
        "refusal_detected": is_refusal(result.text),
        "steps": [],
        "stop_reason": "answer",
        "latency_ms": retrieval_ms + generation_ms,
        "latency_retrieval_ms": retrieval_ms,
        "latency_generation_ms": generation_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "judge": judge,
    }


async def run_agent_mode(
    client: httpx.AsyncClient,
    question: EvalQuestion,
    retriever,
    settings,
    max_steps: int,
) -> dict:
    tools = AgentTools(pipeline=retriever, store=get_store(), settings=settings)
    result = await run_agent(
        question.question,
        tools=tools,
        settings=settings,
        max_steps=max_steps,
        client=client,
    )
    contexts = tools.evidence.chunks
    judge = await judge_answer(
        client,
        question,
        result.text,
        format_contexts(contexts),
        settings,
    )

    return {
        "id": question.id,
        "type": question_type(question),
        "question": question.question,
        "answer": result.text,
        "sources": result.sources,
        "context_count": len(contexts),
        "valid_citations": result.citations["valid"],
        "invalid_citations": result.citations["invalid"],
        "refusal_detected": is_refusal(result.text),
        "steps": result.steps,
        "stop_reason": result.stop_reason,
        "latency_ms": result.elapsed_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "judge": judge,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_row(name: str, records: list[dict]) -> str:
    n = len(records)
    complete = sum(record["judge"].get("correctness") == 2 for record in records) / n
    steps = mean([len(record["steps"]) for record in records])
    latency = mean([record["latency_ms"] for record in records])
    return (
        f"| {name} | {n} | {average(records, 'correctness'):.2f} | "
        f"{complete:.3f} | {average(records, 'faithfulness'):.2f} | "
        f"{average(records, 'citation_support'):.2f} | "
        f"{refusal_accuracy(records):.3f} | {steps:.1f} | {latency:.0f} | "
        f"{sum(record['prompt_tokens'] for record in records)} | "
        f"{sum(record['completion_tokens'] for record in records)} |"
    )


def citation_text(record: dict) -> str:
    return f"{len(record['valid_citations'])}/{len(record['invalid_citations'])}"


def steps_text(record: dict) -> str:
    if not record["steps"]:
        return "-"
    return " → ".join(str(step["tool"]) for step in record["steps"])


def correctness(record: dict) -> int | None:
    return record["judge"].get("correctness")


def excerpt(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact[:limit] + ("..." if len(compact) > limit else "")


def render_pair(pair: dict, limit: int = 360) -> str:
    single = pair["single"]
    agent = pair["agent"]
    return (
        f"### {pair['id']} ({pair['type']})\n"
        f"- Question: {pair['question']}\n"
        f"- Single-shot: correctness={correctness(single)}, "
        f"citations={citation_text(single)}, refusal={single['judge'].get('refusal')}\n"
        f"  - {excerpt(single['answer'], limit)}\n"
        f"- Agent: correctness={correctness(agent)}, citations={citation_text(agent)}, "
        f"steps={steps_text(agent)}, stop={agent['stop_reason']}\n"
        f"  - {excerpt(agent['answer'], limit)}\n"
        f"- Judge reason: {agent['judge'].get('reason')}"
    )


def build_report(pairs: list[dict], label: str, meta: dict) -> str:
    single_records = [pair["single"] for pair in pairs]
    agent_records = [pair["agent"] for pair in pairs]

    wins = [
        pair
        for pair in pairs
        if (correctness(pair["agent"]) or 0) > (correctness(pair["single"]) or 0)
    ]
    regressions = [
        pair
        for pair in pairs
        if (correctness(pair["agent"]) or 0) < (correctness(pair["single"]) or 0)
    ]
    win_ids = {pair["id"] for pair in wins}
    remaining = [
        pair
        for pair in pairs
        if pair["id"] not in win_ids
        and (
            correctness(pair["agent"]) not in (None, 2)
            or pair["agent"]["invalid_citations"]
        )
    ]
    cross_paper = [pair for pair in pairs if pair["type"] == "cross_paper"]
    tool_usage = Counter(
        step["tool"] for record in agent_records for step in record["steps"]
    )

    lines = [
        f"# Single-shot RAG vs Agent: {label}",
        "",
        f"- Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"- Model: `{meta['model']}`",
        f"- Questions: {len(pairs)} ({', '.join(pair['id'] for pair in pairs)})",
        (
            f"- Single-shot: hybrid + query rewrite + rerank + "
            f"{'no ' if not meta['expansion'] else ''}neighbor expansion, "
            f"top-{meta['top_k']}"
        ),
        f"- Agent: 4 tools, max {meta['max_steps']} tool calls, evidence refs [n]",
        "",
        "## Aggregate",
        "",
        "| Mode | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy | Avg steps | Avg latency (ms) | Prompt tokens | Completion tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        aggregate_row("single-shot", single_records),
        aggregate_row("agent", agent_records),
        "",
        "### Single-shot by question type",
        "",
        format_table(single_records),
        "",
        "### Agent by question type",
        "",
        format_table(agent_records),
        "",
        "## Per-question results",
        "",
        "| ID | Type | Single correctness | Agent correctness | Δ | Single citations (valid/invalid) | Agent citations (valid/invalid) | Agent steps | Agent stop |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for pair in pairs:
        single_score = correctness(pair["single"])
        agent_score = correctness(pair["agent"])
        delta = (
            (agent_score or 0) - (single_score or 0)
            if single_score is not None and agent_score is not None
            else None
        )
        delta_text = f"{delta:+d}" if delta is not None else "?"
        lines.append(
            f"| {pair['id']} | {pair['type']} | {single_score} | {agent_score} | "
            f"{delta_text} | {citation_text(pair['single'])} | "
            f"{citation_text(pair['agent'])} | {steps_text(pair['agent'])} | "
            f"{pair['agent']['stop_reason']} |"
        )

    lines.extend(["", "## Where the Agent helped", ""])
    if wins:
        for pair in wins:
            lines.append(render_pair(pair))
            lines.append("")
    else:
        lines.append("No correctness wins.")

    lines.extend(["", "## Regressions and remaining failures", ""])
    if regressions:
        for pair in regressions:
            lines.append(render_pair(pair))
            lines.append("")
    elif remaining:
        for pair in remaining:
            lines.append(render_pair(pair))
            lines.append("")
    else:
        lines.append("None.")

    lines.extend(["", "## Cross-paper cases", ""])
    if cross_paper:
        for pair in cross_paper:
            lines.append(render_pair(pair, limit=500))
            lines.append("")
    else:
        lines.append("No cross-paper questions in this run.")

    lines.extend(
        [
            "## Tool usage",
            "",
            "| Tool | Calls |",
            "|---|---:|",
        ]
    )
    for tool, count in sorted(tool_usage.items()):
        lines.append(f"| {tool} | {count} |")
    if not tool_usage:
        lines.append("| - | 0 |")

    latency_single = [record["latency_ms"] for record in single_records]
    latency_agent = [record["latency_ms"] for record in agent_records]
    lines.extend(
        [
            "",
            "## Latency",
            "",
            (
                f"- Single-shot: P50 {percentile(latency_single, 0.5):.0f} ms, "
                f"P95 {percentile(latency_single, 0.95):.0f} ms"
            ),
            (
                f"- Agent: P50 {percentile(latency_agent, 0.5):.0f} ms, "
                f"P95 {percentile(latency_agent, 0.95):.0f} ms"
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare single-shot RAG with the tool-using agent."
    )
    parser.add_argument("--label", default="agent_comparison")
    parser.add_argument("--ids", default=",".join(DEFAULT_IDS))
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--no-expansion", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--from-json",
        type=Path,
        default=None,
        help="Regenerate the report from an existing result JSON without LLM calls",
    )
    args = parser.parse_args()

    settings = get_settings()

    if args.from_json:
        payload = json.loads(args.from_json.read_text(encoding="utf-8"))
        pairs = payload["pairs"]
        meta = payload.get("meta") or {
            "model": settings.deepseek_model,
            "top_k": args.top_k,
            "max_steps": args.max_steps,
            "expansion": not args.no_expansion,
        }
    else:
        if not settings.deepseek_api_key:
            raise SystemExit("DEEPSEEK_API_KEY is required for agent evaluation")

        selected = {item.strip() for item in args.ids.split(",") if item.strip()}
        questions = [
            question for question in load_questions(args.dataset) if question.id in selected
        ]
        if args.limit:
            questions = questions[: args.limit]
        if not questions:
            raise SystemExit("No questions matched --ids")

        retriever = build_retriever("hybrid", enable_rewrite=True, enable_rerank=True)
        retriever.search("warmup", top_k=1)
        expander = None if args.no_expansion else get_expander()

        async def run() -> list[dict]:
            result = []
            async with httpx.AsyncClient(timeout=240) as client:
                for index, question in enumerate(questions, start=1):
                    print(f"[{index}/{len(questions)}] {question.id} single-shot")
                    single = await run_single_shot(
                        client, question, retriever, expander, args.top_k, settings
                    )
                    print(f"[{index}/{len(questions)}] {question.id} agent")
                    agent = await run_agent_mode(
                        client, question, retriever, settings, args.max_steps
                    )
                    result.append(
                        {
                            "id": question.id,
                            "type": question_type(question),
                            "question": question.question,
                            "single": single,
                            "agent": agent,
                        }
                    )
            return result

        pairs = asyncio.run(run())
        meta = {
            "model": settings.deepseek_model,
            "top_k": args.top_k,
            "max_steps": args.max_steps,
            "expansion": not args.no_expansion,
        }

    report = build_report(pairs, args.label, meta)
    output_path = args.output or PROJECT_ROOT / "reports" / f"{args.label}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    details_path = PROJECT_ROOT / "reports" / f"{args.label}.json"
    details_path.write_text(
        json.dumps({"meta": meta, "pairs": pairs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\n".join(report.splitlines()[:24]))
    print(f"\nSaved {output_path} and {details_path}")


if __name__ == "__main__":
    main()
