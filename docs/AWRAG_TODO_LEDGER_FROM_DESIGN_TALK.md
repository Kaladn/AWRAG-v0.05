# AWRAG TODO Ledger From Design Talk

Status: planning / TODO ledger.

Purpose: turn the latest count-field / speech-field design discussion plus current test-phase repo ideas into one actionable queue.

This document is not an implementation patch.

## Core Correction

AWRAG is not primarily a document search tool.

The working description is:

```text
symbolic cohabitation accounting
```

The production brain is not the exploded 6-1-6 JSON map.

The production brain is the compressed count field:

```text
center_symbol
neighbor_symbol
offset
observation_count
dataset/source custody
```

The JSON/map view is useful for learning, inspection, debugging, and proof.

It is not the runtime format to keep forever at scale.

## Locked Architecture Law

```text
Subject counts decide truth.
Speech counts decide form.
Receipts prove custody.
Reasoning binds truth to form.
```

Supporting law:

```text
Maps show layout.
Counts store lived relationships.
TopK comes from relationship strength.
Documents prove where relationships were witnessed.
Glyph words are display.
Symbols are machine identity.
```

Do not collapse these lanes:

```text
subject field = what this dataset says
speech field = how language/conversation is shaped
evidence trace = authority
pretty answer = presentation
```

## Non-Negotiables

- Keep current AWRAG blocks, citations, coordinates, receipts, query packets, rank keys, and count files.
- Enhance existing paths; do not replace what works.
- Do not create an external search index as a second brain.
- Do not regenerate full exploded 6-1-6 maps as the runtime authority.
- Do not fake native counts from rank, resonance score, or top-k layout.
- Do not use LLM/model output as evidence.
- Do not let speech invent unsupported claims.
- Do not promote experiments into core without receipts and tests.
- Do not re-ingest production-scale data until symbol allocation and index readiness laws are satisfied.

## Immediate TODO Queue

### 1. Preserve Current Working Foundation

Status: active.

Work:

- Keep existing AW intake/count/block/citation/query behavior intact.
- Keep tests green after each slice.
- Keep runtime/generated data ignored.
- Keep evidence trace and pretty answer separate.
- Keep the CLI/operator surface as the usable front door.

Definition of done:

```text
full tests pass
no runtime data tracked
no count/citation/symbol behavior changed accidentally
```

### 2. Write Count-Interior Format Spec

Status: completed as design contract.

Need:

Design the interior access lanes for the count architecture.

Possible sections:

```text
header
dataset/symbol namespace receipt
section directory
symbol totals
positional neighbor counts
center-symbol access ranges
neighbor-symbol reverse access ranges
block/source/position pointers
receipt and ingest-rule section
```

Critical distinction:

```text
records = what was counted
indexes/access ranges = how to walk what was counted
```

Definition of done:

```text
docs/COUNT_FIELD_INTERIOR_FORMAT_SPEC.md
schema examples
read/write invariants
no code until approved
```

Receipt:

```text
docs/COUNT_FIELD_INTERIOR_FORMAT_SPEC.md
```

### 3. Promote Resonance Sample Safely

Status: adapter lane validated; true count promotion blocked until raw counts/source exist.

Current adapter output:

```text
resonance_anchor_records.jsonl
dataset_symbol_lexicon.json
resonance_symbol_records.jsonl
resonance_context_edges.jsonl
resonance_cloud_edges.jsonl
binary_count_readiness_receipt.json
```

Current blocker:

```text
saved resonance JSON contains top-k positional layout and resonance strengths,
not raw observation counts per center/offset/neighbor.
```

TODO:

- Locate original story/source text or raw count table.
- If source text exists, rebuild true raw observations from source.
- If raw count table exists, convert directly to native count records.
- If neither exists, keep resonance output as adapter-local debug/learning data only.

Definition of done:

```text
raw observation source found OR blocker preserved
no fake .awbin counts
adapter remains side lane
```

Receipt:

```text
docs/RESONANCE_SAMPLE_PROMOTION_DECISION_20260623.md
```

### 4. Build Count-Derived Dataset Overview With Link Trails

Status: completed as non-reasoning operator tool.

Purpose:

```text
existing native counts
-> top anchors
-> top cohabitation relationships
-> source/citation trails
-> compact overview reports
```

This gives people an overview of what lives in the dataset without turning
overview into an answer authority or reasoning engine.

Implemented:

```text
src/awrag/engine/dataset_overview.py
awrag dataset-overview
tests/test_dataset_overview.py
```

