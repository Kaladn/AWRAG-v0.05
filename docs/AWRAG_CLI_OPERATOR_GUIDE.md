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
python -m awrag.cli batch --runtime-root <runtime> --dataset-id <dataset> --questions <questions.txt> --top-k 10 --workers 4
```

Batch rules:

- Put one question per line.
- Blank lines are ignored.
- The terminal should show a progress meter unless `--no-progress` is used.
- Outputs are written under the dataset output folder.
- `model_used` remains `none`.
- `--workers 4` means four parallel question workers or fail before work starts.
- `--workers 1` is refused. Single-core batch execution is not an operator path.

## Dataset Overview

Use this when the operator needs an overview of what lives in the count field:

```powershell
python -m awrag.cli dataset-overview --runtime-root <runtime> --dataset-id <dataset> --out <overview-folder>
```

This lane reads existing count, block, citation, coordinate, and lexicon artifacts. It writes:

- `overview_summary.json`
- `overview_summary.md`
- `anchor_overviews.jsonl`
- `relationship_trails.jsonl`
- receipts

Dataset overview is not a reasoning engine and does not answer a question. It shows top anchors, top cohabitation relationships, and source trails.

## Count-Walk Speech

Use this when the operator wants a rough count-guided speech walk from one count-selected local evidence spine:

```powershell
python -m awrag.cli count-walk-speech --runtime-root <runtime> --dataset-id <dataset> --question "What does the data say?" --out <speech-folder> --top-k 5 --max-steps 50 --branch-k 5
```

Optional starter:

```powershell
python -m awrag.cli count-walk-speech --runtime-root <runtime> --dataset-id <dataset> --question "What does the data say?" --starter "known phrase" --out <speech-folder>
```

This lane writes:

- `evidence_trace/count_walk_trace_<id>.json`
- `pretty_answer/count_walk_speech_<id>.md`
- `receipts/run_receipt.json`
- `receipts/no_mutation_receipt.json`

Count-walk speech rules:

- Existing query/count ranking selects the evidence block.
- `block_anchor_postings.awbin` provides the local spine.
- Native relation counts choose among local continuation candidates.
- The output is rough anchor speech, not final ClearSpeak.
- If a starter is provided and not found in the selected local spine, the walk refuses.
- No model is used.
- Retrieval/ranking/count logic is not changed.

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
python -m awrag.cli laptop-temp-intake --source <file-or-folder> --state-root <generated-state-root> --run-id <run-id> --chunk-mb 25 --max-chunks 3 --workers 4 --reserve-ram-fraction 0.50
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
python -m awrag.cli laptop-temp-intake --source <file-or-folder> --state-root <generated-state-root> --run-id proof_001 --chunk-mb 25 --max-chunks 3 --workers 4 --reserve-ram-fraction 0.50
```

Review:

- `run_summary.json`
- `manifest.json`
- `resource_receipt.json`
- `chunk_receipts.jsonl`
- `chunk_failures.jsonl`
- per-chunk receipt files

Resource behavior:

- `--workers 4` means use four workers or fail before work starts.
- `--workers auto` detects CPU/RAM for parallel work but must still select at least two workers.
- `--workers 1` is refused. Single-core execution is not an operator path.
- `--reserve-ram-fraction 0.50` reserves half of system RAM before worker selection.
- `--reserve-ram-gb <number>` can set a minimum RAM reserve.
- `--progress-snapshot-interval-sec 5` writes periodic `progress.json` updates.
- Use `--progress-snapshot-interval-sec 0` to update `progress.json` after every chunk.
- `--refuse-below-reserve` stops before work starts if free RAM is already below the requested reserve.
- `--max-file-mb <number>` and `--oversized-file-policy skip|fail|chunk` control oversized file handling.
- `--json-output` prints full JSON when progress is enabled; otherwise the operator sees a compact summary.
- Every run records the selected worker count and reserve decision in `resource_receipt.json`.
- Failed chunks are written as failure receipts and the run continues where possible.
- Detailed run events are written to `run_events.jsonl`.

Do not call this production until a later merge command exists and passes receipts.

External terminal launcher:

```powershell
.\Start_Laptop_Temp_Intake.ps1 -Source <file-or-folder> -StateRoot <generated-state-root> -RunId proof_001 -ChunkMb 25 -MaxChunks 3
```

The launcher opens a separate PowerShell window, runs the same CLI command, keeps the meter visible there, and leaves chat/terminal space free for other work.

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
- `progress.json` is the live unattended check file for laptop-temp-intake.
- `run_events.jsonl` is the detailed run log for laptop-temp-intake.
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
- `dataset-overview`
- `count-walk-speech`
- `special-search`
- `determinism`
- `crosslink`

Temporary isolated prep lane:

- `laptop-temp-intake`

The temporary lane does not become production just because it runs. It earns promotion only through receipts, tests, and an explicit later merge design.
