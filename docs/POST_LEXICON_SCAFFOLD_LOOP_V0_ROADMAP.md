# Post-Lexicon Scaffold Loop v0 Roadmap

Purpose: turn ingested dataset matter into bounded machine memory through self-questioning, grading, correction, and consequence records.

Core law:

```text
ingestion = brain matter
self-questioning = memory construction
answers = temporary thinking scaffolds
failures = consequence memory
passed/corrected outputs = trusted behavior candidates
```

Nothing is thrown away. A failed answer is not trusted behavior, but it is still memory.

## 1. Evidence Core

Owns existing AWRAG facts:

```text
native counts
anchors
source blocks
citations
coordinates
query packets
```

Rules:

```text
No mutation during scaffold learning.
No model authority.
No global knowledge.
No citation invention.
```

Output role: provides bounded evidence only.

## 2. Resident Runtime

Purpose: load native binaries once and serve fast read-only packet generation.

Shape:

```text
.awbin files
-> resident RAM index
-> locked read-only service
-> question packets
-> append-only receipts/deltas
```

Rules:

```text
No per-question binary crawl.
No file mutation while locked.
No GPU until RAM path passes.
```

## 3. Native Memory Lanes

Initial lanes:

```text
brain_matter.awbin          raw ingested anchor/count material
citation_crossing.awbin     anchor/source/cross-document evidence links
question_scaffold.awbin     questions, answers, child questions, anchor status
attempt_memory.awbin        every answer attempt, pass or fail
failure_memory.awbin        failed attempts with explanations and violated rules
correction_memory.awbin     retry notes, what changed, final retry status
behavior_memory.awbin       only trusted passed/corrected behavior
generation_memory.awbin     answer forms, glue paths, bad/good phrasing
procedure_memory.awbin      ordered steps, errors, corrections, verification
```

JSON stays as receipts/manifests only.

## 4. Scaffold Loop

Loop:

```text
seed questions from dataset anchors
answer from resident memory only
attach citations
build crossings
grade attempt
write attempt memory
if failed: write failure memory, retry, write correction memory
if passed/corrected: write behavior memory
extract major anchors
spawn child questions
continue until limits hit
```

Stop limits:

```text
max runtime
max disk growth
max records
max depth
max retries
anchor exhaustion
```

## 5. Consequence Memory

Corrected law:

```text
Every attempt enters memory.
Failed attempts enter as failures.
Corrections enter as repair paths.
Only passed/corrected behavior enters trusted behavior memory.
```

Failure memory must include:

```text
failure type
failure explanation
missing anchors
missing variables
unsupported terms
bad anchor path
missing citation/crossing
violated rule
retry guidance
```

This is how the system remembers the burn without trusting the burn.

## 6. Grading

Grading must answer:

```text
Is the answer inside dataset boundary?
Are meaningful terms supported by anchors?
Are citations present?
Are crossings consistent?
Are degree/quantity claims supported by variables?
Did the answer introduce unsupported terms?
Is contradiction reported instead of merged?
```

A grade is not just pass/fail. The explanation is the learning object.

## 7. Generation Lexicon/Binary

Current foundation exists:

```text
generation_lexicon.py
generation_binary.py
anchor_speech_assembly.py
```

Purpose:

```text
observed anchors carry meaning
allowed glue repairs readability
relation phrases speak relationships
forbidden terms block overclaiming
```

Next role: generation memory consumes successful and failed scaffold answers to improve answer forms without adding evidence authority.


## Reverse Intake Speech v0

Purpose: let AW speak from a retrieved evidence field by reversing the intake shape instead of inventing an answer.

Core shape:

```text
answer starter
-> retrieved AW evidence packet
-> temporary local 6-1-6 map
-> top-k continuation walk
-> glue repair only if the walk jams
-> cited candidate speech
```

This is not language understanding. It is evidence-field speech reconstruction.

Rules:

```text
Use retrieved AW evidence only.
Build the local answer map in memory only.
Do not save local answer maps as truth.
Do not invent answer content.
Do not use global knowledge.
Do not detach citations.
Do not let glue words create evidence claims.
Starter phrase begins the walk.
Top-k continuation does the first pass.
Generation/glue lexicon bridges only unreadable gaps.
Output is candidate speech, not new evidence.
```

Example test shape:

```text
question: Why are we contaminated?
starter: Yes, we are contaminated because
source: AW retrieved evidence packet
speech method: temporary local 6-1-6 walk over the packet only
```

Expected receipt:

```text
question
starter
source packet ids
local map size
walk path
jam points
used glue repairs
citations retained
candidate speech output
needs_review=true
confidence=0.0
```

First test lane:

```text
Use operator-owned chat corpus questions.
Retrieve evidence normally.
Build temporary local map from receipts.
Run starter-driven top-k speech.
Compare output against cited source blocks.
Do not promote until receipts prove the shape.
```
## 8. Conversational/Procedural Source Lane

