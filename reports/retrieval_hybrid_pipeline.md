# Retrieval Evaluation: hybrid_pipeline

- Generated: 2026-10-24T04:30:52+00:00
- Corpus: 769 chunks
- Retriever: hybrid
- Query field: question
- Query rewrite: True
- Rerank: True
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.923 | 1.000 | 0.795 | 0.845 |
| method | 7 | 1.000 | 1.000 | 1.000 | 1.000 |
| multi_hop | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_paper | 3 | 0.500 | 0.722 | 0.472 | 0.474 |
| **overall** | **26** | **0.904** | **0.968** | **0.837** | **0.862** |

- Latency: P50 133.1 ms, P95 145.4 ms

## Misses (Recall@10 < 1)

- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.72), rag_survey.pdf p4 (0.72), rag_survey.pdf p16 (0.71), rag_survey.pdf p4 (0.70), rag_survey.pdf p2 (0.70)
- `q26`: Recall@10=0.67; top hits: rag_survey.pdf p1 (0.52), rag_survey.pdf p2 (0.51), autogen.pdf p19 (0.50), openmaic.pdf p15 (0.50), rag_survey.pdf p1 (0.50)
