# Edge Case Sniffing Law

## Purpose

Edge-case sniffing is the speech-layer discipline for finding where a readable answer starts to drift away from admitted evidence.

It is not a new retrieval method.
It is not a new scorer.
It is not permission to widen the answer until it sounds better.

It is verification pressure.

## Core Law

```text
Edge-case sniffing is verification pressure, not answer expansion.
```

## Speech Rule

```text
Answer from actuals.
Use wider/deeper context to sniff the edge.
Only widen the answer if widening finds new cited support.
Otherwise keep widening in the trace, not the mouth.
```

## Normal Case

```text
qualified evidence
-> cited support
-> readable answer
-> citations/rank key/receipt
```

## Edge Sniff Cases

These are the cases that should trigger inspection before speech gets stronger:

```text
qualified evidence says yes
but speech says unsupported

speech says yes
but support is generic/noisy

wider context is present
but it does not actually support the answer

expanded anchor variants confuse the speech layer
while AW qualification receipts cover the required terms
```

## Current Lock

The speech layer must respect AW's evidence qualification receipts.

```text
qualified cited support controls the answer form
expanded-anchor noise stays in trace
wider/deeper context verifies the edge
wider/deeper does not speak unless it adds cited support
```

## Output Separation

```text
pretty_answer
  -> document-only readable speech from actual cited support

evidence_trace
  -> citations
  -> coordinates
  -> rank key
  -> qualification receipts
  -> wider/deeper verification context
  -> missing anchors / noisy anchors / edge notes
```

The pretty answer is allowed to be readable.
The evidence trace remains the authority.

## Patch Discipline

Do not expand speech features because an edge case appears.

The allowed loop is:

```text
talk to AW
inspect packet
sniff the edge case
patch only the speech contract leak
run tests
keep receipts
```

Every speech change must come from one of:

```text
packet bug
support-class bug
trace/speech separation bug
citation/coordinate visibility bug
refusal/qualification mismatch
```

## Non-Goals

```text
no backend ranking changes
no retrieval changes
no count changes
no model reasoning as evidence
no Codex-authored answer authority
no uncited answer expansion
```

