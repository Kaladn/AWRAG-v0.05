# AWRAG Next Work Plan

Status: planning document only. No implementation changes are included here.

This is the current top-level roadmap spine for the AWRAG demo/product slice.

Core law:

```text
Frontend displays.
Operator shell routes.
Backend/AWRAG decides.
Receipts prove.
```

## Current Position

AWRAG now has a working evidence-engine core and a terminal-first operator surface.

The immediate product shape is:

```text
operator input
-> OSRL safety/context audit
-> command card or evidence request
-> existing AWRAG command/core
-> meter-first progress for long work
-> receipts/reports
```

The current priority is not a new backend and not a GUI rebuild.

The current priority is:

```text
finish the operator-facing roadmap
keep backend behavior stable
use OSRL to prevent bad work from starting
keep distribution later
```

## Completed / Stable

These are current stable foundations.

```text
native binary count backend
dataset-local public symbol system
CLI as canonical interface
query/status/intake/batch paths
special-search command
operator shell front door
operator command cards
OSRL v0 operator-state audit
laptop-temp-intake isolated sidelane
resource-aware laptop safety receipts
wide-deep evidence reasoning documented
native-aware score/rank report docs
```

Rules:

- Preserve these unless a specific bug is proven.
- Do not replace working paths with new architecture.
- Do not mutate scoring, symbol behavior, citation authority, or count files during roadmap work.
- Keep tests and receipts as the proof layer.

## Active Operator Surface

Purpose: make the working system usable without hiding what it is doing.

Current shape:

```text
awrag-operator / python -m awrag.operator_shell
```

Operator law:

```text
chat stays the cockpit
slash commands are handles
side operations are explicit
receipts are authority
```

Active work:

- Keep command cards readable.
- Keep shortcuts visible.
- Keep long operations meter-first.
- Keep detailed logs in files, not on the operator screen.
- Keep every action tied to an existing command or documented locked/future command.

Do not add:

- hidden actions
- model authority
- GUI-owned truth
- frontend business logic
- silent dataset mutation

Supporting docs:

```text
docs/OPERATOR_UI_CONTRACT.md
docs/CLI_SHORTCUTS.md
docs/AWRAG_CLI_OPERATOR_GUIDE.md
docs/RUNTIME_FOLDER_CONTRACT.md
```

## Active Safety / OSRL

Purpose: audit operator input before AWRAG responds or acts.

Locked distinction:

```text
OSRL audit = what kind of operator input is this, and is AW allowed to act?
Evidence audit = what does admitted data prove?
```

Current OSRL v0 route classes include operator safety modes such as command, evidence demand, ambiguity, vent, destructive lock, correction, and system-shape law handling.

Supporting docs:

```text
docs/OSRL_OPERATOR_STATE_REASONING_LAYER.md
docs/reports/osrl_v0/OSRL_V0_RECEIPT.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## ASAP: Input Cloud Coherence Gate

This is the next OSRL item.

Status:

```text
planned
not implemented
documentation staged
requires active conversation/task cloud
requires operator confirmation gate
```

Purpose:

```text
raw operator input
-> extract anchors
-> compare anchors against active conversation/task cloud
-> detect low-fit disruptor anchors
-> suggest correction if a nearby high-fit anchor exists
-> block execution until operator confirms
-> preserve raw and corrected input in receipt
```

Example class:

```text
raw voice input: DUI
active cloud: CLI, GUI, operator shell, interface, shortcuts, side windows
likely intended anchor: GUI
action: block and ask before executing
```

Safety law:

```text
detect mismatch before work starts
do not silently autocorrect
do not execute malformed instructions
operator confirms the correction
raw input is preserved
```

Roadmap placement:

```text
Active Safety / OSRL
-> OSRL v1: Input Cloud Coherence Gate
```

Staging doc:

```text
docs/ROADMAP_REFACTOR_INPUT_CLOUD_GATE.md
```

Next documentation-only step:

```text
define OSRL v1 requirements and tests
```

Next implementation step, only after explicit approval:

```text
add active task cloud + low-fit anchor warning to OSRL
```

## Planned: Memory Travel Gate

Status:

```text
planned
not implemented
belongs after OSRL/input cloud
```

Purpose: check admitted conversation/history evidence before work starts.

This is not nostalgia retrieval.

Correct memory law:

```text
memory is checking what already happened before we act again
```

Flow:

```text
new operator input
-> OSRL route
-> Input Cloud Coherence Gate
-> Memory Travel Gate
-> did we already do this?
-> what result survived?
-> what failed?
-> what was corrected?
-> act, refuse, continue, or warn
```

Example:

```text
operator asks about machine settings
-> AW checks prior admitted chat evidence
-> detects older/newer contexts
-> surfaces final surviving decision
-> asks whether to continue, revise, or override
```

Rules:

- Do not mutate evidence during the memory check.
- Do not treat old mentions as final decisions unless receipts support that.
- Surface older context, newer context, failures, corrections, and final surviving decision.
- Ask before reopening solved work.

Supporting trace:

```text
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## Active Intake / Laptop Lane

