# Runtime Folder Contract

Purpose: keep repository files, generated runtime files, reports, and receipts separated.

## Repository

The repository stores:

- source code
- tests
- docs
- launcher scripts
- compact report templates
- compact historical reports when intentionally committed

The repository must not store:

- raw corpora
- production runtime data
- generated dataset counts
- generated symbolized chunk payloads
- generated receipt streams unless intentionally packaged

## Dataset Runtime

Normal dataset runtime shape:

```text
<runtime-root>/
  datasets/
    <dataset-id>/
      dataset_manifest.json
      state/
      counts/
      coordinates/
      citations/
      outputs/
      receipts/
```

Production dataset artifacts belong under the selected runtime root, not loose in the repo.

## Laptop Temp Intake Runtime

Laptop temp intake is an isolated prep lane:

```text
<generated-state-root>/
  <run-id>/
    manifest.json
    resource_receipt.json
    source_receipt.json
    progress.json
    run_events.jsonl
    chunk_receipts.jsonl
    chunk_failures.jsonl
    file_failures.jsonl
    run_summary.json
    chunks/
```

This lane does not merge into production counts.

This lane does not write lifetime memory.

This lane does not replace normal `awrag intake`.

## Receipts

Receipts are authority.

A run is trusted by receipts, not by terminal claims.

Important receipt files:

- `resource_receipt.json`
- `source_receipt.json`
- `progress.json`
- `run_events.jsonl`
- `chunk_receipts.jsonl`
- `chunk_failures.jsonl`
- `file_failures.jsonl`
- `run_summary.json`

## Git Hygiene

Generated runtime folders are ignored by Git.

If a report must be committed, keep it compact and do not include raw corpora or generated binary payloads.