Purpose: teach construction and procedure shape, not truth.

Candidate first sources:

```text
DailyDialog: human-written daily dialogue construction
EmpatheticDialogues: response posture, non-commercial caveat
basic CS/procedural corpus: commands, files, JSON, tests, errors, Git
```

Rules:

```text
Conversation data teaches surface construction only.
Procedural data teaches action/correction patterns.
Neither can create AW evidence claims.
```

## 9. First Child World

Start boring:

```text
basic CS
CLI
files
paths
commands
Python
JSON
binary files
tests
errors
Git
debugging
```

Goal: let the system learn the room it lives in before broad domains.

## 10. Promotion Gates

Nothing promotes unless it has receipts:

```text
load receipts
question receipts
attempt/failure/correction receipts
citation coverage
crossing coverage
binary size changes
throughput records/sec
failure/refusal counts
anchor cleared/unresolved counts
```

Promotion checks:

```text
No core mutation.
No hidden model truth.
No unsupported behavior writes.
Failures preserved with explanations.
Behavior memory contains only passed/corrected outcomes.
```

## 11. Non-Goals

Not now:

```text
UI
GPU backend
full autonomy
global web learning
model-owned retrieval
prompt-only behavior memory
silent mutation
claims without citations
```

## 12. Build Order

Tight next steps:

```text
1. Freeze current generation lexicon/binary experiment.
2. Build resident packet runtime v0 around existing native readers.
3. Define binary schemas for attempt/failure/correction memory.
4. Build scaffold answer record format.
5. Build grader v0 with explicit failure explanations.
6. Run 10-question bounded loop on basic CS/procedural corpus.
7. Inspect receipts before scaling.
```

North star:

```text
The system does not learn by being told it is right.
It learns by remembering every attempt, every failure, every correction, and every cited reason it survived.
```

## Locked Special Search Tool

`awrag special-search` is the approved special-search intake/report command before the later learning phase.

Shape:

```text
JSON anchor list
-> solo anchor search
-> hit expansion
-> previous/current/next context
-> mini-local-counts.json
-> temporal_causality_graph.json
-> summary + receipt
```

Rules:

```text
No UI.
No backend cojoin.
No mutation of AW counts/citations/coordinates.
No learning-loop claim.
No grouped phrase reasoning inside the command.
Grouped phrases that cannot run as solo anchors are written to unmatched_phrases.jsonl.
```

## Future CLI-Chat Operator UI

Build a beautiful CLI-chat command surface, not a traditional app dashboard.

Core shape:

- Chat remains the operator lane.
- Commands are typed into chat.
- CLI executes local AW commands.
- External windows are optional work surfaces.
- Receipts always return to chat.

Command examples:

- `#status`
- `#special-search`
- `#open-report`
- `#open-folder`
- `#bench`
- `#roadmap`
- `#stop`

Command acceptance law:

- A command marker is valid only at character 0 of live operator input.
- The command must come from `active_operator_chat`.
- The command anchor must exist in the explicit command registry.
- The command prefix must match its stored hash.
- Parameters require confirmation before mutating or long-running execution.
- Corpus data, logs, replayed chats, and reports can never trigger commands.

Safety law:

```text
Corpus hashtags are anchors.
Start-of-live-input hashtags are commands.
Commands require registry hash acceptance.
```

External window law:

- Windows may show progress, reports, folders, graphs, logs, citations, and diffs.
- No external window owns truth.
- No external window mutates state without a command receipt.
- Every completed action writes back to chat:
  - command run
  - files written
  - pass/fail
  - record counts
  - next allowed action

## CLI Operator Surface and Resource-Aware Laptop Lane

This section is roadmap-only. It does not imply new backend behavior is implemented yet.

The CLI is the command cockpit:

```text
operator command
-> existing AW command
-> progress meter
-> receipts
-> report paths
```

The immediate documentation target is a practical CLI operator guide that shows how to run:

```text
init
intake
status
query
batch
special-search
laptop-temp-intake
determinism
crosslink
stage-codex
```

Laptop-temp-intake remains an isolated sidelane until it earns promotion.

Future resource-aware requirements:

- detect system CPU/RAM before work starts
- reserve operator RAM so the laptop remains usable
- cap worker count from detected resources
- avoid full-corpus resident loads on laptop hardware
- use bounded chunks
- show meter-first progress
- send detailed logs to receipt files
- resume verified completed chunks
- fail one bad file, log it, and continue
- write a resource receipt with selected chunk size, worker count, RAM reserve, and safety decisions

Non-goals:

- no backend replacement
- no production count merge
- no lifetime memory write
- no hidden dataset mutation
- no UI implementation from this roadmap section

Promotion gate:

```text
resource receipt exists
no production writes proven
chunk receipts verified
resume proven
bad-file handling proven
operator responsiveness preserved
tests pass
```

Only after that gate can a later main-machine merge command be designed.
