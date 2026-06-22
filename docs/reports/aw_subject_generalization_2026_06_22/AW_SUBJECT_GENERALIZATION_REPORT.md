# AW Subject Generalization and Native TopK Trace Report

Compact repo-safe report package. Raw corpora, local absolute paths, and bulky generated artifacts are intentionally excluded.

## Guardrails

- No raw corpus copied into repo.
- No local absolute machine paths included.
- No LLM judge, embeddings, reranker, or model authority used.
- Qrels used only for external benchmark gold reference on already identified misses.
- Native topK reveal reports current AW topK position key, not a new scoring formula.

## Aggregate SciFact Miss Forensics

- Misses evaluated: 82
- unclear / needs human review: 31
- Benchmark Miss / AW Semantic-Evidence Better Match: 26
- AW better subject match than gold: 21
- AW near miss: 4
- Combined AW-better style cases: 47 / 82 = 57.3%

## Manual Five-Case Ledger

- confirmed AW better evidence match: 1
- near miss only: 2
- term-overlap false positive: 2

## Weighted Miss Reason Trace

- Cases processed: 10
- Classification counts: `{'no support evidence found': 3, 'AW weighted choice justified': 6, 'unclear / human review': 1}`
- Best K/order pattern: `{'K3/O1': 3, 'K1/O1': 4, 'K10/O1': 2, 'K5/O1': 1}`
- AW > gold: 10
- Gold > AW: 0
- Score kind: report_side_weights

## Native 6-1-6 TopK Position Reveal

The current AW topK position key is:

```text
direct_hit_count desc, density_score desc, score desc, block_ordinal asc
```

`score` is the native candidate total weight number. TopK position is determined by the full key above.

- Cases processed: 10
- Native topK position numbers exposed: True
- Gold forced 6-1-6 score available: True
- Classification counts: `{'AW rank-1 outranks gold by native topK position key': 10}`
- Production mutation detected: False
- Git status changed during run: False

## Native Reveal Cases

| QID | AW Doc | AW Direct | AW Density | AW Score | Gold Rank | Gold Direct | Gold Density | Gold Score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 870 | 11414664 | 3 | 1.379810097558122 | 13.017102426184504 | 1428 | 0 | 0.023675635857724607 | 0.4782244025279039 |
| 623 | 25599283 | 9 | 1.787779631303737 | 26.757035453566484 | 229 | 3 | 1.0911880564130296 | 14.435061154363979 |
| 1199 | 7454794 | 9 | 3.2283969737558147 | 38.06223897515282 | 1667 | 2 | 0.19634062183474302 | 3.440165608399288 |
| 1280 | 29214508 | 7 | 6.617265189479794 | 95.89328289019633 | 673 | 1 | 0.7773417841369994 | 10.965755314783081 |
| 783 | 8246922 | 7 | 3.3105551555447046 | 46.229386870163076 | 351 | 2 | 0.5798462089109786 | 7.288553828172817 |
| 508 | 25516011 | 5 | 3.574917271697241 | 25.779095057292462 | 55 | 3 | 0.7809438012367963 | 9.140712840613375 |
| 560 | 28015516 | 9 | 1.256130779278532 | 16.474000727205077 | 390 | 5 | 0.5621358451359353 | 7.499827604207393 |
| 1281 | 29214508 | 3 | 2.228312659306519 | 32.291318254314035 | 3964 | 0 | 0.01364178427020811 | 0.19244104899138487 |
| 830 | 52873726 | 10 | 2.6517063790847817 | 35.57637432002039 | 642 | 4 | 1.231589724039946 | 14.779076688479352 |
| 1110 | 756887 | 4 | 2.514508535963073 | 34.84205232282941 | 2705 | 1 | 0.08291567414938497 | 1.9847871846265341 |
