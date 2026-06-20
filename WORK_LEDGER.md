# AWRAG Work Ledger

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

This file records architecture-significant work in plain language. It exists so
backend substitutions, storage changes, model changes, data-scope changes, and
contract changes cannot be hidden as implementation details.

## 2026-06-20 - Packet Diff Forms And Twin-Machine Playbook

### Operator Direction

Machine 2 may contain extended local work. The update path must not overwrite it.

The comparison order is:

```text
1. compare repo/data/count/citation packets
2. classify disagreement layer
3. discuss final answer wording
```

### Added

New docs:

```text
docs/AW_PACKET_DIFF_FORMS_V1.md
docs/TWIN_MACHINE_REPLICATION_PLAYBOOK.md
```

`AW_PACKET_DIFF_FORMS_V1.md` defines:

```text
AW_DIFF_REPORT_V1
AW_MACHINE_DIFF_V1
```

`TWIN_MACHINE_REPLICATION_PLAYBOOK.md` defines:

```text
snapshot before update
diff before overwrite
packets before wording
fast-forward only update path
stop on divergence
dataset-local rebuild commands
determinism receipt commands
benchmark zip transfer receipt
```

### Contract

This is governance and comparison infrastructure. It does not change retrieval,
ranking, qualification, citations, native count binaries, symbol assignment, or
model authority.

## 2026-06-20 - Twin-Machine Determinism Receipt

### Operator Direction

When two machines disagree, prove whether the disagreement is in AW or outside
AW before comparing final wording.

The receipt must separate:

```text
raw AW packet differs
```

from:

```text
raw AW packet matches but renderer/human wording differs
```

### Added

New CLI command:

```text
awrag determinism
```

It records:

```text
repo HEAD
branch
git status
dataset status
dataset manifest hash
dataset lexicon hash
blocks hash
metadata sidecar hash
native count binary hashes
citation index hash
coordinate index hash
question list hash
raw query packet hash
citation order
block/location order
score fields
final answer hash
```

### Contract

The determinism receipt is a comparison sidecar. It does not change retrieval,
ranking, qualification, citation rendering, count binaries, symbol assignment,
or model authority.

### Verification

```text
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 py -3.11 -m pytest tests -q
29 passed

PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 py -3.11 -m awrag.cli determinism --help
command displayed
```

## 2026-06-20 - Engine Modular Safety Split

### Operator Direction

Split the engine for blast-radius control, not beautification.

The public import surface must remain:

```text
awrag.engine
```

No feature changes, no scoring changes, no crosslink tuning, no data-scope
changes, no SQL, and no model authority changes were allowed.

### Backup Snapshot

The pre-split monolith was preserved at:

```text
backups/engine_20260620_pre_modular_split.py
```

### Concern Boundaries Created

The former single `src/awrag/engine.py` file is now the package:

```text
src/awrag/engine/
```

with concerns separated into:

```text
anchors.py
base.py
chat.py
codex.py
crosslinks.py
forensic.py
pipeline.py
qualification.py
querying.py
storage.py
```

`src/awrag/engine/__init__.py` re-exports the public API so existing imports keep
working.

### Contract Preserved

Unchanged:

```text
count_backend: awrag_native_binary_counts@1
symbol_system: awrag_public_6b@1
scope: dataset_local
lifetime/user counts: not written
SQL/database backend: not used
model search: not allowed
crosslink scoring: unchanged
```

### Verification

```text
PYTHONPATH=src py -3.11 -m pytest tests -q
28 passed

PYTHONPATH=src py -3.11 -m awrag.cli --version
awrag 0.05
```

### Honesty Statement

This split changes file layout only. It does not claim a faster engine, better
ranking, new scoring, or new evidence behavior.

## 2026-06-18 - Native Binary Count Backend Recovery

### Operator Direction

The public AWRAG demo must represent the AnchorWorks-style count engine shape:

```text
local admitted data
-> dataset-local lexicon
-> native binary dataset-local counts
-> source coordinates
-> AWRAG-owned citations
-> evidence/coordinate packet
```

The public demo may use the demo-safe symbol namespace:

```text
symbol_system: awrag_public_6b@1
symbol_bytes: 6
scope: dataset_local_demo_only
```

but it must not replace the count engine with SQL.

### What Went Wrong

Codex introduced SQLite in commit:

```text
9ca8bad Publish dataset-local AWRAG review demo
```

That commit added `src/awrag/engine.py` with:

```text
import sqlite3
counts/dataset_counts.sqlite
SQL tables for anchors, relations, blocks, block_anchors, and citations
SQL query path for neighbor lookup and block scoring
```

This was wrong for AWRAG. It preserved some reviewer-facing scaffolding, but it
did not preserve the required native binary count backend shape.

### Why It Was Wrong

SQLite is a general database backend. AWRAG requires a local, deterministic,
native binary count spine for the public demo.

The mistake changed the system claim from:

```text
native compact count structure
fast deterministic relation search
binary count behavior
small active evidence layer
```

into:

```text
SQLite-backed indexed storage with AWRAG-shaped metadata
```

That is not the same system.

### Recovery Performed

SQLite was removed from `src/awrag/engine.py`.

The active public demo backend is now:

```text
count_backend: awrag_native_binary_counts@1
```

Dataset-local binary count files:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

Reviewer-readable JSON/JSONL remains only for:

```text
dataset_manifest.json
state/dataset_lexicon.json
state/blocks.jsonl
coordinates/coordinate_index.jsonl
citations/citations.jsonl
outputs/
receipts/
```

