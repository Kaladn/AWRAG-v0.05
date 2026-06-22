# AWRAG Agent Onboarding

Purpose: give future Codex/agent sessions the system shape before they touch code, docs, data, or runtime artifacts.

Source doctrine: Cortex Evolved / AnchorWorks System Shape.

## One-Line Identity

AWRAG is the current proving lane for AnchorWorks, a local evidence operating system. It is not a chatbot, not a normal RAG stack, and not an LLM wrapper.

The system exists to make evidence inspectable.

## Core Job

An agent working here must protect this flow:

```text
admit data
assign anchors
count relationships
preserve citations
show native scores
produce receipts
answer only from evidence
refuse when evidence is absent
govern actions through tool boundaries
```

The system does not exist to sound smart. It exists to show what admitted data supports, where it supports it, and what cannot be supported.

## Evidence Laws

Do not treat these as optional preferences:

```text
A document is not an answer.
A citation without support is not proof.
A benchmark gold doc is not automatically truth.
A model answer is not authority.
Evidence must carry source, coordinate, score, and support class.
```

The machine must be able to say:

```text
I found support here.
I found related evidence, but not exact support.
I found contradiction.
I found no support.
The expected document is weaker than another source.
The question itself appears malformed.
I cannot answer from admitted evidence.
```

## Main System Boundaries

### AnchorWorks

AnchorWorks is the evidence, language, count, and operator-facing layer.

It owns:

```text
anchors
symbols
lexicon
count lattice
citations
coordinates
native rank keys
document-only evidence answers
operator chat surface
```

AnchorWorks admits data, turns it into anchors/symbols, counts relationships, and produces evidence-backed output.

### AWRAG

AWRAG is the current public/demo/proving lane for AnchorWorks. It is not the entire final product.

AWRAG currently proves:

```text
native ranking
question cloud preflight
answer cloud reform
document-only cited answers
benchmark miss forensics
support/no-support classification
operator command cards
CLI operator flow
```

Do not blur AWRAG with the private lifetime system. AWRAG is a front door and test surface.

### SecureCore

SecureCore is governance.

It owns:

```text
tool permission
action gates
mutation boundaries
approval receipts
adapter controls
security posture
```

SecureCore does not retrieve data, answer questions, or become count memory. It controls agency.

### TrueVision / TrueAudio

TrueVision and TrueAudio are witness systems.

They observe state, log state, replay state, and surface media from state logs and tools. They do not create truth and do not replace AnchorWorks.

TrueVision law:

```text
witness state
log state
profile behavior
plan replay
surface media
receipt everything
```

Generated media is a synthetic surface, not source evidence.

## Agency Network Law

Do not build free-thinking agent mazes.

This system uses an agency network:

```text
one tool
one purpose
one input contract
one output contract
one mutation boundary
one receipt
one approval path
```

A tool cannot invent new authority. A tool cannot do more than its declared action. SecureCore decides whether tools may run. AnchorWorks decides what evidence/context justifies requesting them. The tool performs the action and returns a receipt.

## Data Is The System

The system is whatever is admitted into it.

Bad data makes a bad system. Clean admitted data makes a stronger system.

Long-term shape:

```text
raw data
-> intake
-> question/cloud quality check
-> anchor/symbol assignment
-> citation/coordinate preservation
-> count lattice
-> evidence packet
-> optional promotion into lifetime counts
```

Lifetime memory is not magical memory. It is admitted evidence that can be found again with citations.

## Chat Memory Law

Chat memory is pre-action history, not nostalgia retrieval.

Before repeating work, the system should ask:

```text
Did we already do this?
What result survived?
What failed?
What was corrected?
What was the final decision?
What date/context did it belong to?
```

Memory Travel Gate:

```text
operator input
-> OSRL/input cloud check
-> memory travel check
-> command/evidence/action
```

## OSRL Conversation Front Gate

OSRL is the Operator State Reasoning Layer. It is not psychology and does not mirror emotion.

It classifies operator input before action:

```text
What kind of input is this?
Is it a task?
A vent?
A destructive command?
A system correction?
An evidence demand?
A malformed instruction?
A low-fit anchor from voice input?
```

OSRL belongs in the conversation front gate. It does not execute commands by itself.

## Input Cloud Coherence Gate

This catches malformed operator input before work starts.

Example:

```text
raw transcript: DUI nightmare
active cloud: CLI, GUI, operator shell, interface cleanup
likely intended anchor: GUI
```

Correct behavior:

```text
Anchor `DUI` does not fit the active interface cloud.
Did you mean `GUI`?
```

Rule:

```text
extract anchors
compare to active task cloud
find low-fit disruptor anchors
suggest correction if safe
block execution until operator confirms
```

## Question Cloud Preflight

Benchmark questions are not automatically clean.

Before retrieval, AnchorWorks may inspect the question itself:

