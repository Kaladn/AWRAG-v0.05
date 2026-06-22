# AWRAG Human Companion

This document explains the system shape in plain language for a human reader. It is not an implementation plan and it is not a promise that every future feature is complete today.

## What AWRAG Is

AWRAG is the current proving lane for AnchorWorks.

It is not a chatbot, not a normal RAG demo, and not an LLM wrapper. It is a local evidence system that tries to make data inspectable before language happens.

The simple idea is:

```text
data comes in
anchors/symbols are assigned
relationships are counted
citations and coordinates are preserved
queries return evidence packets
answers must cite what supports them
unsupported claims are refused or labeled
```

AWRAG is where these ideas are being tested because benchmark-style datasets make the wins and misses easy to inspect.

## Why It Exists

Most AI products focus on producing fluent answers.

AnchorWorks starts earlier. It asks:

```text
What evidence was admitted?
Where did it come from?
What exact block supports the claim?
What score/rank key put this result first?
What is missing?
What cannot be answered from this data?
```

The goal is not to sound smart. The goal is to show the evidence path.

## The Core Difference

AWRAG does not treat a document title or benchmark label as proof.

A document can be related without supporting the claim. A benchmark gold document can be weak or mismatched. A model can sound confident while missing the evidence.

AWRAG tries to separate these cases:

```text
clean support
related but unsupported
contradiction
no support found
question appears malformed
benchmark expected document is weaker than another source
human review needed
```

That is why it keeps receipts.

## What A Receipt Means

A receipt is the proof trail for an operation.

Depending on the operation, a receipt may include:

```text
input question
candidate rank
native score/rank key
citation id
document id
line or block coordinates
support class
output file path
run metadata
```

The receipt is more important than the pretty answer. The pretty answer helps a human read the result. The receipt proves where it came from.

## Evidence And Pretty Answers Are Separate

AWRAG should keep two lanes:

```text
evidence trace = source blocks, citations, rank keys, receipts
pretty answer = readable human phrasing derived from cited blocks
```

The pretty answer should never become the evidence authority. It is a presentation of evidence, not a replacement for it.

## How A Question Should Work

A clean AWRAG-style question flow looks like this:

```text
question
-> question cloud preflight
-> retrieval/evidence packet
-> native score/rank key
-> cited blocks
-> support class
-> document-only readable answer
-> receipt
```

Question Cloud Preflight checks whether the question itself fits the dataset field before retrieval. It can approve the original question, suggest a safer shape, or mark it for human review.

Answer Cloud Reform takes existing cited blocks and forms a readable answer without retrieving again and without model invention.

## What Native Ranking Means

AWRAG ranking is not based on vibes.

The current exposed rank key is:

```text
direct_hit_count desc
density_score desc
score desc
block_ordinal asc
```

The native weight number is `score`, but rank is produced by the full key. A strong report should show all of those fields, not just the final position.

## Why Benchmarks Can Be Tricky

Traditional benchmarks often ask:

```text
Did the system retrieve the labeled document?
```

AWRAG asks a deeper question:

```text
Did the system find the strongest supporting evidence field, and does the cited block actually support the claim?
```

Sometimes those agree. Sometimes they do not.

AWRAG miss forensics exists to tell the difference between a real miss and a benchmark/question/evidence mismatch.

## Main Pieces In The Larger System

### AnchorWorks

AnchorWorks is the larger evidence, count, language, and operator-facing system. It owns anchors, symbols, lexicons, count lattice, citations, coordinates, native rank keys, and document-only evidence answers.

### AWRAG

AWRAG is the current test surface. It proves the behavior with datasets, questions, citations, and benchmark comparisons.

### SecureCore

SecureCore is governance. It controls tool permissions, mutation gates, approvals, adapter rules, and action receipts.

### TrueVision / TrueAudio

TrueVision and TrueAudio are witness lanes. They observe, log, replay, and surface state. They do not create truth and do not replace AnchorWorks.

## Operator Safety

The operator surface should not blindly execute every sentence.

The Operator State Reasoning Layer, or OSRL, is meant to classify input first:

```text
task
vent
system correction
evidence demand
destructive command
malformed voice input
ambiguous instruction
```

If a voice input says `DUI` but the active work is about `GUI`, the system should stop and ask for confirmation before doing work.

## Tool Safety

Tools are not free-thinking workers.

Each tool should have:

```text
one purpose
one input contract
one output contract
one mutation boundary
one receipt
one approval path
```

The tool performs its declared job and returns a receipt. It does not invent authority.

## What Is Deferred

Some important ideas are future work, not current runtime authority:

```text
GPU acceleration
SecureCore action maps
TrueVision media tooling
full lifetime memory promotion
headless application contracts
wide-deep evidence reasoning
speech forms beyond current document-only reform
```

Deferred does not mean rejected. It means not allowed to pretend it is already complete.

## The Final Shape

The target system is:

```text
one operator chat surface
visible command cards
keyboard shortcuts
side windows/tools when useful
AnchorWorks evidence memory
SecureCore governance
TrueVision/TrueAudio witness lanes
receipts everywhere
```

The operator should be able to drop data, inspect shape, ask questions, see support, see missing support, promote admitted evidence, run tools through approval gates, and export evidence packets.

## Plain-English Law

The system is the admitted data.

If it does not know, it should say it does not know.

If support is absent, it should say support is absent.

If evidence exists, it should show the path.
