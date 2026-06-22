# Roadmap Refactor Input: Input Cloud Coherence Gate

Purpose: break down the attached input into system-aligned roadmap pieces before the full roadmap refactor.

This is a staging document only.

No backend implementation is implied by this document.

## Refactor Meaning For This System

In this context, refactor does not mean changing what the system does.

It means:

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

It is not:

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

## Cleanup Spine Before Distribution

The roadmap cleanup should preserve the current proof instead of dragging a GUI nightmare forward.

Correct order:

```text
finish roadmap/to-do
preserve working proof
strip generated data
lock runtime boundaries
push clean system
then refactor into a real distributable repo
```

This is not random cleanup.

It is cleanup with receipts.

## Real Operator Environment

The operator environment is not clean-room software work.

It includes:

```text
family logistics
money pressure
house interruptions
repo commits
CLI contracts
OSRL architecture
runtime cleanup
distribution pressure
```

The system should not treat that as noise to ignore.

It should survive it by routing input correctly:

```text
vent
task
command
evidence demand
ambiguity
destructive request
system law candidate
input cloud mismatch
```

That is why OSRL belongs in the conversation front gate.

## Source Correction

The source example was a voice-input error:

```text
raw transcript anchor: DUI
intended anchor: GUI
```

Context made the raw anchor unlikely because the active work field was:

```text
CLI
GUI
operator shell
chat front door
shortcuts
side windows
interface cleanup
distribution repo
usable system surface
```

So the correct inference is:

```text
voice input misheard GUI as DUI
```

The lesson is not about that one word.

The lesson is:

```text
Do not blindly execute from malformed operator input.
Check whether the anchors fit the active task cloud before work starts.
```

## System Lane

This belongs in:

```text
OSRL conversation front gate
```

It does not belong in:

```text
evidence search
retrieval scoring
ClearSpeak answer generation
distribution packaging
production intake
```

Locked distinction:

```text
OSRL audit = what kind of operator input is this, and is it coherent enough to act on?
Evidence audit = what does admitted data prove?
```

## New Roadmap Concept

Name:

```text
Input Anchor Coherence Gate
```

Alternate name:

```text
Input Cloud Mismatch Gate
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

## Why It Matters

The system should not wait until after a bad run to discover a malformed instruction.

It should catch the mismatch before execution:

```text
input cloud does not fit
specific anchor causes mismatch
operator confirmation required
no state changes made
```

This is OSRL applied before command execution.

## Proposed OSRL Rule

Rule name:

```text
RULE_INPUT_CLOUD_MISMATCH
```

Rule shape:

```text
if input_anchor_cloud_fit < threshold
and anchor is meaning-bearing
and mismatch affects task meaning:
    selected_mode = AMBIGUITY_MODE
    action_state = BLOCKED_UNTIL_OPERATOR_CONFIRMATION
    mutation_allowed = false
```

If a correction candidate exists:

```text
suggest correction
preserve raw input
preserve corrected candidate
ask operator to confirm
```

If no correction candidate exists:

```text
warn about low-fit anchor
ask operator to clarify
do not execute
```

## Example Operator Output

With correction candidate:

```text
Input coherence warning.

Anchor `DUI` does not fit the active interface/refactor cloud.
Possible correction: `GUI`.

Confirm before I continue:
1. use `GUI`
2. keep `DUI`
3. rewrite the phrase
```

Without correction candidate:

```text
Input coherence warning.

Anchor `<anchor>` does not fit the active task cloud.
No safe correction found.
Clarify before execution.
```

## Telemetry Shape

Future OSRL receipt extension:

```json
{
  "raw_anchor": "DUI",
  "active_cloud": ["CLI", "GUI", "operator_shell", "chat", "shortcut", "interface"],
  "cloud_fit": 0.03,
  "disruptor": true,
  "suggested_anchor": "GUI",
  "suggested_anchor_fit": 0.91,
  "routing": "AMBIGUITY_MODE",
  "action_state": "BLOCKED_UNTIL_OPERATOR_CONFIRMATION",
  "payload": "Anchor `DUI` does not fit the active interface cloud. Did you mean `GUI`?"
}
```

## Roadmap Placement

This belongs under:

```text
Active Safety / OSRL
```

It should be implemented after:

```text
OSRL v0 audit gate
operator shell command cards
```

It should come before:

```text
real command execution gates
exfil actions
dangerous mutation operations
full distribution packaging
```

## Implementation Requirements

Future implementation should add:

- active conversation/task cloud
- low-fit anchor detection
- correction candidate search
- OSRL route `RULE_INPUT_CLOUD_MISMATCH`
- confirmation-required action state
- raw/corrected input receipt fields
- tests for voice-input misfire cases

## Non-Goals

Do not use this as:

- a model classifier
- an evidence search operation
- a ClearSpeak answer generator
- a command executor
- a silent autocorrect layer

The system may suggest a correction, but the operator confirms before execution.

## Acceptance Tests

Minimum future tests:

```text
Input: "DUI nightmare" during interface/refactor active cloud
Expected: AMBIGUITY_MODE, suggested_anchor = GUI, no execution

Input: "delete it all" with ambiguous target
Expected: DESTRUCTIVE_COMMAND_LOCK or AMBIGUITY_MODE, no execution

Input: "show citation trace" during evidence work
Expected: EVIDENCE_AUDIT_MODE, no correction warning

Input: low-fit anchor with no correction candidate
Expected: AMBIGUITY_MODE, clarify before execution
```

## Full Roadmap Refactor Impact

When the full roadmap is refactored, this item should appear as:

```text
OSRL v1: Input Cloud Coherence Gate
```

Status:

```text
planned
not implemented
requires active context cloud
requires confirmation gate
```

Speech/ClearSpeak items remain deferred to a later session.

## Full Roadmap Refactor Buckets

When we do the full roadmap refactor, the current working buckets should be:

```text
Completed / Stable
Active Operator Surface
Active Safety / OSRL
Active Intake / Laptop Lane
Planned Input Cloud Coherence Gate
Deferred Wide-Deep Evidence Reasoning
Deferred Evidence Speech / ClearSpeak Forms
Deferred Exfil / Removal / Symbol Return
Deferred Generation Memory
Deferred Distribution Packaging
```

Speech items stay deferred.

This staging input belongs under:

```text
Active Safety / OSRL
-> OSRL v1: Input Cloud Coherence Gate
```
