# Dataset Folder And Global Symbol Allocator Law

Status: implementation law and planning contract.

This document defines the clean ingest foundation for the next AWRAG/AW re-ingest pass.

It does not claim the current code already satisfies every requirement.

## Core Lock

```text
Dataset-local evidence.
Global symbol uniqueness.
No symbol collision.
No silent merge.
```

Mental model:

```text
Dataset folder = local world.
Dataset lexicon = local map.
Global symbol registry = no-collision allocator.
Pristine lexicon = approved/correct truth lane.
Lifetime bridge = later, explicit only.
```

Most important rule:

```text
Start at zero once.
Continue forever.
Never reuse a symbol.
```

## Dataset Folder Law

Every dataset gets its own folder.

Each dataset folder owns its own:

```text
blocks/
counts/
state/
citations/
coordinates/
outputs/
receipts/
manifest
dataset lexicon
dataset index
```

No dataset writes into another dataset folder.

No query may cross dataset folders unless an explicit cross-dataset or lifetime bridge is built later.

## Re-Ingest Law

We are going to re-ingest all data.

Current data state:

```text
zero active ingested data
zero active runtime datasets
zero active dataset lexicons
zero active counts
zero active citations
zero active coordinates
```

Treat existing datasets as disposable unless explicitly preserved as historical output.

Do not patch old datasets in place.

Build clean datasets from source again.

Before query, every dataset must pass index readiness:

```text
blocks exist
dataset lexicon exists
relation counts exist
block-anchor postings exist
citations/coordinates exist
intake receipt exists
artifacts are non-empty
```

If readiness fails:

```text
INDEX_NOT_READY
query_allowed=false
```

## Symbol Allocator Law

The symbolizer starts at zero only once per symbol namespace.

It must persist the last assigned symbol.

For the next dataset, it must continue from the last assigned symbol.

It must never regenerate the same symbols for a different dataset.

Example:

```text
dataset_001 uses symbols 0..49,999
dataset_002 starts at 50,000
dataset_003 starts after dataset_002 ends
```

Anchors may repeat across datasets.

Symbols may not collide.

## Dataset Lexicon Vs Global Symbol Registry

Each dataset has its own dataset lexicon.

The dataset lexicon maps that dataset's admitted anchors to the symbols assigned during intake.

A separate simple global symbol registry tracks:

```text
symbol_namespace
last_assigned_symbol
assigned ranges
dataset_id
dataset_folder
range_start
range_end
created_at
receipt
```

The global registry is not the answer engine.

It is not the pristine approved lexicon.

It exists to prevent symbol collision and preserve symbol allocation history.

## Pristine Lexicon Separation

Do not mix this with the pristine approved AW lexicon.

The pristine lexicon remains for corrected/approved terms only.

This new/simple registry is for large-scale symbol allocation and collision prevention.

It is experimental but operationally required for clean re-ingest.

## Required Receipts

Every dataset intake must write a receipt containing:

```text
dataset_id
dataset_folder
source_count
block_count
anchor_count
symbols_created
symbol_range_start
symbol_range_end
last_assigned_symbol_before
last_assigned_symbol_after
collision_count
duplicate_word_count
counts_written
citations_written
coordinates_written
runtime_path
worker_count
memory_budget
drive_type if detectable
elapsed_time
```

## Collision Rules

Before writing a symbol assignment:

```text
check symbol not already assigned
check dataset range does not overlap existing ranges
check allocator state is current
write receipt
```

If collision or overlap is detected:

```text
STOP
COLLISION_DETECTED
query_allowed=false
intake_allowed=false until reviewed
```

## Boundaries

Do not use flat-file search as the answer path.

Do not query before index readiness.

Do not merge datasets silently.

Do not write to lifetime/pristine lexicon unless explicitly approved.

Do not let Codex answer for AW.

Do not use model reasoning as evidence.

## Target Ingest Shape

```text
source data
-> dataset folder
-> canonical blocks
-> block-local coordinates
-> anchors
-> globally unique symbols
-> dataset lexicon
-> native counts/index
-> citations/coordinates
-> receipts
-> query allowed only after index readiness
```

## Current Code Gaps

The current dataset-symbol code does not yet implement this full law.

Known gaps:

```text
src/awrag/engine/anchors.py
```

Current symbol behavior:

```text
symbol_for(anchor)
-> SHA-derived dataset 6-byte symbol from anchor text
```

That means repeated anchors across datasets can receive the same symbol.

The new law requires:

```text
global monotonic allocator
persisted last_assigned_symbol
dataset-specific assigned range
no reuse across datasets
```

Current collision guard:

```text
assert_no_symbol_collisions(...)
```

This only checks collisions inside the current dataset-local symbol namespace.

It does not prove global no-reuse across datasets.

Known anchorization gap:

```text
anchorize(...)
```

Current dataset-symbol anchorization still applies a stop-anchor list and normalization. If the target ingest law is "all anchors count", anchorization must be corrected in a separate approved slice before production re-ingest.

Do not claim compliance until these gaps are implemented and tested.

## Implementation Plan

First implementation slice:

```text
GlobalSymbolAllocator v0
```

Responsibilities:

```text
read allocator state
lock allocator state for intake
reserve the next contiguous range
write assigned range receipt
update last_assigned_symbol
fail closed on overlap/collision
```

Proposed registry artifacts:

```text
<global-symbol-registry-root>/allocator_state.json
<global-symbol-registry-root>/assigned_ranges.jsonl
<global-symbol-registry-root>/receipts/
```

Dataset artifacts:

```text
<runtime-root>/datasets/<dataset-id>/state/dataset_lexicon.json
<runtime-root>/datasets/<dataset-id>/receipts/intake_*.json
```

Second implementation slice:

```text
intake uses dataset lexicon symbols, not SHA-derived active symbols
```

Required behavior:

```text
extract anchors
build unique anchor list
allocate globally unique symbols
write dataset lexicon
symbolize blocks from dataset lexicon
count from assigned symbols
write non-empty native count artifacts
write receipts
```

Third implementation slice:

```text
index readiness validates symbol allocation receipts
```

Readiness must verify:

```text
dataset lexicon exists
symbol range exists
range does not overlap registry
counts are non-empty
citations/coordinates are non-empty
intake receipt names the same symbol range
```

## Tests Required Before Re-Ingest

Minimum tests:

```text
two datasets with the same anchor receive different symbols
dataset ranges never overlap
allocator resumes from last_assigned_symbol
collision detection fails closed
query is blocked when symbol receipt is missing
query is blocked when index artifacts are missing
counts are written from assigned symbols
pristine lexicon is not mutated
lifetime memory is not mutated
```

## Stop Conditions

Stop immediately if:

```text
symbol range overlaps a previous dataset
allocator state cannot be locked
dataset lexicon disagrees with receipt
counts were built from text instead of assigned symbols
query attempts to run before INDEX_READY
any pristine/lifetime store changes without explicit approval
```

## Completion Condition

The ingest foundation is not complete until:

```text
global registry persists allocation state
each dataset owns its folder and lexicon
same anchor across datasets does not reuse a symbol
receipts prove ranges and counts
index readiness blocks partial datasets
query uses only ready indexed datasets
tests pass
```