Purpose: let laptop hardware prepare or prove data safely without replacing production intake.

Current status:

```text
implemented as isolated sidelane
explicit call only
ignored/generated runtime output
per-chunk receipts
resource-aware worker and RAM selection
resume/skip verified chunks
bad-file logging and continue behavior
no production merge
no lifetime write
```

Rules:

- Do not promote this lane to production automatically.
- Do not merge chunk outputs into dataset counts until a separate merge spec is approved.
- Do not use full-corpus resident loads on laptop hardware.
- Keep external-terminal launch and meter-first progress for long runs.

Supporting doc:

```text
docs/LAPTOP_TEMP_INTAKE.md
```

Remaining work:

```text
run real long receipt
review operator experience
tighten presentation only if receipts justify it
```

## Planned: Release/Runtime Cleanup Before Distribution

Purpose: keep the repo clean before any distribution pass.

Cleanup spine:

```text
finish roadmap/to-do
preserve working proof
strip generated data
lock runtime boundaries
push clean system
then refactor into a real distributable repo
```

Checks:

- No `__pycache__`.
- No `.pyc`.
- No runtime `sqlite3` import.
- No `dataset_counts.sqlite`.
- No hardcoded local machine paths.
- Tests pass.
- CLI help works.
- Sample `init -> intake -> status -> query` works.
- `.awbin` count files are created.
- Status reports `awrag_native_binary_counts@1`.
- Symbol system reports `awrag_public_6b@1`.
- `persistent_memory=false`.
- Outputs include watermark/facsimile notice.

Deliverable when run:

```text
RELEASE_GATE_REPORT.md
```

## Deferred Wide-Deep Evidence Reasoning

Status:

```text
documented
deferred unless explicitly pulled forward
```

Purpose:

```text
question
-> native topK/rank key
-> wide field expansion
-> deep proof burden
-> consequence classification
-> answer form selection
-> evidence-controlled speech receipt
```

Rules:

- Do not change retrieval.
- Do not change scoring.
- Do not change citation authority.
- Do not change intake behavior.
- Keep this report/algorithm lane separate until approved.

Supporting doc:

```text
docs/WIDE_DEEP_EVIDENCE_REASONING_ROADMAP.md
```

## Deferred Benchmark Answer Standard

Status:

```text
deferred
report/design lane only
```

Purpose: define an AWRAG benchmark standard that measures answer formation from cited content, not document-hit alone.

Correct benchmark distinction:

```text
document found != answer formed
```

Better benchmark shape:

```text
question
-> cited document block
-> document-only answer
-> citation lines
-> rank key
-> receipt
```

Score lanes should stay separate:

```text
document_hit
cited_content_support
document_only_answer_quality
rank_key_receipt_present
support_absent_refusal
benchmark_gold_mismatch
```

Rules:

