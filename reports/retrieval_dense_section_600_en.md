# Retrieval Evaluation: dense_section_600_en

- Generated: 2026-10-24T04:23:35+00:00
- Corpus: 769 chunks
- Retriever: dense
- Query field: question_en
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.846 | 1.000 | 0.681 | 0.757 |
| method | 7 | 1.000 | 1.000 | 0.810 | 0.857 |
| multi_hop | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_paper | 3 | 0.722 | 0.722 | 0.667 | 0.587 |
| **overall** | **26** | **0.891** | **0.968** | **0.751** | **0.792** |

- Latency: P50 27.5 ms, P95 28.8 ms

## Misses (Recall@10 < 1)

- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.82), rag_survey.pdf p4 (0.81), rag_survey.pdf p4 (0.81), rag_survey.pdf p1 (0.81), rag_survey.pdf p2 (0.80)
- `q26`: Recall@10=0.67; top hits: rag_survey.pdf p1 (0.75), openmaic.pdf p11 (0.75), rag_survey.pdf p1 (0.74), rag_survey.pdf p14 (0.74), rag_survey.pdf p1 (0.73)
