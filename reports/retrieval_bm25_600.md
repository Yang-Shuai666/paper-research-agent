# Retrieval Evaluation: bm25_600

- Generated: 2026-10-24T04:15:07+00:00
- Corpus: 769 chunks
- Retriever: bm25
- Embedding: bge-m3 (auto)
- Top-k: 10
- Questions: 26 answerable

| Group | N | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| factoid | 13 | 0.385 | 0.615 | 0.306 | 0.377 |
| method | 7 | 1.000 | 1.000 | 0.814 | 0.860 |
| multi_hop | 3 | 1.000 | 1.000 | 0.833 | 0.877 |
| cross_paper | 3 | 0.333 | 0.333 | 0.167 | 0.231 |
| **overall** | **26** | **0.615** | **0.731** | **0.488** | **0.548** |

- Latency: P50 4.3 ms, P95 6.8 ms

## Misses (Recall@10 < 1)

- `q04`: Recall@10=0.00; top hits: openmaic.pdf p5 (4.40), openmaic.pdf p5 (3.83), openmaic.pdf p4 (3.76), openmaic.pdf p14 (3.75), openmaic.pdf p5 (3.68)
- `q05`: Recall@10=0.00; top hits: openmaic.pdf p5 (4.40), openmaic.pdf p5 (3.83), openmaic.pdf p4 (3.76), openmaic.pdf p14 (3.75), openmaic.pdf p5 (3.68)
- `q15`: Recall@10=0.00; top hits: rag_survey.pdf p2 (3.49), rag_survey.pdf p1 (3.47), rag_survey.pdf p4 (3.41), rag_survey.pdf p2 (3.33), rag_survey.pdf p4 (3.32)
- `q16`: Recall@10=0.00; top hits: rag_survey.pdf p2 (3.49), rag_survey.pdf p1 (3.47), rag_survey.pdf p4 (3.41), rag_survey.pdf p2 (3.33), rag_survey.pdf p4 (3.32)
- `q21`: Recall@10=0.00; top hits: autogen.pdf p7 (10.14), autogen.pdf p6 (9.66), autogen.pdf p39 (9.55), autogen.pdf p19 (9.50), autogen.pdf p6 (8.57)
- `q24`: Recall@10=0.00; top hits: openmaic.pdf p5 (4.40), openmaic.pdf p5 (3.83), openmaic.pdf p4 (3.76), openmaic.pdf p14 (3.75), openmaic.pdf p5 (3.68)
- `q26`: Recall@10=0.00; top hits: 
