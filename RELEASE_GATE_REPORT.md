# Release Gate Report

Status: PASS after generated residue cleanup.

This report verifies the current AWRAG core package before any optional UI adapter work.

## Scope

Checked:

- Existing CLI/core behavior.
- Native demo-safe count backend.
- Public demo symbol namespace.
- Package hygiene.
- Test suite.
- Sample `init -> intake -> status -> query` smoke path.

Not changed:

- Count engine.
- Symbol behavior.
- Citation authority.
- Evidence qualification.
- Query behavior.
- CLI behavior.
- Model behavior.
- Dataset mutation rules.

No UI adapter or backend bridge was implemented during this gate.

## Hygiene Results

| Check | Result |
|---|---|
| Generated `__pycache__` residue removed | PASS |
| Generated `.pyc` residue removed | PASS |
| Runtime `sqlite3` import absent | PASS |
| `dataset_counts.sqlite` absent | PASS |
| Release-scanned files have no hardcoded local machine paths | PASS |
| Truth history preserved outside release-scanned Markdown | PASS |

Notes:

- The comparison history artifact intentionally contains prior machine/run paths for audit context.
- To preserve that history without breaking public package hygiene, it is stored as `AWRAG_TRUE_HISTORY_FOR_COMPARISON.local`.
- That file is a local comparison artifact, not a release-scanned Markdown document.

## Test Results

Command shape:

```text
python -B -m pytest -p no:cacheprovider tests -q
```

Result:

```text
16 passed
```

## CLI Help

Command shape:

```text
python -B -m awrag.cli --help
```

Result:

```text
PASS
```

Available commands:

```text
init
intake
status
query
```

## Smoke Path

Command path:

```text
init -> intake -> status -> query
```

Source:

```text
README.md
```

Dataset:

```text
release_gate_smoke
```

Temporary runtime:

```text
created under system temp and removed after verification
```

Smoke result:

| Check | Result |
|---|---|
| Status count backend | `awrag_native_binary_counts@1` |
| Manifest symbol system | `awrag_public_6b@1` |
| Manifest symbol bytes | `6` |
| Lexicon symbol system | `awrag_public_6b@1` |
| Persistent memory | `false` |
| Watermark locked | `true` |
| Final answer status | `answered_from_awrag_locations` |
| SQLite count files in smoke runtime | `0` |

Created count files:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

Smoke counts:

| Metric | Value |
|---|---:|
| Anchor count | 300 |
| Relation count | 6040 |
| Block anchor postings | 725 |
| Citation count | 54 |

## Gate Verdict

The current core passes the release gate.

The package demonstrates:

- dataset-local evidence indexing
- native demo-safe binary counts
- public demo six-byte symbols
- source coordinates
- AWRAG-owned citations
- receipts / query outputs
- no persistent memory
- no model-owned retrieval
- no SQLite count backend

## Next Allowed Step

Only after this report:

```text
optional read-only UI adapter
```

First adapter scope:

```text
status
manifest
lexicon search
anchor detail
count backend status
symbol system status
protected notice
```

Still deferred:

- action bridge
- graph exfil
- dataset removal
- returned-symbol file
- chat finalization
- approval/rejection workflow
- dry inspection
- install-local symbol ledger

