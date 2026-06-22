# AWRAG Current Roadmap Spine

Status: documentation-only roadmap. No implementation changes are included here.

Authoritative system-shape references:

```text
AGENTS.md
.agents/AWRAG_AGENT_ONBOARDING.md
docs/AWRAG_HUMAN_COMPANION.md
```

Core law:

```text
The system is the admitted data.
Evidence authority comes from citations, coordinates, native rank keys, support classes, and receipts.
Pretty answers are presentation, not authority.
```

Operating law:

```text
Frontend/operator surfaces display.
Operator shell routes.
Backend/AWRAG decides from admitted evidence.
Receipts prove what happened.
```

## Current Position

AWRAG has a working evidence-engine core and a terminal-first operator surface.

Current product shape:

```text
operator input
-> OSRL safety/context audit
-> command card or evidence request
-> existing AWRAG command/core
-> meter-first progress for long work
-> evidence trace / pretty answer separation
-> receipts/reports
```

The current priority is not a new backend, not a GUI rebuild, and not evidence speech expansion.

The current priority is:

```text
keep backend behavior stable
make the operator-facing system usable without Codex
use OSRL to prevent bad work from starting
keep report tools isolated
keep distribution later
```

## Roadmap Buckets

```text
Completed / Stable
Active Operator Surface
Active Report Tools
Active Safety / OSRL
Active Intake / Laptop Lane
Deferred Evidence Speech / ClearSpeak Forms
Deferred Wide-Deep Evidence Reasoning
Deferred Exfil / Removal / Symbol Return
Deferred TrueVision / TrueAudio
Deferred SecureCore Action Map
Deferred Generation Memory
Deferred Distribution Packaging
```

## Completed / Stable

These are current stable foundations:

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
question cloud preflight report tool
answer cloud reform report tool
native-aware score/rank report docs
benchmark miss-forensics reports
wide-deep evidence reasoning documented
AWRAG agent onboarding doctrine
human companion system explanation
```

Rules:

- Preserve these unless a specific bug is proven.
- Do not replace working paths with new architecture.
- Do not mutate scoring, symbol behavior, citation authority, count files, coordinates, or lifetime memory during roadmap work.
- Keep tests and receipts as the proof layer.

## Active Operator Surface

Purpose: make the working system usable without hiding what it is doing.

Current shell:

```text
awrag-operator
python -m awrag.operator_shell
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
- Make docs good enough that a human can run common operations without Codex.

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

## Active Report Tools

Purpose: investigate evidence shape without changing retrieval, scoring, or backend behavior.

Current active report lanes:

```text
Question Cloud Preflight
Answer Cloud Reform
Native-aware formula/rank-key report
Subject generalization reports
Benchmark miss forensics
Special-search receipts
```

Report-tool law:

```text
report tools may inspect
report tools may classify from computed components
report tools may write compact reports/receipts
report tools may not mutate production evidence
report tools may not become retrieval authority
```

Question Cloud Preflight:

```text
benchmark questions
-> dataset cloud fit check
-> approve unchanged / suggest reshape / human review
-> no retrieval
-> no answering
```

Current receipt:

```text
300 questions processed
244 approved unchanged
20 suggested changes
36 human review
no search
no topK
no answering
no model
```

Answer Cloud Reform:

```text
existing AW output
-> cited blocks only
-> document-only readable answer
-> evidence trace separated from pretty answer
```

Current receipt on changed-question set:

```text
CLEAN_SUPPORTED_ANSWER: 10
BENCHMARK_MISMATCH: 6
NO_SUPPORT_FOUND: 4
RELATED_BUT_UNSUPPORTED: 0
HUMAN_REVIEW: 0
```

Hard rule:

```text
AW may speak from cited blocks.
AW may not speak beyond cited blocks.
```

Output separation rule:

```text
evidence_trace/ = citations, snippets, rank keys, receipts
pretty_answer/ = readable answer only
```

## Active Safety / OSRL

Purpose: audit operator input before AWRAG responds or acts.

Locked distinction:

```text
OSRL audit = what kind of operator input is this, and is AW allowed to act?
Evidence audit = what does admitted data prove?
```

Current OSRL v0 route classes include command, evidence demand, ambiguity, vent, destructive lock, correction, and system-shape law handling.

Supporting docs:

```text
docs/OSRL_OPERATOR_STATE_REASONING_LAYER.md
docs/reports/osrl_v0/OSRL_V0_RECEIPT.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

## Planned: Input Cloud Coherence Gate

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

Supporting docs:

```text
docs/POST_LEXICON_SCAFFOLD_LOOP_V0_ROADMAP.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
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

## Deferred TrueVision / TrueAudio

Status:

```text
separate system notes may live trapped in repo
deferred
not wired into AWRAG runtime
```

Purpose:

```text
witness state
log state
profile behavior
plan replay
surface media
receipt everything
```

Rules:

- TrueVision/TrueAudio are witness lanes, not evidence authority.
- Generated media is synthetic surface, not source evidence.
- Codex builds tools; Codex does not become the media artist.
- Open-source libraries may be tool bodies later.
- SecureCore must approve tool use when that lane exists.

Tracked note:

```text
truevision_engineering/TRUEVISION_ENGINEERING_ROADMAP.md
```

## Deferred SecureCore Action Map

Status:

```text
design lane only
not implemented in AWRAG
```

Purpose:

```text
available actions
required inputs
outputs
mutation rights
unsafe combinations
help map
code pointers
receipts
```

Contextual help law:

```text
If the operator can see it, the operator can ask what it is.
If the operator can touch it, the operator can ask what it does.
```

Examples:

```text
/inspect citation:AWCIT...
/inspect score:183.84
/help command:/laptop
/explain anchor:GUI
/source receipt:run_receipt.json
```

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

## Release / Runtime Cleanup Before Distribution

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

## Current Next Move

Next documentation-only move:

```text
turn the CLI/operator docs into a use-without-Codex runbook
```

Next implementation move, only after explicit approval:

```text
implement Input Cloud Coherence Gate inside OSRL front gate
```

Do not start distribution, evidence speech, exfil, graph export, or backend refactor before the operator safety lane and human-operable CLI docs are locked.
