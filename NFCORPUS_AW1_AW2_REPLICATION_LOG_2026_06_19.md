# NFCorpus AW1/AW2 Replication Log - 2026-06-19

This log records the cross-machine NFCorpus replication result for AWRAG v0.05.

It is a documentation artifact only. No raw benchmark data, generated reports, runtime folders, count binaries, or local output artifacts are committed here.

## Repo / Engine

AW1 reported:

```text
AWRAG repo: D:\AnchorWorks_Clean_Runtime\AWRAG-v0.05
Commit: bffc2f095dae087ec00e522824372dcce0101f3e
Backend: awrag_native_binary_counts@1
Symbol system: awrag_public_6b@1
```

AW2 local repo state:

```text
Commit: bffc2f0 Align package version with v0.05
CLI version: awrag 0.05
```

## Dataset

Benchmark:

```text
BeIR/nfcorpus
BeIR/nfcorpus-qrels test
```

Shared receipts:

```text
Corpus rows / blocks: 3,633
Test queries: 323
Qrel query IDs: 323
Backend: awrag_native_binary_counts@1
Symbol system: awrag_public_6b@1
Anchor count: 25,932
Block postings: 696,324
Relation records: 5,405,576
Persistent memory: false
```

## AW1 Report Builder

AW1 reported:

```text
D:\AnchorWorks_Clean_Runtime\AWRAG_NFCorpus_Benchmark_20260619\reports\build_nfcorpus_reports.py
SHA256: 9C6FF976F21552AA58899701B8134D0DC6408F1679C9FD05977F59406B129706
```

Command:

```powershell
python .\AWRAG_NFCorpus_Benchmark_20260619\reports\build_nfcorpus_reports.py
```

Important boundary:

```text
The strength scorer was report-side code, not AWRAG engine code.
```

## Scoreboard Comparison

### Qualified AWRAG Path

AW1:

```text
Hit@1:  108 / 323 = 33.44%
Hit@3:  155 / 323 = 47.99%
Hit@5:  182 / 323 = 56.35%
Hit@10: 197 / 323 = 60.99%
```

AW2:

```text
Hit@1:  108 / 323 = 33.44%
Hit@5:  182 / 323 = 56.35%
Hit@10: 197 / 323 = 60.99%
```

The qualified engine output replicated at Hit@10 exactly.

### Raw No-Gate Native Count Walk

AW1:

```text
Hit@1:  109 / 323 = 33.75%
Hit@3:  157 / 323 = 48.61%
Hit@5:  185 / 323 = 57.28%
Hit@10: 204 / 323 = 63.16%
```

AW2:

```text
Hit@1:  109 / 323 = 33.75%
Hit@3:  157 / 323 = 48.61%
Hit@5:  186 / 323 = 57.59%
Hit@10: 205 / 323 = 63.47%
```

The raw native candidate path replicated tightly. The one-hit difference is small and should be investigated through exact report-script parity if exact reproducibility is required.

### Strength-Ranked Evidence Candidates

AW1:

```text
Hit@1:  132 / 323 = 40.87%
Hit@3:  171 / 323 = 52.94%
Hit@5:  188 / 323 = 58.20%
Hit@10: 207 / 323 = 64.09%
```

AW2:

```text
Hit@1:  113 / 323 = 34.98%
Hit@3:  162 / 323 = 50.15%
Hit@5:  189 / 323 = 58.51%
Hit@10: 208 / 323 = 64.40%
```

Interpretation:

```text
Candidate pool is effectively similar.
Top-rank ordering differs.
The difference comes from report-side strength scoring, not native AWRAG engine behavior.
```

## Disagreement Audit Comparison

AW1 remaining strength Top10 misses:

```text
AW stronger by anchor coverage: 60
near tie by anchor coverage: 27
ambiguous partial: 4
gold stronger by anchor coverage: 7
no AW candidate: 18
```

AW2 remaining strength Top10 misses:

```text
AW stronger heuristic: 64
near tie heuristic: 19
ambiguous / partial: 5
gold stronger heuristic: 9
no candidate / gold present: 18
```

The disagreement pattern replicated:

```text
Many benchmark misses are not clean engine failures.
Many are evidence-disagreement or near-tie review cases.
Some are real AW flaws.
```

## Boundary Discovered

The native AWRAG evidence engine is stable across machines.

The strongest-evidence judge is currently external report code.

Therefore:

```text
Benchmark-label agreement can be compared across machines now.
Strength-ranked ordering cannot be compared exactly until the strength scorer is versioned.
```

## Required Next Step

Create a versioned scorer receipt for strength-ranking reports.

Minimum required fields:

```text
reranker_name
reranker_version
script_path
script_sha256
candidate_depth
dedupe_rule
scoring_formula
qrels_used_for_selection: false
engine_commit
count_backend
symbol_system
```

Suggested name:

```text
awrag_strength_reranker@0.1
```

## Correct Claim

The defensible current claim is:

```text
AWRAG v0.05 replicated native evidence-engine behavior across machines.
NFCorpus also replicated the benchmark-label-agreement versus strongest-evidence-discovery split.
Strength-ranked ordering is promising but must be version-locked before exact rank comparisons are treated as engine results.
```

Do not claim:

```text
The benchmark is wrong.
AWRAG is always right.
Strength-ranking is engine behavior.
```

Do claim:

```text
AWRAG exposes where benchmark gold labels and corpus-strength evidence disagree.
That disagreement can reveal AWRAG flaws, benchmark limitations, or both.
```