- Do not replace existing benchmark reports retroactively.
- Do not claim leaderboard superiority from this alone.
- Keep document-hit metrics as reference only.
- Add answer-from-cited-content metrics as a separate AW-style standard.

Supporting trace:

```text
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## Deferred Evidence Speech / ClearSpeak Forms

Status:

```text
deferred to another session except isolated report tools already used for diagnostics
```

Purpose:

```text
candidate_0 defines the answer spine
aligned topK candidates provide support
drift creates refusal pressure
citations remain attached
```

Rules:

- No speech work until packet generation and operator safety are stable.
- No LLM-owned answer authority.
- No uncited generated claims.
- No backend scoring mutation.
- AW forms readable output from cited document blocks only.
- Answer forms may change presentation, not truth.
- Receipts always exist, but receipts do not always have to be spoken.

Answer form profiles to design later:

```text
plain_speech
operator_card
receipt_detail
developer_debug
benchmark_report
evidence_packet
compact_summary
```

Plain speech mode matters for listening-first operator contexts:

```text
no tables unless requested
no code blocks unless requested
no boxed layouts
short paragraphs
receipts summarized in normal language
```

Supporting roadmap section:

```text
docs/POST_LEXICON_SCAFFOLD_LOOP_V0_ROADMAP.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## Deferred Exfil / Removal / Symbol Return

Status:

```text
visible concept
locked for now
```

Future purpose:

```text
remove selected dataset/source material
write removal report
return eligible symbols to returned-symbol file
write receipt
preserve audit trail
```

Rules:

- No deletion-only behavior.
- No hidden symbol reuse.
- No active implementation until ledger spec exists.
- No current public demo symbol behavior changes.

## Deferred Generation Memory

Status:

```text
deferred
```

Purpose:

```text
successful and failed scaffold answers
-> answer forms
-> glue paths
-> bad/good phrasing
-> generation memory
```

Rules:

- Generation memory cannot create evidence claims.
- Failed attempts may be remembered as failures, not trusted behavior.
- Passed/corrected behavior requires receipts.

Supporting roadmap:

```text
docs/POST_LEXICON_SCAFFOLD_LOOP_V0_ROADMAP.md
```

## Deferred Distribution Packaging

Status:

```text
later
```

Do not package the system until:

```text
roadmap is clean
repo is clean
runtime/data boundaries are locked
operator shell is documented
release gate passes
generated data is excluded
```

Distribution should package the system, not the local workbench mess.

## Deferred GPU Count Field Accelerator Lane

Status:

```text
deferred
not authority
not current work
```

Purpose: later acceleration lane for count-field/matrix experiments when enough data exists to justify it.

Rules:

- CPU/file-backed evidence core remains authority.
- GPU may accelerate count/matrix experiments later.
- GPU output cannot replace deterministic source evidence.
- Citations and receipts remain available on demand.
- Do not open this lane before current CPU/file-backed receipts are stable.

Supporting trace:

```text
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## Optional / Deferred Read-Only UI Bridge

The older read-only UI bridge plan remains optional and deferred.

It is not the current priority.

If revived later, it must obey:

```text
Frontend displays.
Backend bridge translates.
AWRAG decides.
```

Allowed read-only functions only:

- status
- dataset manifest
- dataset-local lexicon search
- anchor detail
- citation lookup
- coordinate lookup
- evidence packet display
- count backend status
- symbol system status
- watermark/facsimile notice display

Forbidden:

- No count/ranking logic.
- No citation authority.
- No symbol assignment.
- No dataset mutation.
- No model calls.
- No raw file editing.
- No old Clearbox business logic.

## Current Next Move

Next documentation-only move:

```text
expand OSRL v1 Input Cloud Coherence Gate requirements/tests
```

Next implementation move, only after explicit approval:

```text
implement Input Cloud Coherence Gate inside OSRL front gate
```

Do not start distribution, evidence speech, exfil, graph export, or backend refactor before the operator safety lane is locked.
