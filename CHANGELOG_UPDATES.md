# AWRAG Updates Branch Changelog

This changelog tracks update-branch changes that are not yet part of the stable
main branch. Main stays the stable public-review release surface; update
branches carry focused, test-backed improvements for review.

## updates/chat-metadata-index

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

