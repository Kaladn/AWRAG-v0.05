# AWRAG Query Math And Code Glossary

## Purpose

This glossary maps the current AWRAG codebase by process stage and names which tools are callable.

The central point:

```text
The query must do math before AW speaks.
```

Speech is downstream of evidence.
Evidence is downstream of query math.
Query math is downstream of dataset-local counts.

## Query Math Spine

The current live query path is:

```text
question
-> index readiness gate
-> anchorize
-> expand query anchors
-> count query anchors
-> read dataset blocks
-> read block-anchor postings
-> walk relation counts
-> score candidate blocks
-> sort top candidates
-> qualify evidence
-> build answer packet
-> deterministic readable answer
-> forensic receipt
```

Primary implementation:

```text
src/awrag/engine/querying.py
```

Before query math runs, AWRAG verifies:

```text
index_status = INDEX_READY
query_allowed = true
```

If the index is missing, empty, stale, or inconsistent, query stops with `INDEX_NOT_READY`.

## The Actual Query Math

### 0. Index Readiness Gate

File:

```text
src/awrag/engine/storage.py
```

Function:

```text
index_readiness()
```

Law:

```text
No index, no questioning.
```

Canonical MD/block text is the citation surface.
Native count/index artifacts are the query surface.
Speech is downstream of the packet.

### 1. Question Anchors

```python
q_anchors = expand_query_anchors(anchorize(question))
q_counter = Counter(q_anchors)
```

The question becomes anchors. The query is not model-owned.

### 2. Relation Neighbor Math

Function:

```text
top_relation_neighbors()
```

Uses:

```text
counts/relation_counts.awbin
```

Math shape:

```text
for each relation row:
  if center anchor is in the question:
    neighbor_score += observations * question_anchor_count
```

Query anchors and stop anchors are blocked from becoming relation-neighbor suggestions here.

Output:

```text
top relation neighbors, usually limit 16
```

### 3. Candidate Weight Construction

Function:

```text
score_blocks()
```

Direct question anchors get strong weight:

```text
direct anchor weight += 80 * question_anchor_count
```

Relation-neighbor anchors get smaller descending weight:

```text
neighbor weight += max(1, 4 - index // 4)
```

So query terms are the spine. Relation neighbors are support pressure.

### 4. Document Frequency Adjustment

For each anchor hit in a block:

```text
adjusted_weight = weight / sqrt(document_frequency)
```

This reduces over-common anchors.

### 5. Block Score

For each candidate block:

```text
block_score += adjusted_weight
```

This is the native score field exposed in packets:

```text
score
```

### 6. Density Score

The score is normalized by block size:

```text
density_score = score / sqrt(block_anchor_count)
```

This prevents giant blocks from winning just because they contain many anchors.

### 7. Direct Hit Count

For each block:

```text
direct_hit_count = count of direct question symbols found in that block
```

This is sorted before density and raw score.

### 8. Native Sort Key

The live topK rank key is:

```text
direct_hit_count desc
density_score desc
score desc
block_ordinal asc
```

Important:

```text
score is the native weight number.
rank is produced by the full sort key.
```

So a lower raw score can rank higher if it has better direct hits or better density.

## Evidence Qualification

File:

```text
src/awrag/engine/qualification.py
```

Purpose:

```text
candidate blocks
-> required terms
-> coverage
-> reject reasons
-> qualified locations
```

This is not the same as query ranking.
It is the evidence gate after candidate math.

Important output:

```text
answer_packet.qualification
answer_packet.qualification_receipts
```

Speech must respect these receipts.

## Speech Layer Position

Files:

```text
src/awrag/nlp_resolver.py
experiments/aw_packet_speech.py
experiments/answer_cloud_reform.py
experiments/clearspeak_map_speaker.py
```

Speech does not own evidence.
Speech does not rerank.
Speech does not search.

Correct speech pipeline:

```text
evidence packet
-> cited blocks
-> qualification receipts
-> answer form
-> pretty_answer
-> evidence_trace
```

Promoted callable speech command:

```text
awrag packet-speech --packet <query-output.json> --out <speech-output-folder>
```

