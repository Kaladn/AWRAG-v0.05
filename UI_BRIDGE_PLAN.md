# Optional UI Adapter Plan

Status: proposal only. No adapter code has been added.

The existing AWRAG CLI remains a first-class interface. Any UI path is optional and must sit beside the CLI, not replace it.

## Boundary

```text
Frontend displays.
Backend bridge translates.
AWRAG decides.
```

The optional adapter may translate UI requests into existing AWRAG calls and display shapes. It must not become a second engine.

## Allowed Optional Adapter Modules

Create at most two modules, only after approval:

```text
src/awrag/ui_read_bridge.py
src/awrag/ui_action_bridge.py
```

No other bridge modules in the first patch.

## Module 1: ui_read_bridge

Purpose: read-only inspection.

Allowed operations:

- `get_status(runtime_root, dataset_id)`
- `get_manifest(runtime_root, dataset_id)`
- `search_lexicon(runtime_root, dataset_id, query=None, prefix=None, limit=100)`
- `get_anchor_detail(runtime_root, dataset_id, anchor=None, symbol=None)`
- `get_citation(runtime_root, dataset_id, citation_id)`
- `get_coordinate(runtime_root, dataset_id, citation_id=None, block_id=None)`
- `get_evidence_packet(runtime_root, dataset_id, output_path_or_id)`
- `get_count_backend_status(runtime_root, dataset_id)`
- `get_symbol_system_status(runtime_root, dataset_id)`
- `get_miss_diagnosis(runtime_root, dataset_id, output_path_or_id)`

Allowed data sources:

- `dataset_manifest.json`
- `state/dataset_lexicon.json`
- `state/blocks.jsonl`
- `counts/anchor_counts.awbin`
- `counts/relation_counts.awbin`
- `counts/block_anchor_postings.awbin`
- `coordinates/coordinate_index.jsonl`
- `citations/citations.jsonl`
- `outputs/query_*.json`
- `receipts/*.json`

Forbidden:

- No new ranking.
- No citation creation.
- No symbol assignment.
- No mutation.
- No external calls.
- No model calls.
- No old Clearbox store logic.
- No changes to CLI behavior.

## Module 2: ui_action_bridge

Purpose: explicit optional UI actions only. Direct CLI use remains supported.

Allowed first-patch operations:

- `init_dataset(runtime_root, dataset_id, owner)`
- `intake_dataset(runtime_root, dataset_id, source, owner, window=6)`
- `query_dataset(runtime_root, dataset_id, question, top_k=5)`

Allowed later only after approval:

- `request_approval_packet(...)`
- `request_rejection_packet(...)`
- `request_reingest(...)`
- `request_dataset_removal_receipt(...)`

Mutation receipt rule:

Every mutating operation must return an AWRAG backend receipt or output path. The optional adapter can validate request shape before calling AWRAG, but it cannot perform the underlying mutation itself.

## First Patch Recommendation

Patch only `ui_read_bridge.py` first.

Why:

- It is read-only.
- It does not touch count engine behavior.
- It does not touch symbol behavior.
- It does not touch citation authority.
- It does not add chat behavior.
- It lets the Lexicon Viewer/Search tab become real without dangerous mutations.
- It preserves CLI usage unchanged.

First patch endpoints/functions should cover:

```text
status
manifest
lexicon search
anchor detail
count backend status
symbol system status
watermark/facsimile notice
```

Then add:

```text
citation lookup
coordinate lookup
evidence packet display
miss diagnosis display
```

Only after that should `ui_action_bridge.py` expose:

```text
init dataset
intake dataset
query dataset
```

## Explicitly Deferred

Do not implement these in the first bridge patch:

- Chat storage.
- Chat finalization as counted source.
- Dry inspection.
- Coverage approval/rejection packets.
- Graph exfil.
- Dataset removal.
- Returned-symbol file.
- Install-local symbol ledger.
- Theme controls.

These are real modules, not bridge formatting. They need their own approved specs and tests.

## Test Requirements For First Patch

Read-only bridge tests:

- Status read returns same count fields as `engine.status`.
- Manifest read returns `symbol_system`, `symbol_bytes`, scope, count backend, and protected notice.
- Lexicon search does not mutate `dataset_lexicon.json`.
- Anchor detail resolves by anchor and by symbol.
- Count backend status reports `.awbin` paths and record counts.
- Symbol system status reports public demo namespace and non-transferable flags.
- No output files are written by `ui_read_bridge`.

Action bridge tests when approved:

- Init creates dataset shell and returns status.
- Intake calls `engine.intake` and returns intake receipt.
- Query calls `engine.query` and returns output path plus answer packet.
- Mutating bridge calls never bypass AWRAG engine functions.
- CLI commands still work directly.