Outputs:

```text
overview_summary.json
overview_summary.md
anchor_overviews.jsonl
relationship_trails.jsonl
receipts/run_receipt.json
receipts/no_mutation_receipt.json
```

Boundaries:

```text
no query
no intake
no model
no reasoning engine
no count mutation
no evidence invention
```

Definition of done:

```text
overview command works from existing count/block/citation artifacts
source trails are written
no-mutation receipt is written
focused tests pass
full suite passes
```

### 5. Implement Global Monotonic Symbol Allocator

Status: planned; required before clean re-ingest.

Source doc:

```text
docs/DATASET_FOLDER_AND_GLOBAL_SYMBOL_ALLOCATOR_LAW.md
```

Current gap:

```text
src/awrag/engine/anchors.py currently uses SHA-derived symbols.
Same anchor across datasets can reuse the same symbol.
```

Required:

```text
global allocator state
assigned range receipts
dataset-local lexicon from assigned symbols
collision/overlap fail-closed checks
index readiness verifies symbol receipts
```

Definition of done:

```text
two datasets with same anchor receive different symbols
ranges never overlap
allocator resumes after restart
query blocks missing symbol receipts
```

### 6. Resolve Anchorization Law Conflict

Status: known code/law mismatch.

Current code:

```text
anchorize() applies STOP_ANCHORS and normalization
```

Operator law discussed:

```text
all anchors count
no stop words as hidden removal
```

TODO:

- Decide final production anchorization law.
- If all anchors count, remove stop-anchor filtering in a separate approved slice.
- Preserve display/search convenience separately from machine counting.
- Rebuild tests around the final law.

Definition of done:

```text
anchorization law documented
code/tests match law
no hidden stop-word removal if law says all anchors count
```

### 7. Validate Dataset Cloud Gate On Real Questions

Status: active behavior now exists in live query path.

Purpose:

```text
question
-> dataset cloud gate
-> refuse if the question does not belong to the dataset field
-> only then TopK
```

TODO:

- Run a small real-question set across SciFact / chat / repo docs.
- Record false positives and false refusals.
- Preserve gate receipts.
- Do not weaken gate from one anecdote.

Definition of done:

```text
dataset_cloud_gate false-refusal cases logged
valid mismatch cases logged
policy adjusted only from receipts
```

### 8. Build Resident Count Runtime V0

Status: experiment exists; not promoted.

Relevant experiment:

```text
experiments/resident_dataset_tap.py
```

Purpose:

```text
load .awbin once
keep read-only hot structures in RAM
answer many
avoid per-question binary crawl
```

Rules:

- Read-only lock.
- No mutation while loaded.
- Use resource budgets.
- No laptop full-corpus resident load unless data fits comfortably.

Definition of done:

```text
resident load receipt
memory estimate
query equivalence against normal path
unload/close behavior
```

### 9. Define Subject Field / Speech Field Binding

Status: primary design need.

Goal:

```text
subject field chooses truth
speech field chooses how to say it
```

TODO:

- Define input/output contract for binding subject evidence to speech shape.
- Define refusal when speech field wants to exceed subject support.
- Define receipt that proves subject evidence controlled the claim.
- Keep speech field from becoming answer authority.

Definition of done:

```text
SUBJECT_SPEECH_BINDING_CONTRACT.md
first tiny fixture
support/refusal examples
no LLM
```

### 10. Build Tiny Conversation Speech Field Test

Status: next proof after binding contract.

Need:

Use a tiny conversational corpus to teach form only.

Flow:

```text
conversation source
-> speech-field counts
-> question/answer shape
-> subject evidence packet
-> grounded response form
```

Rules:

- Conversation data teaches form, not truth.
- Subject data supplies claims.
- Citations remain tied to subject evidence.

Definition of done:

```text
one question
one subject evidence packet
one speech-shaped response
separate evidence_trace and pretty_answer
refusal if support absent
```

## Active/Test-Phase Ideas Inventory

These ideas exist in docs, tests, experiments, or CLI surfaces. They are not all core.

### Packet Speech

Files:

```text
experiments/aw_packet_speech.py
tests/test_aw_packet_speech.py
```

Role:

```text
existing AW packet
-> evidence trace
-> pretty answer
```

TODO:

- Keep as report/tool lane.
- Do not let it become answer authority.
- Later bind it to count-selected local spine and subject/speech fields.

### Answer Cloud Reform

