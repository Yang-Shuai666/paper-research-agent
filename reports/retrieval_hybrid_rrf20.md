# Retrieval Evaluation: hybrid_rrf20

- Generated: 2026-10-24T04:16:07+00:00
- Corpus: 769 chunks
- Retriever: hybrid
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.769 | 0.923 | 0.675 | 0.735 |
| method | 7 | 1.000 | 1.000 | 0.886 | 0.912 |
| multi_hop | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_paper | 3 | 0.556 | 0.722 | 0.733 | 0.580 |
| **overall** | **26** | **0.833** | **0.929** | **0.776** | **0.795** |

- Latency: P50 35.8 ms, P95 38.5 ms

## Misses (Recall@10 < 1)

- `q05`: Recall@10=0.00; top hits: openmaic.pdf p9 (0.05), openmaic.pdf p4 (0.05), openmaic.pdf p4 (0.05), openmaic.pdf p5 (0.05), openmaic.pdf p4 (0.05)
- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.06), rag_survey.pdf p1 (0.06), rag_survey.pdf p4 (0.05), rag_survey.pdf p4 (0.05), rag_survey.pdf p2 (0.05)
- `q26`: Recall@10=0.67; top hits: openmaic.pdf p11 (0.05), rag_survey.pdf p1 (0.05), rag_survey.pdf p14 (0.04), rag_survey.pdf p2 (0.04), openmaic.pdf p15 (0.04)
