# Retrieval Evaluation: hybrid_rrf20_en_rerank

- Generated: 2026-10-24T04:26:42+00:00
- Corpus: 769 chunks
- Retriever: hybrid
- Query field: question_en
- Query rewrite: False
- Rerank: True
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.923 | 0.923 | 0.833 | 0.856 |
| method | 7 | 0.857 | 1.000 | 0.778 | 0.829 |
| multi_hop | 3 | 0.667 | 0.667 | 0.667 | 0.667 |
| cross_paper | 3 | 0.333 | 0.611 | 0.708 | 0.517 |
| **overall** | **26** | **0.808** | **0.878** | **0.785** | **0.788** |

- Latency: P50 173.7 ms, P95 186.1 ms

## Misses (Recall@10 < 1)

- `q16`: Recall@10=0.00; top hits: rag_survey.pdf p14 (0.73), rag_survey.pdf p14 (0.73), rag_survey.pdf p2 (0.73), rag_survey.pdf p2 (0.72), rag_survey.pdf p12 (0.71)
- `q23`: Recall@10=0.00; top hits: autogen.pdf p6 (0.60), autogen.pdf p7 (0.56), autogen.pdf p6 (0.56), autogen.pdf p6 (0.56), autogen.pdf p2 (0.55)
- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.72), rag_survey.pdf p4 (0.72), rag_survey.pdf p16 (0.72), rag_survey.pdf p4 (0.71), rag_survey.pdf p2 (0.70)
- `q26`: Recall@10=0.33; top hits: rag_survey.pdf p2 (0.52), rag_survey.pdf p1 (0.50), autogen.pdf p6 (0.50), rag_survey.pdf p1 (0.50), rag_survey.pdf p1 (0.50)
