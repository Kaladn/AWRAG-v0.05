# Resonance Sample Promotion Decision

Status: adapter validated; native count promotion blocked.

Source folder inspected:

```text
operator-supplied resonance sample folder named "basement_analysis  RESONANCE SAMPLE FOR LEARNING"
```

## What Exists

The folder contains:

```text
analysis_results.json
context_clouds.json
context_map.json
process_story.py
process_story_standalone.py
standalone_context_parser.py
summary_report.md
plots/cloud_size_distribution.png
plots/resonance_heatmap.png
__pycache__/standalone_context_parser.cpython-311.pyc
```

The adapter successfully produced:

```text
resonance_anchor_records.jsonl
resonance_adapter_summary.json
resonance_adapter_summary.md
dataset_symbol_lexicon.json
resonance_symbol_records.jsonl
resonance_context_edges.jsonl
resonance_cloud_edges.jsonl
symbol_receipt.json
binary_count_readiness_receipt.json
```

Latest validated runtime output:

```text
runtime/resonance_samples/basement_resonance_symbolized_20260623
```

## What Was Proven

```text
context anchors: 2544
cloud anchors: 2544
symbolized records: 2544
symbol anchors: 2546
symbol collisions: 0
context edges: 69171
cloud edges: 43945
source mutated: false
AW intake ran: false
native .awbin counts written: false
```

## Source Search

A read-only source-drive search was run for likely raw-source/raw-count names:

```text
*The Basement*.txt
*basement*.txt
*Basement*.md
*basement*.md
*raw*count*.json
*observation*.json
*relation*count*.json
```

Result:

```text
No original story text or raw observation/count table was found.
```

## Decision

Do not promote this sample into native AW counts yet.

Reason:

```text
The saved resonance JSON contains derived top-k positional layout and resonance strengths.
It does not contain raw observation counts per center/offset/neighbor.
```

Native count authority requires:

```text
original source text
or
raw observation rows:
  center_anchor / neighbor_anchor / offset / observation_count
```

Top-k clouds and resonance scores are useful for understanding the old map shape.

They are not enough to honestly reconstruct the native count field.

## Allowed Use

The resonance sample may be used as:

```text
adapter validation
old-system shape study
debug/visual map reference
symbolized display artifact
future fixture if source text is recovered
```

## Forbidden Use

Do not use this sample as:

```text
native count authority
query-ready dataset
production re-ingest proof
evidence of full binary promotion
```

## Next Unlock

If the original story text is recovered:

```text
source text
-> normal AW intake
-> true 6-left/self/6-right observations
-> native count files
-> overview/link trail report
```

If a raw count table is recovered:

```text
raw observation rows
-> validate schema
-> assign dataset symbols
-> write native relation counts
-> write receipts
```
