# OSRL Operator State Reasoning Layer

OSRL v0 is the operator conversation input gate.

It is not an evidence search tool.

It is not a document retrieval lane.

It answers:

```text
What kind of operator input is this?
What is AW allowed to do with it?
What mode should the conversation route into?
```

Evidence audit answers a different question:

```text
What does the admitted dataset prove?
```

## Current Shape

OSRL v0 exists in two safe forms:

```text
1. conversation front gate inside awrag.operator_shell
2. standalone audit command for test/debug receipts
```

Standalone command:

```powershell
python -m awrag.cli operator-state-audit --input "Show me the score and citation trace."
```

Optional receipt file:

```powershell
python -m awrag.cli operator-state-audit --input-file <input-file> --output <receipt.json>
```

## Core Law

```text
Emotion is runtime metadata, not machine feeling.
Anchors route behavior.
Receipts prove routing.
No action happens from OSRL v0.
```

## Conversation Flow

```text
raw operator input
-> OSRL audit
-> input mode
-> command card / evidence demand / vent notice / ambiguity gate / destructive lock
-> no execution unless a separate explicit command path is allowed
```

## Anchor Groups

OSRL v0 extracts:

```text
affect_anchors
command_anchors
target_anchors
risk_anchors
care_priority_anchors
ambiguity_anchors
evidence_anchors
mutation_anchors
```

## Anchor Scores

OSRL v0 computes:

```text
anger
urgency
confusion
care_priority
threat_language
destructive_intent
target_specificity
proof_burden
mutation_risk
```

## Modes

```text
TASK_MODE
VENT_MODE
BOUNDARY_MODE
AMBIGUITY_MODE
EVIDENCE_AUDIT_MODE
SYSTEM_COMMAND_MODE
DESTRUCTIVE_COMMAND_LOCK
```

## Invariants

```text
High Affect = High Proof Burden
No Inferred Destruction
Acknowledge Noise, Execute Structure
Zero Tone Feedback Loops
Anchor Before Action
No Target, No Mutation
```

## Routing Rules

```text
RULE_01_DESTRUCTIVE_HIGH_AFFECT:
destructive command + high affect -> DESTRUCTIVE_COMMAND_LOCK

RULE_02_URGENCY_MISSING_TARGET:
urgency + command + weak target -> AMBIGUITY_MODE

RULE_03_VENT_NO_COMMAND:
affect + no command -> VENT_MODE

RULE_04_CARE_VALID_SYSTEM_COMMAND:
care priority + command + target + not destructive -> SYSTEM_COMMAND_MODE

RULE_05_EVIDENCE_REQUEST:
evidence anchors -> EVIDENCE_AUDIT_MODE

RULE_06_CLEAR_TASK:
command + target + low mutation risk -> TASK_MODE
```

## Output Voice

Output must be:

```text
flat
direct
data-first
non-hostile
non-anthropomorphic
audit-only
```

Do not use:

```text
fake apology
therapy framing
tone mirroring
model-judgment language
```

## Hard Boundaries

```text
No production command execution.
No backend mutation.
No count mutation.
No lifetime memory write.
No model classifier.
No embeddings.
No model judge.
No integration into normal command execution yet.
No destructive action under any condition.
```

## Destination

OSRL's real destination is:

```text
every operator input
-> OSRL audit
-> safe route
```

The standalone CLI exists only so the routing can be tested safely before deeper shell integration.
