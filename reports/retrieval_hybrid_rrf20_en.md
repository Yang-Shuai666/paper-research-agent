# Retrieval Evaluation: hybrid_rrf20_en

- Generated: 2026-10-24T04:23:54+00:00
- Corpus: 769 chunks
- Retriever: hybrid
- Query field: question_en
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.846 | 0.923 | 0.707 | 0.759 |
| method | 7 | 1.000 | 1.000 | 0.810 | 0.857 |
| multi_hop | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_paper | 3 | 0.722 | 0.722 | 0.611 | 0.545 |
| **overall** | **26** | **0.891** | **0.929** | **0.757** | **0.788** |

- Latency: P50 31.9 ms, P95 34.3 ms

## Misses (Recall@10 < 1)

- `q11`: Recall@10=0.00; top hits: rag_survey.pdf p4 (0.06), rag_survey.pdf p2 (0.06), rag_survey.pdf p1 (0.05), rag_survey.pdf p16 (0.05), rag_survey.pdf p2 (0.05)
- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.06), rag_survey.pdf p4 (0.06), rag_survey.pdf p4 (0.05), rag_survey.pdf p2 (0.05), rag_survey.pdf p1 (0.05)
- `q26`: Recall@10=0.67; top hits: rag_survey.pdf p1 (0.06), openmaic.pdf p11 (0.05), rag_survey.pdf p1 (0.05), rag_survey.pdf p1 (0.04), rag_survey.pdf p14 (0.04)
