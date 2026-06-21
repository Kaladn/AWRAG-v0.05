# Special Search CLI Instructions

Purpose: run a locked, JSON-list driven special search over an existing AWRAG dataset and write review receipts.

This is a report tool, not a learning loop.

## Command

```powershell
awrag special-search `
  --runtime-root <runtime> `
  --dataset-id <dataset> `
  --trigger-list <triggers.json> `
  --out <report-folder> `
  --expand-prev 1 `
  --expand-next 1 `
  --max-hits-per-anchor 500
```

## Input JSON

Supported shapes:

```json
{
  "anchors": [
    { "anchor": "motherfucker", "class": "vulgar_insult" }
  ]
}
```

```json
{
  "entries": [
    { "surface": "danger", "class": "state_signal_candidate" }
  ]
}
```

A plain JSON list is also allowed:

```json
["danger", "trash", "lawsuit"]
```

## Output Files

The command writes:

- `trigger_anchors.json`
- `trigger_hits.jsonl`
- `trigger_expanded_blocks.jsonl`
- `mini-local-counts.json`
- `temporal_causality_graph.json`
- `trigger_anchor_summary.md`
- `unmatched_phrases.jsonl`
- `run_receipt.json`

## Rules

- Uses the existing AWRAG anchor rules.
- Searches solo anchors only.
- Grouped phrases that cannot run as solo anchors go to `unmatched_phrases.jsonl`.
- Every event starts with `confidence: 0.0` and `needs_review: true`.
- Writes report receipts only.
- Does not mutate AW counts, citations, coordinates, lexicon, or source data.
- Does not complete or replace the later learning phase.
