# AWRAG CLI Operator Guide

Purpose: use the existing AWRAG command line without guessing which lane mutates data, which lane only reports, and which lane is a temporary laptop-safe proof path.

Run commands from the repository root:

```powershell
cd <repo-root>
python -m awrag.cli --help
```

The installed command may also be available as `awrag`. When in doubt, use `python -m awrag.cli` because it runs the repo currently on disk.

## Core Flow

Create a dataset scope:

```powershell
python -m awrag.cli init --runtime-root <runtime> --dataset-id <dataset>
```

Ingest a source folder into that dataset:

```powershell
python -m awrag.cli intake --runtime-root <runtime> --dataset-id <dataset> --source <source-folder> --window 6
```

Check dataset status:

```powershell
python -m awrag.cli status --runtime-root <runtime> --dataset-id <dataset>
```

Ask one question and get a cited local packet:

```powershell
python -m awrag.cli query --runtime-root <runtime> --dataset-id <dataset> --question "What does this dataset say?" --top-k 5
```

Run a question file:

```powershell
python -m awrag.cli batch --runtime-root <runtime> --dataset-id <dataset> --questions <questions.txt> --top-k 10
```

Batch rules:

- Put one question per line.
- Blank lines are ignored.
- The terminal should show a progress meter unless `--no-progress` is used.
- Outputs are written under the dataset output folder.
- `model_used` remains `none`.

## Special Search

Use this for JSON-list driven anchor search reports:

```powershell
python -m awrag.cli special-search --runtime-root <runtime> --dataset-id <dataset> --trigger-list <triggers.json> --out <report-folder> --expand-prev 1 --expand-next 1 --max-hits-per-anchor 100
```

This lane is report-only against an existing dataset. It writes:

- `trigger_hits.jsonl`
- `trigger_expanded_blocks.jsonl`
- `mini-local-counts.json`
- `temporal_causality_graph.json`
- `trigger_anchor_summary.md`
- receipts

Special search must not mutate dataset counts, citations, coordinates, or lifetime memory.

## Laptop Temp Intake

Use this when the laptop should prepare bounded chunks without replacing production intake:

```powershell
python -m awrag.cli laptop-temp-intake --source <file-or-folder> --state-root <generated-state-root> --run-id <run-id> --chunk-mb 25 --max-chunks 3
```

Current lane meaning:

- isolated chunk-local prep
- symbol-first chunk artifacts
- chunk receipts
- no production merge
- no lifetime memory write
- no replacement of `awrag intake`

First proof run should stay small:

```powershell
python -m awrag.cli laptop-temp-intake --source <file-or-folder> --state-root <generated-state-root> --run-id proof_001 --chunk-mb 25 --max-chunks 3
```

Review:

- `run_summary.json`
- `manifest.json`
- `chunk_receipts.jsonl`
- per-chunk receipt files

Do not call this production until a later merge command exists and passes receipts.

## Determinism Receipt

Use this before comparing two machines:

```powershell
python -m awrag.cli determinism --runtime-root <runtime> --dataset-id <dataset> --questions <questions.txt> --top-k 10 --output <receipt.json>
```

The receipt exists to split disagreements into:

- repo/version mismatch
- dataset artifact mismatch
- query packet mismatch
- renderer/report mismatch

## Crosslink

Use this only when two dataset-local scopes already exist and the goal is citation/evidence comparison between them:

```powershell
python -m awrag.cli crosslink --runtime-root <runtime> --left-dataset-id <left-dataset> --right-dataset-id <right-dataset> --question "What overlaps?" --top-k 8
```

## Codex Chat Staging

Use this to stage Codex session JSONL into markdown documents that can later be ingested:

```powershell
python -m awrag.cli stage-codex --sessions-root <sessions-root> --output <staged-output>
```

Staging is not the same as intake. Stage first, inspect the files, then choose whether to ingest.

## Operator Rules

- Long jobs should run in an external terminal so the operator can keep working.
- Terminal output should be meter-first: progress, phase, counts, RAM, and ETA.
- Detailed JSON belongs in log/receipt files, not spammed to the operator screen.
- Generated runtimes, staged data, and receipts stay out of Git unless intentionally packaged as compact reports.
- Raw corpora do not get committed.
- Dataset-local artifacts remain dataset-local.

## Mutating vs Report-Only

Mutating dataset lane:

- `init`
- `intake`

Report/query lanes:

- `status`
- `query`
- `batch`
- `special-search`
- `determinism`
- `crosslink`

Temporary isolated prep lane:

- `laptop-temp-intake`

The temporary lane does not become production just because it runs. It earns promotion only through receipts, tests, and an explicit later merge design.
