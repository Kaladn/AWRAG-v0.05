# AWRAG Whole Repo Map Glossary

## Purpose

This document maps the whole AWRAG repo by process role.

It answers:

```text
Do we still do math for the query?
What does every code file do?
Where is each file in the process?
What tools are built in?
Which tools are callable?
```

## Short Answer

Yes. AWRAG still does math for the query.

The query is not a text lookup followed by speech.

The live path is:

```text
question
-> index readiness gate
-> anchors
-> symbols
-> relation count walk
-> block-anchor posting scan
-> native score
-> density score
-> direct hit count
-> native sort key
-> evidence qualification
-> cited answer packet
-> speech/report layer
```

Speech comes after the math.

Query is blocked unless:

```text
index_status = INDEX_READY
query_allowed = true
```

Core law:

```text
No index, no questioning.
```

## Dataset And Symbol Foundation

Current planning law:

```text
Dataset-local evidence.
Global symbol uniqueness.
No symbol collision.
No silent merge.
```

The target ingest foundation is:

```text
source data
-> dataset folder
-> canonical blocks
-> block-local coordinates
-> anchors
-> globally unique symbols
-> dataset lexicon
-> native counts/index
-> citations/coordinates
-> receipts
-> query allowed only after index readiness
```

Current implementation gap:

```text
src/awrag/engine/anchors.py
```

The current dataset-symbol path derives symbols from anchor text. The next ingest foundation requires a persisted global monotonic symbol allocator so symbols never collide or repeat across datasets.

Planning authority:

```text
docs/DATASET_FOLDER_AND_GLOBAL_SYMBOL_ALLOCATOR_LAW.md
```

## Native Query Math

Primary file:

```text
src/awrag/engine/querying.py
```

The query creates anchors:

```text
anchorize(question)
expand_query_anchors(...)
Counter(...)
```

After the index readiness gate passes, AWRAG reads native dataset counts:

```text
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
state/dataset_lexicon.json
blocks/blocks.jsonl
```

Direct question anchors get strong candidate weight:

```text
80 * question_anchor_count
```

Relation neighbors add support pressure:

```text
max(1, 4 - index // 4)
```

Document-frequency adjustment reduces over-common anchors:

```text
adjusted_weight = weight / sqrt(document_frequency)
```

Candidate score:

```text
score += adjusted_weight
```

Density score:

```text
density_score = score / sqrt(block_anchor_count)
```

Native topK sort key:

```text
direct_hit_count desc
density_score desc
score desc
block_ordinal asc
```

Important:

```text
score = native weight number
rank = result of the full sort key
```

## Process Stages

### 1. Repo Setup / Packaging

```text
pyproject.toml
```

Defines package name `awrag`, version `0.05`, dependency on `tqdm`, and CLI entrypoints:

```text
awrag = awrag.cli:main
awrag-operator = awrag.operator_shell:main
```

```text
README.md
```

Human-facing project overview and contract.

```text
LICENSE
NOTICE
SECURITY.md
CONTRIBUTING.md
PACKAGE_BUILD.txt
READ_FIRST.txt
```

Public review, package, security, and handoff docs.

```text
AnchorWorks_Reviewer_Demo.code-workspace
```

VS Code workspace wrapper.

### 2. Operator / Agent Instructions

```text
AGENTS.md
ARCHITECTURE_GUARDRAILS.md
WORK_LEDGER.md
CHECKPOINT.md
AWRAG_NEXT_WORK_PLAN.md
CHANGELOG_UPDATES.md
```

Repo operating contract, architectural guardrails, work history, and next-work planning.

### 3. Launch / Install Scripts

```text
Install_To_Local.ps1
Run_From_USB.ps1
Start_AWRAG_CLI.ps1
Launch_AWRAG_CLI.cmd
Start_Laptop_Temp_Intake.ps1
```

Operator launch and setup scripts.

Process role:

```text
outside Python package
-> launch/install helper
-> operator convenience
```

### 4. Main Package

```text
src/awrag/__init__.py
```

Package marker.

```text
src/awrag/cli.py
```

Main `awrag` command dispatcher.

Callable commands:

```text
init
intake
laptop-temp-intake
status
query
packet-speech
batch
stage-codex
stage-codex-md
crosslink
special-search
determinism
operator-state-audit
```

### 5. Core Engine

```text
src/awrag/engine/__init__.py
```

