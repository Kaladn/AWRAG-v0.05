# Method Notes

This folder preserves compact, repo-safe methods and results from the AW subject-generalization / miss-forensics work.

## Weighted Miss Reason Trace

Report-side trace over already identified SciFact misses. It used question text, AW rank-1 doc text, gold doc text, topK doc text where available, and computed unique anchor fields, relation hints, frame terms, value terms, drift, and choice score. It did not use an LLM, model judge, embeddings, reranker, or backend mutation.

## Native 6-1-6 TopK Position Reveal

Standalone report module revealed the existing AW topK position key without touching backend code. The current candidate position key is:

```text
direct_hit_count desc, density_score desc, score desc, block_ordinal asc
```

`score` is the native candidate total weight number. `density_score` is normalized by block size and is sorted before raw score. The report forced gold documents through the same audit score calculation without inserting them into retrieval.


## Native-Aware Formula Rework

The current method separates ranking truth from explanation:

```text
Native AW weight number = score
Native AW ranking decision = direct_hit_count desc, density_score desc, score desc, block_ordinal asc
```

The previous weighted field formula is retained only as a secondary interpretive audit. It is not native AW scoring and must not be used as the topK ranking truth.

## Data Hygiene

Raw corpora, runtime count binaries, and local absolute paths are intentionally excluded from this repo report package.