Boundary:

```text
no retrieval rerun
no topK rerun
no intake
no model reasoning
```

Current law:

```text
qualified cited support controls the answer form
expanded-anchor noise stays in trace
wider/deeper context verifies the edge
wider/deeper does not speak unless it adds cited support
```

## Process Map

### Dataset Setup

```text
src/awrag/engine/base.py
src/awrag/engine/storage.py
```

Role:

```text
paths
schemas
protected notice
dataset folders
binary record formats
status
read/write helpers
```

### Anchor And Symbol Identity

```text
src/awrag/engine/anchors.py
```

Role:

```text
text -> anchors
anchors -> dataset 6-byte symbols
query anchor expansion
symbol collision checks
```

### Intake

```text
src/awrag/engine/pipeline.py
```

Role:

```text
source files
-> blocks
-> anchors
-> dataset lexicon
-> anchor counts
-> relation counts
-> block-anchor postings
-> citations
-> coordinates
```

Output count backend:

```text
awrag_native_binary_counts@1
```

### Query

```text
src/awrag/engine/querying.py
```

Role:

```text
question
-> count math
-> topK candidate blocks
-> qualification
-> answer packet
-> final answer
-> forensic receipt
```

This is where the query earns its answer.

### Evidence Gate

```text
src/awrag/engine/qualification.py
```

Role:

```text
candidate block
-> significant required terms
-> coverage
-> reject reasons
-> qualified evidence
```

### Answer Resolver

```text
src/awrag/nlp_resolver.py
```

Role:

```text
answer packet locations
-> best cited sentence
-> deterministic readable answer
```

No model search.
No invented citations.

### Forensic Receipt

```text
src/awrag/engine/forensic.py
```

Role:

```text
answer packet + final answer
-> conservative support ladder
-> supported / not-supported receipt
```

### Batch Questions

```text
src/awrag/engine/querying.py
```

Role:

```text
questions.txt
-> repeated query()
-> per-question packet JSON
-> batch_run_summary.json
```

### Determinism Receipts

```text
src/awrag/engine/determinism.py
```

Role:

```text
repo state
dataset artifact hashes
query packet hashes
raw packet comparison receipts
```

### Codex Chat Staging

```text
src/awrag/engine/codex.py
```

Role:

```text
Codex JSONL or Markdown export
-> AWRAG chat-turn markdown
```

This prepares chat data for normal intake.

### Chat Metadata Filters

```text
src/awrag/engine/chat.py
```

Role:

```text
chat metadata block
-> timestamps / speaker
-> query filtering
```

### Citation Crosslinks

```text
src/awrag/engine/crosslinks.py
```

Role:

```text
left dataset query
right dataset query
-> shared anchor comparison
-> crosslink rows
```

### Special Search

```text
src/awrag/engine/special_search.py
```

Role:

```text
JSON trigger list
-> anchor search
-> hit expansion
-> mini local counts
-> temporal causality graph
-> reports
```

This is a callable tool lane, not core query.

### Laptop Temp Intake

```text
src/awrag/engine/laptop_temp_intake.py
```

Role:

```text
source file/folder
-> bounded chunks
-> chunk-local symbols
-> chunk-local counts
-> receipts
```

This is an isolated sidelane.
It does not replace production intake.
It does not merge into dataset counts.

### Read-Only UI Bridge

```text
src/awrag/ui_read_bridge.py
src/awrag/ui_server.py
```

Role:

```text
status
manifest
lexicon search
anchor detail
anchor locations
count backend status
symbol system status
protected notice
```

Read-only inspection only.

### Operator Shell

```text
src/awrag/operator_contract.py
src/awrag/operator_shell.py
src/awrag/operator_state/
```

Role:

```text
chat-first terminal cockpit
slash command registry
OSRL input audit
command cards
locked future commands
```

## Callable CLI Tools

Main executable:

```text
awrag
python -m awrag.cli
```

### Active Commands

```text
awrag init
```

Creates a dataset-local scope.

```text
awrag intake
```

Builds dataset-local lexicon, counts, coordinates, and citations.

