# Roadmap GPT Correction Trace

Status: roadmap context only. No implementation changes are implied by this document.

Purpose: preserve the operator reasoning pattern that corrected the GPT-side framing and turned it into AWRAG roadmap work.

## Core Correction Pattern

The operator correction pattern was:

```text
GPT frames the work as a familiar AI/RAG concept
-> operator rejects the weak frame
-> operator names the actual system law
-> AWRAG roadmap gets the corrected lane
```

This is not argument for argument's sake.

It is architecture defense.

## Correction 1: Benchmark Retrieval Is Not An Answer

Weak benchmark frame:

```text
question
-> retrieve the labeled document
-> count it as success
```

Operator correction:

```text
The user did not ask for a document.
The user asked a question.
If the system only points to a document, the user still has to do the answer work.
```

Correct AWRAG frame:

```text
question
-> cited document block
-> document-only answer
-> citation lines
-> rank key
-> receipt
```

Roadmap result:

```text
Benchmark Answer Standard
```

Benchmarks should distinguish:

```text
document found
answer formed from cited content
support actually present
rank key / citation receipt attached
```

## Correction 2: Chat Memory Is Pre-Action History, Not Nostalgia Retrieval

Weak memory frame:

```text
find me something later
```

Operator correction:

```text
memory is checking what already happened before we act again
```

Correct AWRAG frame:

```text
new operator input
-> OSRL/input cloud check
-> memory travel check
-> did we already do this?
-> what result survived?
-> what failed?
-> what was corrected?
-> act, refuse, continue, or warn
```

Roadmap result:

```text
Memory Travel Gate / Pre-Action History Check
```

This belongs after OSRL and Input Cloud Coherence, before command execution.

## Correction 3: Answer Form Is Presentation, Not Evidence

Weak output frame:

```text
one answer format for everyone
```

Operator correction:

```text
Evidence stays deterministic.
Speech form is selectable.
Receipts always exist, but receipts do not always have to be spoken.
```

Correct AWRAG frame:

```text
same evidence packet
-> plain_speech
-> operator_card
-> receipt_detail
-> developer_debug
-> benchmark_report
-> evidence_packet
```

Roadmap result:

```text
Answer Form Profiles
```

Plain speech matters because some operator contexts are listening-first, not screen-reading-first.

## Correction 4: GPU Count Field Is Accelerator, Not Authority

Weak acceleration frame:

```text
GPU lane becomes a new brain or new authority
```

Operator correction:

```text
GPU comes later, after enough data exists.
It accelerates count/matrix experiments.
It does not replace deterministic evidence/citations.
```

Correct AWRAG frame:

```text
CPU/file-backed evidence core remains authority
GPU count field may accelerate experiments later
deterministic source and receipts remain available on demand
```

Roadmap result:

```text
Deferred GPU Count Field Accelerator Lane
```

## Locked Product Laws

```text
The system is the admitted data.
The answer must come from cited content, not document pointing alone.
Memory checks history before action.
Presentation form is selectable.
Receipts always exist.
Receipts do not always have to be spoken.
Acceleration never replaces evidence authority.
```

## Roadmap Placement

These corrections feed the current roadmap as:

```text
Active Safety / OSRL
-> Input Cloud Coherence Gate
-> Memory Travel Gate

Deferred Evidence Speech / ClearSpeak Forms
-> Answer Form Profiles
-> Document-only cited answer reform

Deferred Benchmark Standard
-> answer correctness beyond document hit

Deferred Accelerator Lane
-> GPU count-field experiments only after stable receipts
```