### Tests Added

Regression test added:

```text
test_demo_uses_native_binary_counts_not_sqlite
```

The test requires:

```text
count_backend == awrag_native_binary_counts@1
anchor_counts.awbin exists
relation_counts.awbin exists
block_anchor_postings.awbin exists
dataset_counts.sqlite does not exist
sqlite_counts_path is not present in status output
```

### Verification

```text
python -m pytest tests -q
14 passed

python -m compileall src
passed

CLI verification:
count_backend = awrag_native_binary_counts@1
anchor_counts.awbin created
relation_counts.awbin created
block_anchor_postings.awbin created
```

### Current Honesty Statement

The public AWRAG demo now uses a demo-safe native binary count backend with
public six-byte dataset-local symbols.

It is not the private AnchorWorks lifetime count spine.

It must not be marketed as the private AnchorWorks symbol genome or private
lifetime memory system.

It may be described as:

```text
A public-review AWRAG slice using native fixed-width binary dataset counts and
demo-safe six-byte dataset-local symbols.
```

## Required Logging Rule Going Forward

Every future architecture-significant change must add a ledger entry before it
is considered complete.

Required fields:

```text
date
operator direction
files changed
contract affected
backend/storage affected
data scope affected
model authority affected
tests run
honesty statement
```

No backend, storage, model, symbol, count, citation, data-scope, or persistence
change may be treated as a private implementation detail.

## 2026-06-20 - Branch Governance Law And Chat Metadata Update Channel

### Operator Direction

Keep the original stable AWRAG animal caged. `main`/`master` is the known stable
reference. Candidate upgrades live on `updates/*` branches so multiple machines
can pull them like app updates without mutating the stable base.

### Change

Added the formal branch governance rule to:

```text
ARCHITECTURE_GUARDRAILS.md
```

The rule defines:

```text
main/master = stable reference
updates/* = isolated candidate update channels
```

No `updates/*` branch may merge into `main` or `master` without explicit
operator promotion.

This branch also carries:

```text
updates/chat-metadata-index
```

as the first update-channel branch.

### Files Changed

```text
ARCHITECTURE_GUARDRAILS.md
CHANGELOG_UPDATES.md
README.md
src/awrag/cli.py
src/awrag/engine.py
tests/test_awrag_dataset_local.py
```

### Contract Affected

Changed:

```text
chat metadata side index
date/speaker query filters
status reporting for chat metadata index rows
README usage documentation
update-branch changelog
branch promotion law
```

Not changed:

```text
native .awbin count backend
six-byte public demo symbols
dataset-local scope
AWRAG-owned citations
source coordinates
lifetime memory policy
model authority policy
SQL/database prohibition
```

### Backend / Storage Affected

Added metadata sidecar:

```text
state/chat_metadata_index.jsonl
```

This is a narrowing/annotation side index only. It is not a count backend and
does not replace:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

### Data Scope Affected

Chat metadata remains dataset-local. It does not promote chat content,
metadata, anchors, or counts into lifetime/user memory.

### Model Authority Affected

No model authority change. The default remains:

```text
model_used: none
model_may_search: false
```

### Tests Run

```text
python -m pytest tests\test_awrag_dataset_local.py -q
18 passed

python -m pytest tests -q
25 passed
```

Live dataset verification:

```text
chat_metadata_row_count: 31151
filtered voltage query by created-after/created-before/speaker returned [AWCIT-6bf9eeda17]
```

### Honesty Statement

The chat metadata index lets AWRAG narrow chat evidence by time/date and speaker
before scoring candidates. It does not make AWRAG understand time as reasoning.
It is a deterministic metadata filter over dataset-local chat blocks.

The stable branch remains untouched. This work lives on:

```text
updates/chat-metadata-index
```

## 2026-06-18 - Deterministic NLP Answer Resolver

### Operator Direction

Final answer output needs NLP, not LLM reasoning. AW owns evidence, citations,
coordinates, counts, and refusal. The language layer may only make admitted
locations readable.

### Change

Added:

```text
src/awrag/nlp_resolver.py
resolver: awrag_deterministic_nlp_resolver@1
```

The query output now includes:

```text
answer_packet
final_answer
```

The resolver receives only `answer_packet.locations`, picks readable
question-relevant sentences from those locations, and appends the AWRAG-owned
citation marker already present on the location.

### Guardrails

The resolver must not:

```text
search
read counts
read source files
create citations
rewrite citations
call an LLM
```

Unsupported packets return:

```text
status: not_enough_information
```

### Tests Added

Tests now verify:

```text
final_answer uses awrag_deterministic_nlp_resolver@1
model_used remains none
model_may_search remains false
citations come from answer_packet.locations
unsupported packets remain not_enough_information
```

## 2026-06-18 - Package Cleanup And Symbol Collision Guard

### Operator Direction

Before handoff, the reviewer package must be clean and generic:

```text
no bytecode caches
clear test instructions
public six-byte symbol collision guard
no dataset-specific code names
```

### Change

Added a dataset-local public symbol collision guard before binary count files
are written. If two different anchors map to the same six-byte public demo
symbol, intake fails instead of writing ambiguous counts.

Added explicit test instructions for:

```text
python -m pip install -e .
python -m pytest tests -q
```

and direct unpacked-package testing with:

```text
PYTHONPATH=src
```

### Tests Added

```text
test_intake_fails_on_public_symbol_collision
```