```text
awrag status
```

Shows dataset-local status and count file paths.

```text
awrag query
```

Runs the query math and returns a cited local answer packet.

```text
awrag batch
```

Runs many questions through the existing query path.

```text
awrag stage-codex
```

Stages Codex JSONL sessions as markdown.

```text
awrag stage-codex-md
```

Stages visible Codex Markdown export as AWRAG chat-turn markdown.

```text
awrag crosslink
```

Builds citation crosslinks between two dataset-local scopes.

```text
awrag special-search
```

Runs JSON-list driven trigger/special search reports.

```text
awrag determinism
```

Writes twin-machine determinism receipts.

```text
awrag operator-state-audit
```

Audits operator input without executing commands.

```text
awrag laptop-temp-intake
```

Runs isolated laptop-safe chunk prep with resource receipts.

## Operator Shell Commands

Executable:

```text
awrag-operator
python -m awrag.operator_shell
```

Command prefix must be at the start of live operator input.

```text
/intake      Ctrl+I
/query       Ctrl+Q
/batch       Ctrl+B
/status      Ctrl+S
/laptop      Ctrl+L
/receipts    Ctrl+R
/settings    Ctrl+,
/help        Ctrl+H
/quit        Ctrl+X
```

Locked command:

```text
/exfil       Ctrl+E
```

Reason:

```text
action bridge not enabled
```

## Experiments And Tool Lanes

These are not the core backend unless explicitly promoted.

```text
experiments/aw_packet_speech.py
```

Reads existing AW query packets and writes separate evidence trace and pretty answer files.

Promoted callable:

```text
awrag packet-speech
```

```text
experiments/answer_cloud_reform.py
```

Benchmark/report-side answer reform from existing AW outputs.

```text
experiments/question_cloud_preflight.py
```

Question-shape audit before retrieval.

```text
experiments/clearspeak_map_speaker.py
```

Experimental map-speaker using loaded count lattice and evidence frames.

```text
experiments/generation_lexicon.py
experiments/generation_binary.py
experiments/anchor_speech_assembly.py
```

Experimental generation helper and anchor-first speech assembly.

```text
experiments/trigger_anchor_*.py
experiments/bad_phrase_*.py
experiments/mini_local_counts.py
experiments/temporal_causality_graph.py
experiments/hit_expander.py
```

Trigger/special-search research lanes for hit expansion, local counts, and temporal graph receipts.

```text
experiments/scaffold_*.py
```

Self-scaffold learning research lane.

```text
experiments/resident_dataset_tap.py
experiments/aw_backend_tap.py
```

Read-only dataset/backend tap experiments.

## Tests As Guardrails

```text
tests/test_awrag_dataset_local.py
```

Core dataset, query, citation, model flag, refusal, batch behavior.

```text
tests/test_aw_packet_speech.py
```

Packet speech split, refusal, weak evidence, qualification-term behavior.

```text
tests/test_question_answer_report_tools.py
```

Question preflight and answer cloud reform report tools.

```text
tests/test_generation_binary_and_speech.py
tests/test_generation_lexicon.py
```

Generation helper and anchor-first speech safety.

```text
tests/test_clearspeak_map_speaker.py
```

Experimental loaded map speaker.

```text
tests/test_operator_shell.py
tests/test_operator_state_audit.py
```

Operator cockpit and OSRL audit.

```text
tests/test_laptop_temp_intake.py
```

Laptop-safe isolated intake lane.

```text
tests/test_ui_read_bridge.py
tests/test_ui_server.py
```

Read-only UI bridge/server.

```text
tests/test_repo_hygiene.py
```

Repo cleanliness and forbidden artifact checks.

## Bottom Line

Yes, AW still does math for the query.

The query answer is earned through:

```text
anchor counts
relation counts
block-anchor postings
document-frequency adjustment
block scoring
density scoring
direct hit priority
qualification receipts
citations and coordinates
```

Then speech is allowed to read the admitted packet and talk like a careful third grader:

```text
simple
cited
qualified
refuses when support is weak
keeps evidence trace separate from pretty answer
```
