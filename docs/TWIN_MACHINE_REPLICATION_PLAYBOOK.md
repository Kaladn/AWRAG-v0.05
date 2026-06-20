# Twin Machine Replication Playbook

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

This playbook keeps Machine 1 and Machine 2 aligned without destroying work that
may exist only on one machine.

## Prime Rule

```text
Snapshot before update.
Diff before overwrite.
Packets before wording.
```

Machine 2 may contain extended local work. Do not reset it, overwrite it, or
assume it is disposable.

## Branch Governance

```text
master / main
= stable public-review animal
= no casual mutation

updates/*
= update channel
= candidate behavior
= safe for machine-to-machine alignment
```

Current update branch:

```text
updates/chat-metadata-index
```

## Machine Snapshot Commands

Run these on each machine before pulling or copying anything:

```powershell
git rev-parse HEAD
git branch --show-current
git status --short
git log --oneline --decorate -5
python -m awrag.cli --version
python -m pytest tests -q
```

If using a local source tree without editable install:

```powershell
$env:PYTHONPATH = "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
py -3.11 -m awrag.cli --version
py -3.11 -m pytest tests -q
```

## GitHub Snapshot Commands

Capture the remote state before pulling:

```powershell
git remote -v
git ls-remote origin
git fetch origin
git log --oneline --decorate --all -10
git diff --stat HEAD..origin/updates/chat-metadata-index
git diff --stat origin/updates/chat-metadata-index..HEAD
```

Interpretation:

```text
HEAD..origin/updates/chat-metadata-index
= what GitHub has that this machine lacks

origin/updates/chat-metadata-index..HEAD
= what this machine has that GitHub lacks
```

If Machine 2 has local changes, save them before updating:

```powershell
git diff > MACHINE2_LOCAL_UNCOMMITTED_DIFF.patch
git status --short > MACHINE2_LOCAL_STATUS.txt
```

Do not run destructive reset commands as part of this playbook.

## Update Without Destroying Machine 2

Preferred safe path:

```powershell
git fetch origin
git switch updates/chat-metadata-index
git pull --ff-only origin updates/chat-metadata-index
```

If `--ff-only` fails, stop and inspect. That means Machine 2 diverged.

Do not merge or reset until a human reviews:

```powershell
git log --oneline --left-right --cherry-pick HEAD...origin/updates/chat-metadata-index
git diff --stat HEAD...origin/updates/chat-metadata-index
```

## Chat Data Transfer

Chat data is dataset-local data, not repo code.

Transfer raw/staged chat data by USB or local copy. Do not commit raw chat data
to the public repo.

Expected scopes:

```text
previous_chats_chatgpt_2024_12_25
previous_chats_chatgpt_2026_06_delta
previous_chats_chatgpt_combined
codex_sessions_*
```

Each chat ingest keeps its own:

```text
dataset-local lexicon
dataset-local native counts
metadata sidecar
citations
coordinates
receipts
```

## Rebuild Dataset Counts

For every transferred source folder:

```powershell
py -3.11 -m awrag.cli intake `
  --runtime-root <LOCAL_RUNTIME> `
  --dataset-id <DATASET_ID> `
  --source <SOURCE_FOLDER>
```

Then verify:

```powershell
py -3.11 -m awrag.cli status `
  --runtime-root <LOCAL_RUNTIME> `
  --dataset-id <DATASET_ID>
```

Required status values:

```text
count_backend = awrag_native_binary_counts@1
persistent_memory = false
dataset scope = dataset_local
```

## Determinism Receipt

After both machines rebuild, run the same command on both:

```powershell
py -3.11 -m awrag.cli determinism `
  --runtime-root <LOCAL_RUNTIME> `
  --dataset-id <DATASET_ID> `
  --questions <QUESTION_LIST_TXT> `
  --top-k 10 `
  --output <OUTPUT_DIR>\determinism_<MACHINE_ID>.json
```

Compare:

```text
repo HEAD
branch
git status
dataset artifact hashes
native .awbin hashes
raw AW packet hashes
citation order
block order
score fields
```

If raw packets match and wording differs:

```text
renderer / bot / human interpretation difference
```

If raw packets differ:

```text
repo / data / count / index / retrieval / ranking / citation difference
```

## Packet Diff Forms

Use:

```text
docs/AW_PACKET_DIFF_FORMS_V1.md
```

Order:

```text
1. Machine A fills AW_DIFF_REPORT_V1
2. Machine B fills AW_DIFF_REPORT_V1
3. Compare into AW_MACHINE_DIFF_V1
4. Classify disagreement layer
5. Discuss final answer wording
```

## Benchmark Zip Transfer

When a new benchmark is downloaded on Machine 1:

```text
leave original zip in Downloads
copy zip to USB
copy exact intake notes with it
do not rely on a hidden cache
```

Machine 2 should rebuild from the same zip, not from a guessed folder.

Minimum benchmark transfer receipt:

```text
zip file path
zip SHA256
unpack directory
source file count
source byte count
dataset_id
intake command
status output
determinism receipt path
```

## What Not To Do

```text
Do not overwrite Machine 2 local work.
Do not commit raw chats to the repo.
Do not write benchmark data into lifetime/user counts.
Do not compare final wording before packet hashes.
Do not use SQL/database replacement.
Do not mutate master/main.
Do not reset hard without explicit human approval.
```
