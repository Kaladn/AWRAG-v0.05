# AWRAG Next Work Plan

Status: planning document only. No implementation changes are included here.

Core law:

```text
Frontend displays.
Backend bridge translates.
AWRAG decides.
```

## Current Position

AWRAG is the public/demo evidence-engine slice. The current safe direction is:

```text
verify release gate
-> preserve CLI as the canonical interface
-> optionally expose read-only UI views beside the CLI
-> optionally wire minimal explicit UI actions beside the CLI
-> defer new systems until separately specified
```

No work should begin by adding chat storage, graph export, symbol return, dataset removal, approval workflows, or old Clearbox logic.

The existing AWRAG core and CLI must keep working unchanged. The UI is an optional surface, not a replacement path.

## Phase 0: Release Gate First

Goal: prove the current repo/package is clean and still demonstrates the corrected AWRAG contract.

Checks:

- No `__pycache__`.
- No `.pyc`.
- No runtime `sqlite3` import.
- No `dataset_counts.sqlite`.
- No hardcoded local machine paths.
- Tests pass.
- CLI help works.
- Sample `init -> intake -> status -> query` works.
- `.awbin` count files are created.
- Status reports `awrag_native_binary_counts@1`.
- Symbol system reports `awrag_public_6b@1`.
- `persistent_memory=false`.
- Outputs include watermark/facsimile notice.

Deliverable:

```text
RELEASE_GATE_REPORT.md
```

No code patch unless the gate finds a release-blocking issue and the fix is explicitly approved.

## Phase 1: Optional Read-Only UI Adapter

Goal: support the AWRAG evidence surface as an optional interface without changing the existing CLI/core behavior.

The read adapter may aggregate existing backend facts for display, but it may not create new facts.

If implemented, create only:

```text
src/awrag/ui_read_bridge.py
```

Allowed read-only functions:

- status
- dataset manifest
- dataset-local lexicon search
- anchor detail
- citation lookup
- coordinate lookup
- evidence packet display
- count backend status
- symbol system status
- miss diagnosis display from existing query fields
- watermark/facsimile notice display

Forbidden:

- No count/ranking logic.
- No citation authority.
- No symbol assignment.
- No dataset mutation.
- No model calls.
- No raw file editing.
- No old Clearbox business logic.

Test gate:

- Read adapter writes no files.
- Read adapter does not mutate datasets.
- Lexicon search returns data from `state/dataset_lexicon.json`.
- Anchor detail resolves by anchor and symbol.
- Count backend status matches `engine.status`.
- Symbol status matches manifest/lexicon fields.
- CLI behavior remains unchanged.

## Phase 2: Optional Read-Only Surface Wiring

Goal: connect the static UI concept to read-only adapter outputs without replacing CLI usage.

Allowed UI behavior:

- Display status.
- Display manifest.
- Display lexicon search results.
- Display anchor details.
- Display citations.
- Display coordinates.
- Display evidence packets.
- Display miss diagnosis.

Forbidden UI behavior:

- No inline evidence edits.
- No lexicon row edits.
- No count edits.
- No symbol edits.
- No browser-side evidence decisions.
- No browser-side citation decisions.

Deliverable:

```text
UI_READ_ONLY_WIRING_REPORT.md
```

## Phase 3: Optional Minimal Action Adapter

Goal: expose only current AWRAG actions through a bounded optional adapter while preserving direct CLI use.

Create only after Phase 1/2 pass:

```text
src/awrag/ui_action_bridge.py
```

Allowed first actions:

- init dataset
- intake dataset
- query dataset
- dispatch an approved AWRAG tool request to one of the allowed actions

Rules:

- Every mutating action must call the existing AWRAG backend function.
- Every mutating action must return an existing backend receipt/output path.
- The bridge may validate request shape.
- The bridge may reject unknown tool names.
- The bridge may format safe error messages.
- The bridge may not perform the underlying evidence work itself.
- The frontend may request a named backend tool, but it must never execute tool behavior itself.

Test gate:

- `init_dataset` calls `engine.ensure_dataset`.
- `intake_dataset` calls `engine.intake`.
- `query_dataset` calls `engine.query`.
- No action bridge path bypasses AWRAG engine functions.
- Unknown tool names are rejected before any backend action runs.
- CLI commands remain a supported first-class path.

## Phase 4: Deferred New Backend Modules

These are real modules, not bridge formatting. Do not implement them during the first bridge pass.

Deferred modules:

- Dry inspection / pre-intake coverage.
- Approval packet / rejection packet workflow.
- Re-ingest workflow.
- Chat storage.
- Chat finalization as counted source.
- Graph exfil.
- Dataset removal.
- Returned-symbol file.
- Install-local symbol ledger.

Each needs:

- separate spec
- explicit data model
- receipt format
- tests
- release gate update

## Phase 5: Graph Exfil Later

Goal: export AWRAG evidence structures to graph formats without replacing the count backend.

Possible outputs:

- Neo4j CSV
- GraphML
- JSON graph

Rules:

- AWRAG `.awbin` files remain source of truth.
- Exfil creates export artifacts only.
- Exfil must write receipts.
- Exfil must not alter count files.

## Phase 6: Dataset Removal And Symbol Return Later

Goal: safely remove dataset/source data and return eligible symbols for future assignment.

Rules:

- Removal is not deletion-only.
- Backend must verify references.
- Backend must write a removal receipt.
- Backend must return eligible symbols to a returned-symbol file.
- Next ingest must consume returned symbols first only after ledger behavior is approved.

Do not touch current public demo symbol behavior until the ledger spec is approved.

## Recommended Next Smallest Patch

Do not patch yet. If approved, the next smallest safe implementation is:

```text
src/awrag/ui_read_bridge.py
```

with only:

```text
status
manifest
lexicon search
anchor detail
count backend status
symbol system status
protected notice
```

That gives the Lexicon Viewer/Search page real data without creating a God bridge.