```text
extract anchors
compare against dataset cloud
find low-fit anchors
find missing expected anchors
approve unchanged
suggest reshape
or mark human review
```

This is diagnostic. It is not silent rewriting.

Current receipt to preserve:

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

## Answer Cloud Reform

Answer Cloud Reform takes existing AW outputs and cited blocks, then reforms them into readable document-only answers.

It does not retrieve again. It does not use a model. It does not invent support. It speaks only from cited blocks.

Current receipt to preserve on the 20 changed-question set:

```text
CLEAN_SUPPORTED_ANSWER: 10
BENCHMARK_MISMATCH: 6
NO_SUPPORT_FOUND: 4
RELATED_BUT_UNSUPPORTED: 0
HUMAN_REVIEW: 0
```

Core rule:

```text
AW may speak from cited blocks.
AW may not speak beyond cited blocks.
```

## Benchmark Miss Forensics

Do not treat benchmark labels as final truth.

A benchmark miss may be:

```text
true AW miss
AW better evidence field
gold/question mismatch
related but exact support absent
no support found
malformed question
human review needed
```

Better standard:

```text
question
-> answerability check
-> exact supporting content
-> citation/coordinate
-> support class
-> contradiction/missing support
-> native score/path
-> receipt
```

## Native Rank Key

Current exposed native ranking key:

```text
direct_hit_count desc
density_score desc
score desc
block_ordinal asc
```

The native AW weight number is:

```text
score
```

Rank is produced by the full key, not score alone.

Reports must show:

```text
candidate rank
direct_hit_count
density_score
score
block_ordinal
citation
document id
support class
```

## Evidence And Presentation Must Stay Separate

Evidence packet and pretty answer are different artifacts.

Same evidence packet can be shown as:

```text
plain_speech
operator_card
receipt_detail
developer_debug
benchmark_report
evidence_packet
legal_style
medical_review
household_plain
```

Important law:

```text
Receipts always exist.
Receipts do not always have to be spoken.
```

Plain speech matters. Some users listen while driving or working. Do not bury important information only inside tables, YAML, or code blocks unless requested.

## Contextual Help Law

If the operator can see it, the operator can ask what it is.

If the operator can touch it, the operator can ask what it does.

CLI/chat examples:

```text
/inspect citation:AWCIT...
/inspect score:183.84
/help command:/laptop
/explain anchor:GUI
/source receipt:run_receipt.json
```

Every visible output element should be inspectable.

## Headless Action Map Direction

AI should not replace serious software. AI should operate serious software through declared headless contracts.

A proper headless application exposes:

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

Menu/help generated from code belongs in the SecureCore action-map/product lane.

## GPU Law

GPU is deferred. It is an accelerator, not authority.

CPU/file-backed evidence remains the authority. Acceleration never replaces source, citation, coordinate, or receipt authority.

## TrueVision Headless Effects Direction

When TrueVision work resumes, do not hand-code videos. Use open-source video/vision libraries as headless tool bodies.

Possible tool bodies:

```text
FFmpeg
OpenCV
Blender headless
Natron/OpenFX
MLT
```

Rule:

```text
outside AI authority is not allowed
open-source libraries are allowed as tools
Codex builds tools
Codex does not become the media artist
TrueVision remains witness/planner
SecureCore approves tool use
```

## Refactor Meaning

Refactor means:

```text
same behavior
cleaner structure
clearer boundaries
less duplicated logic
better names
obvious command paths
consistent receipts
tests protecting behavior
dead junk removed
```

Refactor does not mean:

```text
new features
silent behavior changes
backend redesign
scoring changes
intake rule changes
distribution packaging
```

Short version:

```text
same machine, cleaner skeleton
```

## Release Goal

Near-term release goal: clean repo that selected people can inspect.

Release repo must have:

```text
no private data
no benchmark corpora checked in
small demo examples
short docs
clear CLI
runtime folders ignored
receipt examples
tests green
operator guide
architecture guide
```

Docs must be short and load-bearing. No giant README.

Docs should answer:

```text
What is this?
Why does it exist?
How do I run it?
Where does data go?
What does it output?
What are receipts?
What is not implemented yet?
```

## Agent Operating Rules

When working in this repo:

1. Inspect before changing.
2. Preserve existing native paths before creating new ones.
3. Keep data, evidence, and presentation separated.
4. Do not mutate counts, citations, coordinates, or lifetime memory unless explicitly asked.
5. Do not introduce model authority, embeddings, rerankers, or hidden scoring.
6. Do not treat benchmark expected docs as unquestioned truth.
7. Do not mix adjacent systems into AWRAG runtime.
8. Keep adjacent system notes trapped and clearly marked if they must live in this repo.
9. Produce receipts for actions.
10. Stop when the operator says stop.

## Final Law

```text
The system is the admitted data.
The system does not lie.
If it does not know, it says it does not know.
If support is absent, it says support is absent.
If evidence exists, it shows the path.
```
