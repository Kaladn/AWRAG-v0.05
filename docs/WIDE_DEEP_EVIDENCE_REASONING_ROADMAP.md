# Wide-Deep Evidence Reasoning Roadmap

Purpose: define the next evidence-speech layer without changing retrieval, scoring, citations, or intake behavior yet.

This is roadmap/design only until a later implementation pass is explicitly approved.

## Core Law

AWRAG should not collapse every question into one expected path.

It should inspect the full evidence field:

```text
not one variable
not one expected answer
not one obvious path
not one panic move

look wider
look deeper
compare consequences
separate support from pressure
separate truth from label
separate useful evidence from expected evidence
```

The question is not only:

```text
What is the top match?
```

The better field audit is:

```text
What field did the question create?
What field did the expected answer assume?
What evidence did AW actually find?
What nearby fields exist?
What is missing?
What contradicts?
What changes if we follow another strong path?
What consequence does each interpretation create?
```

## Native Rank-Key Foundation

Native AWRAG topK position is controlled by the current sort key:

```text
direct_hit_count desc
density_score desc
score desc
block_ordinal asc
```

The evidence-speech layer must expose the native key instead of inventing a new authority.

Every answer candidate should be able to show:

```text
candidate_rank
direct_hit_count
density_score
score
block_ordinal
citations
coordinates
```

## Algorithm 1: Wide Field Expansion

Purpose: inspect the surrounding evidence field, not only rank-1.

Input:

```text
Q = question / claim
K = top candidates
O = order depth 1..6
```

Build:

```text
FQ = question field
FK1 = rank-1 field
FK3 = top-3 field
FK5 = top-5 field
FK10 = top-10 field
```

For each K and order:

```text
expand anchors by native 6-1-6 count traversal
record:
  direct_hit_count
  density_score
  score
  block_ordinal
  citations
  coordinates
  drift
  repeated relations
  new relations
  missing query anchors
```

Output:

```text
wide_field_map = {
  strongest direct field,
  nearby support fields,
  drift fields,
  contradiction candidates,
  unsupported value fields
}
```

## Algorithm 2: Deep Proof Burden Walk

Purpose: force each possible answer field to show what it can and cannot support.

For each candidate field:

```text
Can it support the exact claim?
Can it support only a related claim?
Does it contain the relation?
Does it contain the value?
Does it contain the correct population/context?
Does it contradict another candidate?
Does it merely share anchors?
```

Status outputs:

```text
exact_support_candidate
related_evidence_exact_value_absent
same_subject_weak_support
contradiction_candidate
no_support
```

Law:

```text
A close paper is not automatically proof.
A gold label is not automatically truth.
No support is a valid finding.
```

## Algorithm 3: Expected-vs-Actual Field Audit

Purpose: explain benchmark misses without assuming the benchmark gold is truth or assuming AW is right.

Input:

```text
Q = question
G = expected/gold doc
A = AW rank-1
K = AW topK
```

Compare:

```text
Q <-> A
Q <-> G
A <-> G
Q <-> K
K <-> A
K <-> G
```

Fields:

```text
field overlap
relation overlap
value overlap
frame overlap
native rank key comparison
citation support
drift
```

Allowed classifications:

```text
AW better evidence field
AW better field, exact support absent
true AW miss
no support evidence found
gold/question mismatch candidate
unclear / human review
```

## Algorithm 4: Consequence Field Traversal

Purpose: classify what happens if AW answers from each candidate field.

For each answer option:

```text
support = proof support
missing = missing required evidence
contradiction = contradiction pressure
drift = drift pressure
citation = citation strength
```

Then classify the allowed consequence:

```text
exact supported answer
narrow related answer
contradiction report
no support refusal
unclear / human review
```

This is how AW decides what kind of answer is legally allowed by admitted evidence.

## Algorithm 5: Answer Form Selector

AW should not use one answer mode for every field.

Form selection:

```text
if exact_support_candidate:
  FORM_SUPPORTED_CLAIM

if related_evidence_exact_value_absent:
  FORM_RELATED_BUT_UNSUPPORTED

if contradiction_candidate:
  FORM_EVIDENCE_SPLIT

if no_support:
  FORM_NO_SUPPORT

if gold_question_mismatch:
  FORM_BENCHMARK_MISMATCH

if unclear:
  FORM_HUMAN_REVIEW
```

Example starters:

```text
SUPPORTED:
"The strongest admitted evidence supports the claim because..."

RELATED BUT UNSUPPORTED:
"I found related evidence, but not support for the exact claim..."

EVIDENCE SPLIT:
"The evidence field separates into two competing frames..."

NO SUPPORT:
"I cannot support this from admitted evidence..."

BENCHMARK MISMATCH:
"The expected document does not carry the strongest evidence field for the question as phrased..."
```

This is evidence-controlled speech, not model-owned answer generation.

## Algorithm 6: Missing Evidence Detector

Missing evidence is a finding, not a failure to hide.

Required missing markers:

```text
required relation missing
required value missing
required population missing
required outcome missing
required citation missing
```

Example:

```text
Claim:
5 percent of perinatal mortality is due to low birth weight

Finding:
low birth weight <-> neonatal mortality field found
exact 5 percent contribution value not found
therefore exact claim unsupported
```

## Full Pipeline

```text
QUESTION
  -> Build Question Field
  -> Native 6-1-6 TopK
  -> Expose Rank Key
  -> Wide Field Expansion
  -> Deep Proof Burden Walk
  -> Expected-vs-Actual Audit if benchmark/gold exists
  -> Consequence Traversal
  -> Answer Form Selection
  -> ClearSpeak Evidence Output
  -> Receipt
```

Formula:

```text
Speakable Answer =
Native Ranked Evidence
+ Wide Field Context
+ Deep Proof Burden
+ Consequence Classification
+ Citation Coordinates
- Unsupported Claims
- Drift
```

## First Implementation Target

Do not implement until the operator explicitly approves the next algorithm pass.

Candidate module:

```text
src/awrag/engine/wide_deep_reasoning.py
```

Candidate functions:

```text
build_question_field()
build_candidate_field()
compare_fields_bidirectional()
compute_native_rank_key_trace()
detect_missing_support()
classify_evidence_consequence()
select_answer_form()
write_reasoning_receipt()
```

Rules:

```text
Do not change retrieval behavior.
Do not change scoring behavior.
Do not change citation authority.
Do not add model judges.
Do not add embeddings.
Do not use hardcoded case wins.
Classifications must come from computed fields.
```

## First Case Targets

These are test targets, not hardcoded outcomes.

Target 1:

```text
SciFact Q1280
AW doc 29214508
Gold doc 4387784
```

Expected kind of investigation:

```text
native key comparison
AW field vs gold field
urease maturation / gene cluster frame support
answer form candidate = benchmark mismatch / AW better evidence field if computed evidence supports it
```

Target 2:

```text
Perinatal mortality / low birth weight claim
```

Expected kind of investigation:

```text
mortality / low birth weight field
exact value support check
answer form candidate = related evidence, exact value unsupported if computed evidence supports it
```

## Principle

AW should be a decision-rights machine:

```text
Can I answer?
Can I only answer narrowly?
Should I refuse?
Should I show contradiction?
Should I report benchmark mismatch?
Should I ask for human review?
```

That is the wide/deep evidence reasoning layer.
