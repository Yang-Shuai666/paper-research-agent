# Retrieval Evaluation: hybrid

- Generated: 2026-10-24T04:09:29+00:00
- Corpus: 542 chunks
- Retriever: hybrid
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.769 | 0.769 | 0.519 | 0.581 |
| method | 7 | 1.000 | 1.000 | 0.905 | 0.929 |
| multi_hop | 3 | 1.000 | 1.000 | 0.833 | 0.877 |
| cross_paper | 3 | 0.389 | 0.722 | 0.556 | 0.521 |
| **overall** | **26** | **0.814** | **0.853** | **0.663** | **0.702** |

- Latency: P50 33.5 ms, P95 36.7 ms

## Misses (Recall@10 < 1)

- `q05`: Recall@10=0.00; top hits: openmaic.pdf p5 (0.03), openmaic.pdf p9 (0.03), openmaic.pdf p4 (0.03), openmaic.pdf p8 (0.03), openmaic.pdf p6 (0.03)
- `q15`: Recall@10=0.00; top hits: rag_survey.pdf p12 (0.03), rag_survey.pdf p2 (0.03), rag_survey.pdf p1 (0.03), rag_survey.pdf p2 (0.03), rag_survey.pdf p2 (0.03)
- `q16`: Recall@10=0.00; top hits: rag_survey.pdf p12 (0.03), rag_survey.pdf p2 (0.03), rag_survey.pdf p2 (0.03), rag_survey.pdf p17 (0.03), rag_survey.pdf p2 (0.03)
- `q24`: Recall@10=0.50; top hits: openmaic.pdf p5 (0.03), openmaic.pdf p6 (0.03), openmaic.pdf p8 (0.03), openmaic.pdf p11 (0.03), openmaic.pdf p12 (0.03)
- `q26`: Recall@10=0.67; top hits: openmaic.pdf p11 (0.02), rag_survey.pdf p14 (0.02), openmaic.pdf p5 (0.02), rag_survey.pdf p2 (0.02), rag_survey.pdf p14 (0.02)
