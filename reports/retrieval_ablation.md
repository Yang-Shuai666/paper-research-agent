# Retrieval Ablation

- 3 PDFs, 26 answerable questions (13 factoid, 7 method, 3 multi-hop, 3 cross-paper)
- Top-k 10; page-level evidence recall; embedding `bge-m3`
- Query rewrite: DeepSeek translates Chinese questions to English for retrieval; the reranker sees the original Chinese question
- Rerank: `BAAI/bge-reranker-v2-m3`, top-12 candidates

| Run | Chunks | Retriever | Query | Rewrite | Rerank | Recall@5 | Recall@10 | MRR | nDCG@10 | P50 ms |
|---|---:|---|---|:---:|:---:|---:|---:|---:|---:|---:|
| Baseline: fixed 500-char chunks | 546 | Dense | zh | - | - | 0.865 | 0.917 | 0.701 | 0.744 | 28.0 |
| Section-aware 800-char | 542 | Dense | zh | - | - | 0.853 | 0.910 | 0.681 | 0.724 | 27.3 |
| Section-aware 600-char | 769 | Dense | zh | - | - | 0.795 | 0.929 | 0.794 | 0.809 | 30.1 |
| BM25 only | 769 | BM25 | zh | - | - | 0.615 | 0.731 | 0.488 | 0.548 | 4.3 |
| Naive RRF (k=60, 1:1) | 542 | Hybrid | zh | - | - | 0.814 | 0.853 | 0.663 | 0.702 | 33.5 |
| Weighted RRF (k=20, 1:0.25) | 769 | Hybrid | zh | - | - | 0.833 | 0.929 | 0.776 | 0.795 | 35.9 |
| Dense + query rewrite | 769 | Dense | en | ✓ | - | 0.891 | 0.968 | 0.751 | 0.792 | 27.5 |
| Hybrid + query rewrite | 769 | Hybrid | en | ✓ | - | 0.891 | 0.929 | 0.757 | 0.788 | 31.9 |
| Dense pipeline: rewrite + rerank | 769 | Dense | zh | ✓ | ✓ | 0.865 | 0.929 | 0.793 | 0.819 | 128.9 |
| Hybrid pipeline: rewrite + rerank | 769 | Hybrid | zh | ✓ | ✓ | 0.904 | 0.968 | 0.837 | 0.862 | 133.4 |

## What changed

- **Section-aware 600-char chunks** beat fixed 500-char chunks on ranking (MRR 0.701 → 0.794, nDCG@10 0.744 → 0.809) while keeping Recall@10 comparable (0.917 → 0.929). The lower Recall@5 comes from several chunks of the same page occupying top slots.
- **Equal-weight RRF was a regression**: Chinese queries over English papers give BM25 mostly low-information tokens such as "RAG". Weighting dense 1 : sparse 0.25 and lowering `rrf_k` to 20 recovered Recall@5 (0.795 → 0.833).
- **Cross-lingual query rewriting** was the largest single win: Recall@10 0.929 → 0.968 and Recall@5 0.795 → 0.891 for dense retrieval.
- **Reranking with the original Chinese query** added MRR 0.751 → 0.837 and nDCG@10 0.792 → 0.862. Reranking with the translated keyword query was worse; the multilingual cross-encoder benefits from the natural-language question.
- **Final pipeline** (rewrite → weighted hybrid → cross-encoder rerank): Recall@5 0.904, Recall@10 0.968, MRR 0.837, nDCG@10 0.862, versus the original baseline 0.865 / 0.917 / 0.701 / 0.744.

## Latency

- Hybrid + cached rewrite + rerank: P50 133 ms, P95 145 ms (26 questions).
- First query rewrite call: ~1.6 s; cached rewrite: <1 ms. The cache is stored in `data/cache/query_rewrites.json`.

## Remaining weakness

- Cross-paper questions: Recall@5 0.500, Recall@10 0.722, MRR 0.472. A global top-10 usually covers only one paper; the planned `compare_papers` agent tool will allocate retrieval slots per paper.
- The 26-question set is small. Candidate counts and weights were tuned on it, so treat the absolute numbers as directional and the ablation as the main evidence.

## Reproduce

```bash
python scripts/reset_index.py
python scripts/ingest_all.py
python scripts/eval_retrieval.py --retriever dense --label dense_section_600
python scripts/eval_retrieval.py --retriever hybrid --label hybrid_rrf20
python scripts/eval_retrieval.py --retriever hybrid --label hybrid_pipeline --rewrite --rerank
```
