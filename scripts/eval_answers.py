import argparse
import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import PROJECT_ROOT, get_settings
from app.eval.answer_quality import (
    format_contexts,
    format_table,
    is_refusal,
    judge_answer,
    percentile,
)
from app.eval.dataset import EvalQuestion, load_questions
from app.rag.citations import extract_citations
from app.rag.context import get_expander
from app.rag.llm import generate_answer
from app.rag.pipeline import build_retriever


async def evaluate_question(
    client: httpx.AsyncClient,
    question: EvalQuestion,
    retriever,
    expander,
    top_k: int,
) -> dict:
    started = time.perf_counter()
    chunks = retriever.search(question.question, top_k=top_k)
    if expander:
        chunks = expander.expand(chunks)
    retrieval_ms = (time.perf_counter() - started) * 1000

    contexts = format_contexts(chunks)
    generation_started = time.perf_counter()
    result = await generate_answer(
        question.question,
        [{"document": chunk.text, "metadata": chunk.metadata} for chunk in chunks],
    )
    generation_ms = (time.perf_counter() - generation_started) * 1000

    valid, invalid = extract_citations(result.text, len(chunks))
    judge = await judge_answer(client, question, result.text, contexts)
    refusal_detected = is_refusal(result.text)

    return {
        "id": question.id,
        "type": "unanswerable" if not question.answerable else question.type,
        "question": question.question,
        "answerable": question.answerable,
        "answer": result.text,
        "reference_answer": question.reference_answer,
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
        "refusal_detected": refusal_detected,
        "judge": judge,
        "latency_retrieval_ms": retrieval_ms,
        "latency_generation_ms": generation_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate end-to-end answer quality.")
    parser.add_argument("--label", default="answer_eval")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-expansion", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    settings = get_settings()
    if not settings.deepseek_api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required for answer evaluation")

    questions = load_questions(args.dataset)
    if args.limit:
        questions = questions[: args.limit]

    retriever = build_retriever("hybrid", enable_rewrite=True, enable_rerank=True)
    retriever.search("warmup", top_k=1)
    expander = None if args.no_expansion else get_expander()

    async def run() -> list[dict]:
        records = []
        async with httpx.AsyncClient(timeout=180) as client:
            for index, question in enumerate(questions, start=1):
                print(f"[{index}/{len(questions)}] {question.id}")
                records.append(
                    await evaluate_question(
                        client, question, retriever, expander, args.top_k
                    )
                )
        return records

    records = asyncio.run(run())

    output_path = args.output or PROJECT_ROOT / "reports" / f"{args.label}.md"
    references = [record for record in records if record["answerable"]]
    unanswerable = [record for record in records if not record["answerable"]]
    retrieval_latencies = [record["latency_retrieval_ms"] for record in records]
    generation_latencies = [record["latency_generation_ms"] for record in records]
    prompt_tokens = sum(record["prompt_tokens"] for record in records)
    completion_tokens = sum(record["completion_tokens"] for record in records)

    bad_cases = [
        record
        for record in records
        if record["judge"].get("correctness") not in (None, 2)
        or record["invalid_citations"]
        or record["judge"].get("refusal") in {"false_refusal", "missed_refusal"}
    ]

    lines = [
        f"# Answer Evaluation: {args.label}",
        "",
        f"- Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"- Questions: {len(records)} ({len(references)} answerable, {len(unanswerable)} unanswerable)",
        f"- Retrieval: hybrid + query rewrite + rerank, top-{args.top_k}",
        f"- Context expansion: {not args.no_expansion}",
        "",
        format_table(records),
        "",
        (
            f"- Latency: retrieval P50 {percentile(retrieval_latencies, 0.5):.0f} ms, "
            f"P95 {percentile(retrieval_latencies, 0.95):.0f} ms; "
            f"generation P50 {percentile(generation_latencies, 0.5):.0f} ms, "
            f"P95 {percentile(generation_latencies, 0.95):.0f} ms"
        ),
        f"- Tokens: {prompt_tokens} prompt, {completion_tokens} completion",
        "",
        "## Bad cases",
        "",
    ]
    if not bad_cases:
        lines.append("None.")
    for record in bad_cases:
        judge = record["judge"]
        lines.append(
            f"### {record['id']} ({record['type']})\n"
            f"- Question: {record['question']}\n"
            f"- Judge: correctness={judge.get('correctness')}, "
            f"faithfulness={judge.get('faithfulness')}, "
            f"citation_support={judge.get('citation_support')}, "
            f"refusal={judge.get('refusal')}\n"
            f"- Reason: {judge.get('reason')}\n"
            f"- Invalid citations: {record['invalid_citations']}\n"
            f"- Answer: {record['answer'][:300]}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    details_path = PROJECT_ROOT / "reports" / f"{args.label}.json"
    details_path.write_text(
        json.dumps({"records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\n".join(lines[:16]))
    print(f"\nSaved {output_path} and {details_path}")


if __name__ == "__main__":
    main()
