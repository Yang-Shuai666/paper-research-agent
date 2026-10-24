# Retrieval Evaluation: dense_baseline

- Generated: 2026-10-24T04:00:18+00:00
- Corpus: 546 chunks
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.846 | 0.923 | 0.706 | 0.758 |
| method | 7 | 1.000 | 1.000 | 0.833 | 0.876 |
| multi_hop | 3 | 1.000 | 1.000 | 0.528 | 0.644 |
| cross_paper | 3 | 0.500 | 0.611 | 0.548 | 0.473 |
| **overall** | **26** | **0.865** | **0.917** | **0.701** | **0.744** |

- Latency: P50 28.0 ms, P95 28.7 ms

## Misses (Recall@10 < 1)

- `q16`: Recall@10=0.00; top hits: rag_survey.pdf p12 (0.81), rag_survey.pdf p14 (0.80), rag_survey.pdf p12 (0.79), rag_survey.pdf p12 (0.79), rag_survey.pdf p14 (0.79)
- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p14 (0.80), rag_survey.pdf p4 (0.80), rag_survey.pdf p4 (0.79), rag_survey.pdf p2 (0.79), rag_survey.pdf p3 (0.77)
- `q26`: Recall@10=0.33; top hits: openmaic.pdf p15 (0.70), rag_survey.pdf p1 (0.70), rag_survey.pdf p1 (0.70), openmaic.pdf p4 (0.70), rag_survey.pdf p4 (0.70)
