# Count-Walk Speech v0

Status: active tool lane; not final ClearSpeak.

Purpose:

```text
question
-> existing AW query path
-> count-ranked TopK evidence block
-> block_anchor_postings local spine
-> native relation counts choose local continuation
-> rough anchor-speech output
-> evidence trace and receipts
```

This is the missing limb between retrieval paste and freeform language.

It is not a reasoning engine.

It is not an LLM.

It is not a replacement for query ranking.

## Law

```text
Retrieval selects evidence.
Counts choose continuation pressure.
Block postings constrain speech locality.
Documents prove custody.
Speech does not create evidence.
```

Short form:

```text
Counts create the walk.
Blocks constrain the walk.
Citations prove the walk.
```

## CLI

```text
awrag count-walk-speech
  --runtime-root <runtime>
  --dataset <dataset>
  --question "<question>"
  --out <folder>
  --starter "<optional starter>"
  --top-k 5
  --max-steps 50
  --branch-k 5
```

## Outputs

```text
evidence_trace/count_walk_trace_<id>.json
pretty_answer/count_walk_speech_<id>.md
receipts/run_receipt.json
receipts/no_mutation_receipt.json
```

The evidence trace is authority.

The pretty answer is a rough operator view.

## What v0 Proves

v0 proves that AW can walk a count-selected local spine without using document
text as the speech body.

Every step shows:

```text
from anchor
branch candidates
native relation count
chosen candidate
chosen rule
source citation
rank key of the selected block
```

## What v0 Does Not Prove

v0 does not prove final readable speech.

v0 does not prove reasoning.

v0 does not prove overview synthesis.

v0 does not prove semantic correctness beyond the selected evidence spine.

## Refusal

If an operator provides a starter and that starter is not found inside the
count-selected local spine, the tool refuses the walk:

```text
starter_not_found
```

That prevents a starter from forcing speech outside the evidence field.

## Next Layer

The next layer is not broader retrieval.

The next layer is answer framing:

```text
count-walk speech trace
-> answer frame
-> support gate
-> final ClearSpeak candidate
```

That step belongs after resident runtime, symbol allocation, and anchor law
settle enough that the walk can be fast and trustworthy.