Files:

```text
experiments/answer_cloud_reform.py
tests/test_question_answer_report_tools.py
```

Role:

```text
existing answer artifacts
-> document-only readable reform
-> classification
```

TODO:

- Keep report-only.
- Use findings to design answer forms.
- Do not replace query output until approved.

### Question Cloud Preflight

Files:

```text
experiments/question_cloud_preflight.py
tests/test_question_answer_report_tools.py
```

Role:

```text
benchmark question
-> dataset cloud fit
-> approve / suggest / human review
```

TODO:

- Keep as preflight/report lane.
- Compare with live dataset cloud gate.
- Avoid silent question rewriting.

### Count-Selected Local Spine Speech

Files:

```text
src/awrag/engine/count_walk_speech.py
docs/COUNT_WALK_SPEECH_V0.md
tests/test_count_selected_local_spine_speech.py
tests/test_count_walk_speech.py
```

Role:

```text
TopK-selected block
-> block_anchor_postings local spine
-> starter match
-> local continuation
```

TODO:

- Preserve as proof of local-spine speech path.
- Keep `awrag count-walk-speech` as a rough tool lane.
- Do not treat v0 output as final ClearSpeak.
- Do not speak from global relation soup.
- Use the walk trace later as input to answer framing.

Current command:

```text
awrag count-walk-speech
```

Current boundary:

```text
query selects evidence
block postings constrain local spine
native relation counts choose continuation candidates
documents/citations prove custody
```

### ClearSpeak Map Speaker

Files:

```text
experiments/clearspeak_map_speaker.py
tests/test_clearspeak_map_speaker.py
```

Role:

```text
native count lattice / resident loaded path
-> deterministic evidence frames
```

TODO:

- Park as research lane.
- Mine for count-walk ideas.
- Do not promote until resident runtime + count interior spec are stable.

### Generation Lexicon / Generation Binary / Anchor Speech Assembly

Files:

```text
experiments/generation_lexicon.py
experiments/generation_binary.py
experiments/anchor_speech_assembly.py
tests/test_generation_lexicon.py
tests/test_generation_binary_and_speech.py
```

Role:

```text
allowed glue
forbidden claim terms
relation phrases
anchor-first speech assembly
```

TODO:

- Use as speech-field candidate pieces.
- Ensure glue cannot add claims.
- Convert from experiment into subject/speech binding tests only after contract.

### Conversation Generation Dataset Manifest

File:

```text
experiments/conversation_generation_datasets.json
```

Role:

```text
candidate conversation sources for speech-shape learning
```

TODO:

- Keep data outside git.
- Review licenses before download/use.
- Use only for speech form, never evidence authority.

### Special Search / Trigger Anchor / Bad Phrase / Temporal Causality

Files:

```text
src/awrag/engine/special_search.py
experiments/trigger_anchor_search.py
experiments/trigger_anchor_temporal_causality.py
experiments/bad_phrase_*.py
experiments/mini_local_counts.py
experiments/temporal_causality_graph.py
tests/test_trigger_anchor_temporal_causality.py
tests/test_bad_phrase_temporal_causality.py
tests/test_bad_phrase_law_suite.py
```

Role:

```text
JSON anchor list
-> solo search
-> hit expansion
-> mini-local counts
-> temporal causality graph
```

TODO:

- Keep `awrag special-search` as the locked command.
- Do not reinvent phrase logic.
- Use same runner / different lists.
- Keep output report-only unless a later learning lane consumes receipts.

### Scaffold Loop / Learning Memory

Files:

```text
experiments/scaffold_loop_v0.py
experiments/scaffold_*.py
tests/test_scaffold_loop_modules.py
docs/POST_LEXICON_SCAFFOLD_LOOP_V0_ROADMAP.md
```

Role:

```text
self-questioning
attempt memory
failure memory
correction memory
behavior memory
generation memory
```

TODO:

- Defer until resident runtime and subject/speech binding are stable.
- Do not generate child questions unless explicitly approved.
- Every attempt must write consequence memory if this lane resumes.

### Resident Dataset Tap

Files:

```text
experiments/resident_dataset_tap.py
experiments/aw_backend_tap.py
```

Role:

```text
read current AW artifacts
load native count surface once
serve fast read-only inspection
```

TODO:

- Use for resident runtime v0 design.
- Keep read-only.
- Compare output to normal query path.

### OSRL / Input Cloud / Memory Travel

Files/docs:

