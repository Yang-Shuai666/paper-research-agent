import argparse
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.config import PROJECT_ROOT, get_settings
from app.eval.dataset import EvalQuestion, load_questions
from app.eval.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from app.rag.bm25_index import BM25Index, get_bm25_index
from app.rag.pipeline import RetrievalPipeline, build_retriever
from app.rag.vector_store import get_store

Retriever = RetrievalPipeline | BM25Index

GROUP_ORDER = ["factoid", "method", "multi_hop", "cross_paper"]


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


def evaluate_question(
    question: EvalQuestion,
    retriever: Retriever,
    top_k: int,
    query_field: str = "question",
) -> dict:
    query = getattr(question, query_field) or question.question
    started = time.perf_counter()
    chunks = retriever.search(query, top_k=top_k)
    latency_ms = (time.perf_counter() - started) * 1000

    return {
        "id": question.id,
        "type": question.type,
        "question": question.question,
        "query": query,
        "latency_ms": latency_ms,
        "recall@5": recall_at_k(chunks, question.evidence, 5),
        "recall@10": recall_at_k(chunks, question.evidence, 10),
        "mrr": reciprocal_rank(chunks, question.evidence),
        "ndcg@10": ndcg_at_k(chunks, question.evidence, 10),
        "top_chunks": [
            {
                "id": chunk.id,
                "file": chunk.metadata.get("file_name"),
                "page": chunk.metadata.get("page"),
                "score": round(chunk.score, 4),
            }
            for chunk in chunks[:5]
        ],
    }


def aggregate(records: list[dict]) -> dict:
    metrics = {}
    for key in ("recall@5", "recall@10", "mrr", "ndcg@10"):
        values = [record[key] for record in records if record[key] is not None]
        metrics[key] = sum(values) / len(values) if values else 0.0
    metrics["n"] = len(records)
    return metrics


def format_table(records: list[dict]) -> str:
    rows = ["| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |"]
    rows.append("|---|---:|---:|---:|---:|---:|")
    groups = defaultdict(list)
    for record in records:
        groups[record["type"]].append(record)

    for group in GROUP_ORDER + sorted(set(groups) - set(GROUP_ORDER)):
        if group not in groups:
            continue
        metrics = aggregate(groups[group])
        rows.append(
            f"| {group} | {metrics['n']} | {metrics['recall@5']:.3f} | "
            f"{metrics['recall@10']:.3f} | {metrics['mrr']:.3f} | "
            f"{metrics['ndcg@10']:.3f} |"
        )

    overall = aggregate(records)
    rows.append(
        f"| **overall** | **{overall['n']}** | **{overall['recall@5']:.3f}** | "
        f"**{overall['recall@10']:.3f}** | **{overall['mrr']:.3f}** | "
        f"**{overall['ndcg@10']:.3f}** |"
    )
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval on the QA set.")
    parser.add_argument("--retriever", choices=["dense", "bm25", "hybrid"], default="dense")
    parser.add_argument("--label", default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--query-field", choices=["question", "question_en"], default="question")
    parser.add_argument("--rewrite", action="store_true", help="Rewrite Chinese queries to English")
    parser.add_argument("--rerank", action="store_true", help="Rerank candidates with a cross-encoder")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    label = args.label or args.retriever
    questions = [question for question in load_questions(args.dataset) if question.answerable]
    if args.limit:
        questions = questions[: args.limit]

    if args.retriever == "bm25":
        retriever: Retriever = get_bm25_index()
        retriever.search("warmup", top_k=1)
    else:
        retriever = build_retriever(
            args.retriever,
            enable_rewrite=args.rewrite,
            enable_rerank=args.rerank,
        )
        retriever.search("warmup", top_k=1)

    records = [
        evaluate_question(question, retriever, args.top_k, args.query_field)
        for question in questions
    ]
    latencies = [record["latency_ms"] for record in records]
    overall = aggregate(records)

    output_path = args.output or PROJECT_ROOT / "reports" / f"retrieval_{label}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    misses = [record for record in records if record["recall@10"] < 1.0]
    lines = [
        f"# Retrieval Evaluation: {label}",
        "",
        f"- Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"- Corpus: {get_store().count()} chunks",
        f"- Retriever: {args.retriever}",
        f"- Query field: {args.query_field}",
        f"- Query rewrite: {args.rewrite}",
        f"- Rerank: {args.rerank}",
        f"- Embedding: {settings.embedding_model_path.name} ({settings.embedding_device})",
        f"- Top-k: {args.top_k}",
        f"- Questions: {len(records)} answerable",
        "",
        format_table(records),
        "",
        (
            f"- Latency: P50 {percentile(latencies, 0.5):.1f} ms, "
            f"P95 {percentile(latencies, 0.95):.1f} ms"
        ),
        "",
        "## Misses (Recall@10 < 1)",
        "",
    ]
    if not misses:
        lines.append("None.")
    for record in misses:
        lines.append(
            f"- `{record['id']}`: Recall@10={record['recall@10']:.2f}; top hits: "
            + ", ".join(
                f"{chunk['file']} p{chunk['page']} ({chunk['score']:.2f})"
                for chunk in record["top_chunks"]
            )
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    details_path = PROJECT_ROOT / "reports" / f"retrieval_{label}.json"
    details_path.write_text(
        json.dumps({"records": records, "overall": overall}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\n".join(lines[:14]))
    print(f"\nSaved {output_path} and {details_path}")


if __name__ == "__main__":
    main()