Exports core engine functions for CLI, tests, and tools.

```text
src/awrag/engine/base.py
```

Constants, dataset paths, dataset symbol settings, count backend name, protected notice, safe IDs, timestamps, JSON writer.

Key constants:

```text
SYMBOL_SYSTEM = awrag_dataset_6b@1
COUNT_BACKEND = awrag_native_binary_counts@1
```

```text
src/awrag/engine/anchors.py
```

Anchor extraction, anchor normalization, query expansion, dataset symbol assignment, symbol collision checks.

Process role:

```text
raw text/question
-> anchors
-> symbols
```

```text
src/awrag/engine/storage.py
```

Dataset folder creation, status, index readiness gate, binary record formats, native `.awbin` reads/writes, lexicon, blocks, citations, coordinates, chat metadata index.

Process role:

```text
dataset runtime filesystem
-> native binary counts
-> JSON/JSONL readable sidecars
```

```text
src/awrag/engine/pipeline.py
```

Production intake.

Process role:

```text
source files
-> blocks
-> anchors
-> lexicon
-> native counts
-> citations
-> coordinates
```

```text
src/awrag/engine/querying.py
```

Query math and batch query path.

Process role:

```text
question
-> count math
-> ranked candidate blocks
-> qualification
-> answer packet
-> final answer
-> forensic receipt
```

```text
src/awrag/engine/qualification.py
```

Evidence gate after candidate ranking.

Process role:

```text
candidate blocks
-> required terms
-> coverage
-> rejection reasons
-> qualified locations
```

```text
src/awrag/engine/forensic.py
```

Builds conservative support ladder receipt from answer packet and final answer.

Process role:

```text
answer packet
-> support ladder
-> supported / not-supported receipt
```

```text
src/awrag/engine/chat.py
```

Parses chat metadata and applies date/speaker filters to query blocks.

Process role:

```text
chat blocks
-> timestamp/speaker metadata
-> query filter
```

```text
src/awrag/engine/codex.py
```

Stages Codex session exports into AWRAG chat-turn markdown.

Process role:

```text
Codex JSONL or Markdown
-> staged markdown
-> normal AWRAG intake source
```

```text
src/awrag/engine/crosslinks.py
```

Builds citation crosslinks between two dataset-local scopes.

Process role:

```text
left query + right query
-> shared anchor comparison
-> crosslink rows
```

```text
src/awrag/engine/determinism.py
```

Twin-machine determinism receipts.

Process role:

```text
repo state
dataset artifact hashes
query packet hashes
-> determinism receipt
```

```text
src/awrag/engine/special_search.py
```

Locked JSON-list special search path.

Process role:

```text
trigger JSON
-> solo anchor search
-> expanded context
-> mini local counts
-> temporal causality graph
-> reports
```

```text
src/awrag/engine/laptop_temp_intake.py
```

Isolated laptop-safe chunk lane.

Process role:

```text
source files
-> bounded chunks
-> chunk symbols
-> chunk-local counts
-> receipts
```

Does not replace production intake.
Does not merge into dataset counts.

### 6. Speech / Answer Formation

```text
src/awrag/nlp_resolver.py
```

Deterministic resolver that selects readable cited sentences from admitted packet locations.

Process role:

```text
answer packet locations
-> readable cited answer
```

No model search.
No invented citations.

```text
experiments/aw_packet_speech.py
```

Report-only packet speech tool.

Process role:

```text
existing AW query packet
-> evidence_trace
-> pretty_answer
-> no-mutation receipts
```

This is promoted to the main CLI:

```text
awrag packet-speech
```

It remains report-only and does not run retrieval, topK, intake, or model reasoning.

```text
experiments/answer_cloud_reform.py
```

Report-side answer reform from benchmark/comparison artifacts and existing AW outputs.

Process role:

```text
existing AW output
-> document-only readable answer
-> evidence trace / pretty answer split
```

```text
experiments/clearspeak_map_speaker.py
```

Experimental loaded-map speaker.

Process role:

```text
dataset count lattice
-> relation cloud
-> candidate evidence frames
-> normal surface answer
```

This loads native `.awbin` artifacts read-only and writes experiment receipts.

```text
experiments/generation_lexicon.py
experiments/generation_binary.py
experiments/anchor_speech_assembly.py
```

Generation helper lane.

Process role:

```text
AW lexicon
-> generation lexicon
-> generation binary
-> anchor-first speech assembly
```

These are not evidence authority. They help surface construction only.

### 7. Operator Shell / OSRL

```text
src/awrag/operator_contract.py
```

Slash command registry, hashes, shortcuts, command cards.

Process role:

```text
operator command text
-> registered command
-> command card
```

```text
src/awrag/operator_shell.py
```

Terminal-first chat/operator shell.

Process role:

```text
live operator input
-> OSRL audit
-> slash command card or conversation audit response
```

```text
src/awrag/operator_state/__init__.py
```

Exports OSRL functions.

```text
src/awrag/operator_state/anchors.py
```

Operator input anchor group extraction.

```text
src/awrag/operator_state/rules.py
```

Operator mode scoring, routing, and system output rules.

```text
src/awrag/operator_state/modes.py
```

Operator mode definitions.

```text
src/awrag/operator_state/schemas.py
```

OSRL schema constants.

```text
src/awrag/operator_state/audit.py
```

OSRL audit entrypoint.

Process role:

```text
raw operator input
-> deterministic audit
-> mode/routing/receipt
```

### 8. Read-Only UI Surface

```text
src/awrag/ui_read_bridge.py
```

Read-only bridge for status, manifest, lexicon search, anchor detail, anchor locations, count backend status, symbol system status, protected notice.

Process role:

```text
UI request
-> read existing AWRAG facts
-> display payload
```

No action bridge.
No count logic.
No citation authority.

```text
src/awrag/ui_server.py
```

Minimal read-only HTTP server around the read bridge.

Process role:

```text
browser/static UI
-> read-only API endpoints
-> JSON display
```

### 9. Experiments / Research Tools

These are not core backend unless promoted later.

```text
experiments/aw_backend_tap.py
experiments/resident_dataset_tap.py
```

Read-only taps over backend/dataset artifacts.

```text
experiments/question_cloud_preflight.py
```

Question cloud audit before retrieval.

```text
experiments/mini_local_counts.py
experiments/hit_expander.py
experiments/temporal_causality_graph.py
```

Small local count and temporal graph helpers for special-search style reports.

```text
experiments/trigger_anchor_seed.py
experiments/trigger_anchor_search.py
experiments/trigger_anchor_temporal_causality.py
experiments/trigger_receipts.py
```

Trigger-anchor search, hit expansion, temporal causality receipts.

```text
experiments/bad_phrase_law_suite.py
experiments/bad_phrase_search.py
experiments/bad_phrase_temporal_causality.py
```

Bad-phrase trigger/law search lane.

```text
experiments/scaffold_records.py
experiments/scaffold_receipts.py
experiments/scaffold_primer_questions.py
experiments/scaffold_loop_v0.py
experiments/scaffold_grader.py
experiments/scaffold_crosslinks.py
```

Self-scaffold learning research lane.

```text
experiments/conversation_generation_datasets.json
```

Reference list for future conversation-shaped generation data sources.

### 10. Tests

Tests are guardrails for contracts.

```text
tests/test_awrag_dataset_local.py
```

Core dataset-local behavior, intake/query/citations/refusal/model flags/batch.

```text
tests/test_aw_packet_speech.py
```

Packet speech split, refusal, weak evidence, AW qualification-term behavior.

```text
tests/test_question_answer_report_tools.py
```

Question preflight and answer cloud reform report tools.

```text
tests/test_generation_lexicon.py
tests/test_generation_binary_and_speech.py
```

Generation helper and anchor-first speech safety.

```text
tests/test_clearspeak_map_speaker.py
```

Loaded map speaker experiment.

```text
tests/test_operator_shell.py
tests/test_operator_state_audit.py
```

Operator shell and OSRL behavior.

```text
tests/test_laptop_temp_intake.py
```

Laptop-safe chunk lane isolation and receipts.

```text
tests/test_ui_read_bridge.py
tests/test_ui_server.py
```

Read-only UI bridge/server.

```text
tests/test_codex_markdown_adapter.py
```

Codex markdown staging adapter.

```text
tests/test_trigger_anchor_temporal_causality.py
tests/test_bad_phrase_temporal_causality.py
tests/test_bad_phrase_law_suite.py
```

Trigger/bad phrase search and temporal report lanes.

```text
tests/test_scaffold_loop_modules.py
```

Self-scaffold experiment modules.

