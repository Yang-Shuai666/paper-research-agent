# Retrieval Evaluation: dense_section

- Generated: 2026-10-24T04:09:02+00:00
- Corpus: 542 chunks
- Retriever: dense
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.846 | 0.923 | 0.663 | 0.726 |
| method | 7 | 1.000 | 1.000 | 0.750 | 0.813 |
| multi_hop | 3 | 1.000 | 1.000 | 0.611 | 0.710 |
| cross_paper | 3 | 0.389 | 0.556 | 0.667 | 0.519 |
| **overall** | **26** | **0.853** | **0.910** | **0.681** | **0.724** |

- Latency: P50 27.2 ms, P95 27.9 ms

## Misses (Recall@10 < 1)

- `q16`: Recall@10=0.00; top hits: rag_survey.pdf p12 (0.81), rag_survey.pdf p14 (0.81), rag_survey.pdf p12 (0.81), rag_survey.pdf p12 (0.80), rag_survey.pdf p12 (0.80)
- `q24`: Recall@10=0.00; top hits: openmaic.pdf p8 (0.78), openmaic.pdf p5 (0.78), openmaic.pdf p7 (0.77), openmaic.pdf p6 (0.77), openmaic.pdf p4 (0.76)
- `q26`: Recall@10=0.67; top hits: openmaic.pdf p11 (0.74), rag_survey.pdf p14 (0.73), openmaic.pdf p5 (0.72), rag_survey.pdf p2 (0.72), rag_survey.pdf p14 (0.71)
