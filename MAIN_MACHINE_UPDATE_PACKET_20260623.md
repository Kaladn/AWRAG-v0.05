# Main Machine Update Packet - 2026-06-23

Status: update branch handoff.

Purpose: carry the current AWRAG cleanup and foundation work to the main machine safely.

## Branch Intent

This update branch is for:

```text
zero active runtime data
dataset symbol terminology
index readiness gate
packet speech CLI/tool lane
dataset folder + global symbol allocator law
roadmap/glossary cleanup
```

## Current Data State

```text
zero active ingested data
zero active runtime datasets
zero active dataset lexicons
zero active counts
zero active citations
zero active coordinates
```

No data was re-ingested.

No sample dataset was created.

## Main Changes

```text
runtime/generated data removed
cache residue removed
active symbol wording changed from public symbol to dataset symbol
active symbol system changed to awrag_dataset_6b@1
query blocks with INDEX_NOT_READY when required artifacts are missing
packet-speech command promoted as a report/tool lane
TrueVision notes removed from AWRAG tracked tree
new docs define dataset-folder law and global monotonic symbol allocator plan
```

## Safety Boundaries

This branch does not:

```text
re-ingest data
create new symbols
query a dataset
patch old datasets
write lifetime memory
write pristine lexicon entries
merge datasets
change ranking/count math
```

## Tests

Latest local verification before handoff:

```text
python -m pytest -q -p no:cacheprovider
90 passed
```

## Main Machine Update Rule

Do not expect `master` to contain this work until this branch is merged or fast-forwarded.

Recommended main-machine check:

```powershell
git fetch origin
git status -sb
git switch -c review-dataset-symbol-reset origin/updates/dataset-symbol-zero-data-reset-20260623
python -m pytest -q -p no:cacheprovider
```

If using the patch bundle instead of GitHub branch, apply the patch to a clean checkout and run the same tests.

## Do Not Touch

```text
source archives
external data folders
lifetime/pristine lexicon
historical receipts unless intentionally rewriting history
backend scoring/ranking/count math
```