```text
src/awrag/operator_state/
docs/OSRL_OPERATOR_STATE_REASONING_LAYER.md
docs/ROADMAP_REFACTOR_INPUT_CLOUD_GATE.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
tests/test_operator_state_audit.py
```

Role:

```text
operator input
-> classify mode
-> block unsafe/ambiguous actions
```

TODO:

- Implement active task cloud coherence gate after approval.
- Add memory-travel gate after input cloud.
- Keep OSRL as front gate, not document search.

### Operator Shell / CLI Cockpit

Files/docs:

```text
src/awrag/operator_shell.py
src/awrag/operator_contract.py
docs/OPERATOR_UI_CONTRACT.md
docs/CLI_SHORTCUTS.md
docs/AWRAG_CLI_OPERATOR_GUIDE.md
tests/test_operator_shell.py
```

Role:

```text
human-operable command cockpit
```

TODO:

- Make commands usable without Codex.
- Keep command cards visible.
- Keep meter-first long operations.
- Route every action to explicit command receipts.

### Laptop Temp Intake

Files/docs:

```text
src/awrag/engine/laptop_temp_intake.py
Start_Laptop_Temp_Intake.ps1
docs/LAPTOP_TEMP_INTAKE.md
tests/test_laptop_temp_intake.py
```

Role:

```text
laptop-safe chunk preparation side lane
```

TODO:

- Run one real long receipt.
- Keep as side lane.
- Do not merge into production counts yet.

### Resonance Sample Adapter

Files:

```text
src/awrag/engine/resonance_adapter.py
tests/test_resonance_adapter.py
runtime/resonance_samples/
```

Role:

```text
standalone 6-1-6 resonance sample
-> adapter records
-> optional adapter-local symbols
-> binary readiness receipt
```

TODO:

- Locate original source text or raw count table.
- If found, build true observation counts.
- If not found, keep as learning/debug artifact.
- Do not fake `.awbin` from top-k/resonance.

### Native-Aware Benchmark/Miss Forensics

Files/docs:

```text
docs/reports/aw_subject_generalization_2026_06_22/
SCIFACT_STRENGTH_RANKING_LOG_2026_06_19.md
NFCORPUS_AW1_AW2_REPLICATION_LOG_2026_06_19.md
```

Role:

```text
benchmark exact hit
vs
AW evidence-field behavior
```

TODO:

- Keep as report/forensics.
- Do not mutate scoring from these findings yet.
- Use for wide/deep reasoning test cases.

### UI Read Bridge / Static HTML

Files:

```text
src/awrag/ui_read_bridge.py
src/awrag/ui_server.py
HTML UI/
tests/test_ui_read_bridge.py
tests/test_ui_server.py
```

Role:

```text
read-only inspection surface
```

TODO:

- Keep optional/deferred.
- No backend business logic in UI.
- No action bridge until explicitly approved.

### Exfil / Symbol Return

Status: visible concept, not implemented.

TODO:

- Design removal ledger before code.
- Return eligible symbols only by receipt.
- Never delete without audit trail.

### TrueVision / TrueAudio

Status: separate-system notes; not AWRAG runtime.

TODO:

- Keep trapped as notes.
- Do not wire into AWRAG.
- Move/store in separate engineering/data-intake folder when operator chooses.

## Do Not Build Yet

- Do not build native count interior changes before the format spec.
- Do not build a second text/search index.
- Do not build full speech field before the subject/speech binding contract.
- Do not run large re-ingest before global symbol allocator.
- Do not promote scaffold loop into runtime.
- Do not implement exfil/symbol return without ledger spec.
- Do not package distribution while runtime/data/pycache residue exists.
- Do not let report tools become authority.

## Best Next Sequence

```text
1. Preserve current dirty work and tests.
2. Keep COUNT_FIELD_INTERIOR_FORMAT_SPEC.md as the binary-change contract.
3. Keep resonance adapter output side-lane until raw source/count observations exist.
4. Use dataset-overview for non-reasoning overviews with source trails.
5. Implement GlobalSymbolAllocator v0.
6. Resolve anchorization law.
7. Build resident count runtime v0.
8. Define subject/speech binding contract.
9. Run tiny conversation speech-field proof.
10. Only then widen into scaffold/wide-deep/generation memory.
```

## Current Design Sentence

```text
AWRAG records how symbols live together inside admitted datasets,
uses counts to choose evidence structure,
uses documents as witnesses,
and must learn speech form without letting speech become truth.
```
