# AWRAG Updates Branch Changelog

This changelog tracks update-branch changes that are not yet part of the stable
main branch. Main stays the stable public-review release surface; update
branches carry focused, test-backed improvements for review.

## updates/chat-metadata-index

### Added: packet diff forms and twin-machine playbook

- Added `docs/AW_PACKET_DIFF_FORMS_V1.md`.
- Added `docs/TWIN_MACHINE_REPLICATION_PLAYBOOK.md`.
- The forms require each machine to fill the same structured packet report
  before any final answer wording is compared.
- The playbook treats Machine 2 as potentially divergent or extended:
  snapshot first, diff first, fast-forward only, stop on divergence.
- The playbook includes dataset-local rebuild commands, determinism receipt
  commands, and benchmark zip transfer receipt requirements.
- This is documentation/governance only. It does not change retrieval, scoring,
  counts, symbols, citations, or model authority.

### Added: twin-machine determinism receipt

- Added `awrag determinism`.
- The command writes `awrag_twin_machine_determinism_receipt@1`.
- The receipt hashes repo state, dataset-local artifacts, native `.awbin`
  count files, citations, coordinates, optional question lists, and raw AW query
  packets.
- Query receipts include citation order, location order, score fields, text
  hashes, raw packet hash, and final answer hash.
- Purpose: distinguish AW/runtime/data/version differences from
  renderer/interpretation differences when two machines disagree.
- This is a sidecar receipt only. It does not change retrieval, scoring,
  qualification, counts, citations, symbols, or model authority.

### Changed: modular engine package

- Backed up the pre-split engine at
  `backups/engine_20260620_pre_modular_split.py`.
- Replaced the single `src/awrag/engine.py` module with the
  `src/awrag/engine/` package.
- Split engine concerns into anchors, base schemas/constants, storage, intake
  pipeline, querying, qualification, chat metadata, Codex staging, forensic
  receipts, and crosslinks.
- Preserved the public `awrag.engine` import surface through package
  re-exports.
- No scoring, backend, symbol-system, dataset-scope, lifetime-memory, model, or
  crosslink behavior was intentionally changed.

### Added

- Added dataset-local chat metadata indexing during intake.
- New sidecar:
  `state/chat_metadata_index.jsonl`
- Each chat metadata row records:
  - `conversation_id`
  - `message_id`
  - `title`
  - `speaker`
  - `created_at`
  - `date`
  - `time`
  - `turn_index`
  - `block_ordinal`
  - `block_id`
  - `citation_id`
  - `line_start`
  - `line_end`
- Copied parsed chat metadata onto each `blocks.jsonl` block belonging to that
  chat turn so query filtering can happen before block scoring.
- Added CLI query filters:
  - `--created-after`
  - `--created-before`
  - `--speaker user|assistant`
- Added status fields:
  - `chat_metadata_row_count`
  - `chat_metadata_index_path`

### Preserved

- Count backend remains `awrag_native_binary_counts@1`.
- Public demo symbol system remains `awrag_public_6b@1`.
- Chat metadata indexing does not use SQLite or any database backend.
- Chat metadata indexing does not write lifetime memory.
- Query filtering narrows candidate blocks before scoring; it does not replace
  native binary counts, citations, or coordinates.

### Why

Chat datasets need time-aware and speaker-aware narrowing. Reviewers and
operators should be able to ask for evidence like:

```text
voltage settings after 2024-12-10
latest user hardware report
assistant replies near this date
```

The metadata sidecar gives AWRAG a clean way to narrow chat evidence by date and
speaker while keeping every chat ingest as a solo dataset-local lexicon/count
scope.

### Added: forensic support receipts

- Every query result now includes `forensic_support_receipt`.
- The receipt is reconstructive, not accusatory.
- Added support ladder:
  - `L1 artifact_or_subject_referenced`
  - `L2 artifact_existence_evidenced`
  - `L3 artifact_contents_recovered`
  - `L4 artifact_modification_evidenced`
  - `L5 artifact_referenced_after_modification`
  - `L6 deletion_or_rejection_discussed`
  - `L7 deletion_or_rejection_evidenced`
  - `L8 contradictory_statements_found`
  - `L9 execution_or_deployment_evidenced`
- Added support levels:
  `strong`, `partial`, `weak`, `insufficient`, `conflict`.
- Added regression coverage proving conceptual discussion of a system does not
  become execution/deployment evidence.

### Added: canonical chat dataset receipt

- Added `docs/CANONICAL_CHAT_DATASET_2026-06-20.md`.
- The receipt records the combined chat dataset state without committing raw
  private chat data to the repository.
- The canonical chat dataset remains dataset-local, native `.awbin`, six-byte
  public-demo symbols, no SQLite, and no lifetime memory.

### Added: Codex staging and citation crosslinks

- Added `awrag stage-codex` to convert Codex session JSONL into AWRAG chat-turn
  markdown for normal dataset-local intake.
- Added `awrag crosslink` to build citation-to-citation sidecars between two
  existing dataset scopes.
- Crosslinks are written as JSONL receipts under a dataset-local `_crosslinks`
  scope.
- Crosslinks compare AWRAG query packets only; they do not merge raw corpora,
  mutate `.awbin` counts, write lifetime memory, use SQL, or let a model search.
