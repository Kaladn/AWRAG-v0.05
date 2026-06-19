# SciFact Strength-Ranking Log - 2026-06-19

This log records the valid SciFact methodology and scoreboard from the 2026-06-19 AWRAG work session.

It is a report/changelog only. No benchmark data, generated outputs, datasets, count files, or local runtime artifacts are committed here.

## Core Finding

SciFact benchmark scoring asks:

```text
Did the system retrieve the labeled benchmark gold document?
```

AWRAG evidence work also asks:

```text
What are the strongest supported evidence candidates in the corpus?
```

Those are related, but they are not the same test.

The session showed that benchmark expected documents cannot automatically be treated as the strongest available evidence according to the corpus. A labeled gold document may be valid while another document contains parallel, cleaner, broader, or more direct evidence for the same claim.

The correct claim is not "the benchmark is wrong." The correct claim is:

```text
Some benchmark misses are evidence disagreements and deserve review.
```

## Valid Current SciFact Scoreboard

### Prior Valid Baseline

Original full SciFact retrieval-stage run:

```text
Rows: 300
Hit@10: 209 / 300 = 69.67%
```

This was retrieval-only accounting, not final answer correctness.

### Current Valid Improved Run

Laptop strength-ranked AWRAG run:

```text
Rows: 300
Hit@1:  150 / 300 = 50.00%
Hit@3:  195 / 300 = 65.00%
Hit@5:  208 / 300 = 69.33%
Hit@10: 217 / 300 = 72.33%
```

Method:

```text
Native AWRAG candidate path
Raw native count candidates
Candidate depth: 250
Distinct documents
Evidence-strength rerank
Top 10 retained
No qrels used for selection
No engine modifications
```

Important ordering observation:

```text
Strength-ranked Hit@5: 208 / 300 = 69.33%
Prior baseline Hit@10: 209 / 300 = 69.67%
```

This suggests the strength rerank improved ordering quality. New top 5 nearly matched the old top 10.

## Invalid / Excluded Comparison

A quick local Top-5 run reported:

```text
Rows: 300
Hit@5: 184 / 300 = 61.33%
```

That run is excluded from AWRAG benchmark comparison.

Reason:

```text
It did not run the real native AWRAG candidate path.
It used a quick report-only retriever over local SciFact text.
It was BM25-ish / term-weight-ish, not raw native count candidates at depth 250.
It did not reproduce the laptop strength-ranked method.
```

It may still be useful as an audit prototype, but it is not a valid AWRAG score.

## Evidence Disagreement Audit

The strength-ranked Top10 run left:

```text
Top10 misses: 83
```

For those remaining misses, strongest AWRAG candidate vs benchmark gold was classified by deterministic heuristic triage:

```text
candidate stronger than gold heuristic: 43
ambiguous / partial: 23
near tie: 10
gold stronger than candidate heuristic: 7
```

This is not scientific adjudication. It is a review queue.

It shows that many benchmark misses are not clean "AWRAG failed to find evidence" cases. Some are likely corpus-overlap disagreements where AWRAG selected evidence that appears stronger or parallel to the labeled gold document.

## Methodology Rule Added

Going forward:

```text
Do not assume the expected answer/gold document is the strongest answer according to the corpus.
```

For each benchmark miss:

```text
1. Compare benchmark gold evidence.
2. Compare AWRAG-selected evidence.
3. Classify the disagreement.
4. Only then decide whether the system failed, the ranking needs work, or the benchmark label deserves review.
```

Miss categories should include:

```text
gold stronger
AWRAG stronger
parallel / both partial
near tie
exact-number mismatch
predicate mismatch
scope mismatch
no answer / gold present
candidate absent
ranking buried
gate suppressed
```

## Changelog From This Session

- Confirmed the current full SciFact native dataset run used 300 test rows.
- Preserved the prior valid retrieval baseline: `209 / 300 = 69.67% Hit@10`.
- Confirmed the current qualified-gate output scored `179 / 300 = 59.67% Hit@10`.
- Confirmed raw native count candidates without the final qualification gate returned to `209 / 300 = 69.67% Hit@10`.
- Ran lead-at-end reasoning experiments without modifying the engine.
- Found lead-at-end rare-focus reranking had signal but was not stable enough alone: `211 / 300 = 70.33% Hit@10`.
- Built strength-ranked evidence candidates from native AWRAG candidates at depth 250.
- Produced the current strongest valid score: `217 / 300 = 72.33% Hit@10`.
- Confirmed strength-ranked Top5 nearly matches the prior baseline Top10: `208 / 300` vs `209 / 300`.
- Rejected an invalid quick local `184 / 300` comparison because it did not use the native AWRAG count path.
- Established that benchmark score and strongest-evidence discovery are separate metrics.
- Established that benchmark misses should be audited before being treated as failures.

## Product Meaning

AWRAG should report both:

```text
Benchmark Gold Agreement
Best Evidence Discovery
```

These should sit beside each other, not replace each other.

Benchmark Gold Agreement measures whether AWRAG found the labeled document.

Best Evidence Discovery measures whether AWRAG found the strongest supported evidence visible in the corpus.

This distinction is essential for evidence-based review systems because real corpora contain overlapping claims, repeated findings, parallel evidence, and stronger documents that may not be the benchmark-labeled target.

## Boundary

This commit should include this documentation only.

Do not commit:

```text
SciFact raw data
runtime datasets
generated reports
count binaries
query outputs
benchmark artifacts
local absolute runtime folders
```

The committed artifact is a human-readable truth-state log and changelog for later push/review.
