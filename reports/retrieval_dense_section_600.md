# Retrieval Evaluation: dense_section_600

- Generated: 2026-10-24T04:14:55+00:00
- Corpus: 769 chunks
- Retriever: dense
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.769 | 0.923 | 0.713 | 0.762 |
| method | 7 | 0.857 | 1.000 | 0.881 | 0.908 |
| multi_hop | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_paper | 3 | 0.556 | 0.722 | 0.733 | 0.591 |
| **overall** | **26** | **0.795** | **0.929** | **0.794** | **0.809** |

- Latency: P50 30.1 ms, P95 31.0 ms

## Misses (Recall@10 < 1)

- `q08`: Recall@10=0.00; top hits: openmaic.pdf p17 (0.80), openmaic.pdf p4 (0.80), openmaic.pdf p13 (0.80), openmaic.pdf p10 (0.80), openmaic.pdf p4 (0.79)
- `q25`: Recall@10=0.50; top hits: rag_survey.pdf p4 (0.81), rag_survey.pdf p1 (0.81), rag_survey.pdf p4 (0.81), rag_survey.pdf p4 (0.80), rag_survey.pdf p16 (0.79)
- `q26`: Recall@10=0.67; top hits: openmaic.pdf p11 (0.74), rag_survey.pdf p1 (0.74), rag_survey.pdf p14 (0.73), rag_survey.pdf p2 (0.73), openmaic.pdf p15 (0.73)