```text
tests/test_repo_hygiene.py
```

Repo cleanliness and forbidden residue checks.

### 11. Backup

```text
backups/engine_20260620_pre_modular_split.py
```

Historical backup of the older monolithic engine shape before modular split.

Not active runtime.

### 12. External TrueVision Notes

```text
<host-data-root>\data_intake\truevision_engineering\TRUEVISION_ENGINEERING_ROADMAP.md
<host-data-root>\data_intake\truevision_engineering\TRUEVISION_HEADLESS_EFFECTS_TOOLCHAIN_ROADMAP.md
```

External note/scaffold area for another named system.

Not AWRAG runtime.
Not wired into AWRAG backend.

## Built-In Callable Tools

### Package CLI

Callable:

```text
awrag
python -m awrag.cli
```

Commands:

```text
awrag init
awrag intake
awrag laptop-temp-intake
awrag status
awrag query
awrag packet-speech
awrag batch
awrag stage-codex
awrag stage-codex-md
awrag crosslink
awrag special-search
awrag determinism
awrag operator-state-audit
```

### Operator CLI

Callable:

```text
awrag-operator
python -m awrag.operator_shell
```

Slash commands:

```text
/intake
/query
/batch
/status
/laptop
/receipts
/settings
/help
/quit
```

Locked:

```text
/exfil
```

Reason:

```text
action bridge not enabled
```

### Direct Experiment Tools

Callable directly with Python where a `main()` exists:

```text
python experiments/aw_packet_speech.py
python experiments/answer_cloud_reform.py
python experiments/question_cloud_preflight.py
python experiments/clearspeak_map_speaker.py
python experiments/trigger_anchor_temporal_causality.py
python experiments/bad_phrase_temporal_causality.py
python experiments/scaffold_loop_v0.py
```

These are tool lanes, not production backend replacements.

Note:

```text
aw_packet_speech.py is also promoted through awrag packet-speech.
The script remains the implementation/tool lane entry.
```

### Launch Scripts

Callable:

```text
Install_To_Local.ps1
Run_From_USB.ps1
Start_AWRAG_CLI.ps1
Launch_AWRAG_CLI.cmd
Start_Laptop_Temp_Intake.ps1
```

## Documentation Map

### Current System / Plans

```text
AWRAG_NEXT_WORK_PLAN.md
docs/POST_LEXICON_SCAFFOLD_LOOP_V0_ROADMAP.md
docs/WIDE_DEEP_EVIDENCE_REASONING_ROADMAP.md
docs/OSRL_OPERATOR_STATE_REASONING_LAYER.md
docs/OPERATOR_UI_CONTRACT.md
docs/LAPTOP_TEMP_INTAKE.md
docs/AWRAG_CLI_OPERATOR_GUIDE.md
docs/AWRAG_HUMAN_COMPANION.md
```

### Speech / Answer / Edge Rules

```text
docs/EDGE_CASE_SNIFFING_LAW.md
docs/AWRAG_QUERY_MATH_AND_CODE_GLOSSARY.md
docs/AW_PACKET_DIFF_FORMS_V1.md
docs/ROADMAP_GPT_CORRECTION_TRACE.md
```

### Review / Reports

```text
docs/review_packets/
docs/reports/
RELEASE_GATE_REPORT.md
UI_BACKEND_DIFF_REPORT.md
UI_BRIDGE_PLAN.md
```

### Runtime / Replication

```text
docs/RUNTIME_FOLDER_CONTRACT.md
docs/TWIN_MACHINE_REPLICATION_PLAYBOOK.md
docs/SPECIAL_SEARCH_CLI_INSTRUCTIONS.md
docs/CANONICAL_CHAT_DATASET_2026-06-20.md
```

## Boundaries

Core backend:

```text
src/awrag/engine/
src/awrag/cli.py
src/awrag/nlp_resolver.py
```

Operator surface:

```text
src/awrag/operator_*
```

Read-only UI:

```text
src/awrag/ui_*
```

Experiments:

```text
experiments/
```

Tests:

```text
tests/
```

Docs:

```text
docs/
*.md
```

Other-system notes moved outside repo:

```text
<host-data-root>\data_intake\truevision_engineering\
```

## Final Law

The answer path must keep this order:

```text
math first
evidence second
speech third
receipt always
```

If speech appears without query math and cited evidence, it is not AW speaking.
