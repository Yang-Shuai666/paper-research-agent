# Answer Evaluation Summary

- 30 questions: 26 answerable + 4 unanswerable
- Retrieval: query rewrite → weighted hybrid → cross-encoder rerank, top-6
- Judge: DeepSeek JSON mode, temperature 0; deterministic citation check

| Metric | With expansion | Without expansion |
|---|---:|---:|
| Correctness (0-2) | 1.80 | 1.60 |
| Complete answers | 0.833 | 0.700 |
| Faithfulness (0-2) | 2.00 | 2.00 |
| Citation support (0-2) | 1.93 | 1.93 |
| Refusal accuracy | 0.933 | 0.900 |
| Answerable: correctness | 1.77 | 1.54 |
| Answerable: complete | 0.808 | 0.654 |
| Unanswerable: correct refusal | 1.000 | 1.000 |
| Answerable with ≥1 valid citation | 0.962 | 0.962 |

- Invalid citation numbers: 0 answers with expansion, 0 without.
- Tokens: 50063 prompt + 11778 completion with expansion; 23889 + 13110 without.

## Findings

- Neighbor expansion (same page, ±2 chunks, max 16 contexts) raises complete answers from 0.654 to 0.808 and refusal accuracy from 0.885 to 0.923. It fixes q05: the retrieved page had the four student-agent names in adjacent chunks, but the top-6 chunks alone only contained the lead-in.
- Faithfulness stays at 2.00/2 and every citation number is valid; 25 of 26 answerable answers contain at least one citation.
- All four unanswerable questions are correctly refused; no missed refusals.
- Remaining failures are retrieval-limited: q25 and q26 are marked answerable but the global top-6 covers only one or two of the required papers, so the model refuses. The `compare_papers` agent tool will retrieve per paper.
- q06 and q13 are partial: the retrieved page range misses a few list items (query generation / Routing / Predict). This is a chunk-boundary recall issue, not a generation hallucination.

## Reproduce

```bash
python scripts/eval_answers.py --label answer_eval --top-k 6
python scripts/eval_answers.py --label answer_eval_no_expansion --top-k 6 --no-expansion
```
