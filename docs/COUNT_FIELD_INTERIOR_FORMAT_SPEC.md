# Count Field Interior Format Spec

Status: design contract. Do not implement binary changes from this document without a separate approved patch.

Purpose: define the next native count-file shape for AWRAG/AW without replacing the current working `.awbin` backend.

## Core Law

```text
Counts are the brain.
Blocks are witnesses.
Speech is form.
Evidence remains authority.
```

The count architecture must not become an external text/search index.

The index belongs inside or directly alongside the count field as access lanes over counted relationships.

## Current Backend Preservation

Current AWRAG count files remain valid and must not be destroyed:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

Current record shapes:

```text
anchor_counts:
  symbol: 6 bytes
  observations: uint64

relation_counts:
  center_symbol: 6 bytes
  neighbor_symbol: 6 bytes
  offset: int16
  observations: uint32

block_anchor_postings:
  symbol: 6 bytes
  block_ordinal: uint32
  position: uint16
```

This spec is an enhancement path, not a replacement order.

## Required Future Shape

A future count-field container should support:

```text
header
symbol namespace receipt
section directory
symbol totals
positional neighbor counts
center-symbol access ranges
neighbor-symbol reverse access ranges
block/source/position postings
dataset/source custody receipts
```

Critical distinction:

```text
records = what was counted
access ranges = how to walk what was counted
```

## Proposed Container Sections

### 1. Header

Required fields:

```text
magic
format_version
symbol_system
symbol_bytes
dataset_id_hash
window_left
window_right
section_count
created_at_epoch
receipt_hash
```

### 2. Section Directory

Purpose: allow fast jumps without scanning the full file.

Each row:

```text
section_id
record_size
record_count
offset_start
offset_end
content_hash
```

### 3. Symbol Totals

Purpose: answer "how often does this symbol exist in this dataset?"

Record:

```text
symbol
total_observations
first_block_ordinal
last_block_ordinal
first_position
last_position
```

### 4. Positional Neighbor Counts

Purpose: store cohabitation accounting.

Record:

```text
center_symbol
neighbor_symbol
offset
observation_count
```

Meaning:

```text
neighbor_symbol lived at offset N from center_symbol this many times
inside this dataset field.
```

This is the "tractor trailer" / "U-Haul trailer" accountant.

### 5. Center-Symbol Access Ranges

Purpose: allow direct walking from a center symbol into its neighborhood.

Record:

```text
center_symbol
relation_record_start
relation_record_count
total_neighbor_observations
strongest_neighbor_symbol
strongest_neighbor_count
```

Question answered:

```text
Who lives with this symbol, at what offsets, and how strongly?
```

### 6. Neighbor-Symbol Reverse Access Ranges

Purpose: allow reverse lookups.

Record:

```text
neighbor_symbol
reverse_record_start
reverse_record_count
total_center_observations
strongest_center_symbol
strongest_center_count
```

Question answered:

```text
Where does this symbol appear as someone else's neighbor?
```

### 7. Block / Source / Position Postings

Purpose: preserve witness trails.

Record:

```text
symbol
block_ordinal
position_in_block
source_id
line_start
line_end
```

This section does not make documents the brain.

It makes documents witnesses for counted relationships.

### 8. Relation Witness Trails

Optional but strongly useful for overview output.

Record:

```text
center_symbol
neighbor_symbol
offset
block_ordinal
center_position
neighbor_position
```

Purpose:

```text
relationship overview
-> concrete source trail
-> citation/coordinate proof
```

### 9. Receipts

Required receipt payload hash:

```text
source hashes
dataset manifest hash
symbol allocation receipt hash
anchorization law hash
window parameters
record counts
build command
worker/resource receipt
```

## Overview Output Requirement

People do not only want exact retrieval.

They need overviews of what the data field says.

The count field must be able to produce:

```text
top anchors by observation
top cohabitation pairs
strongest local neighborhoods
rare but exact relationships
field drift / high-noise anchors
source trails for overview claims
```

The overview answer should not be a model summary.

It should be:

```text
count-derived structure
+ witness links
+ cautious human-readable report
```

## Speech Field Boundary

The subject count field decides what may be said.

The speech count field may shape how it is said.

Speech field cannot add unsupported subject claims.

```text
subject counts decide truth
speech counts decide form
receipts prove custody
reasoning binds truth to form
```

## No Fake Promotion Rule

Do not build native count records from:

```text
top-k context JSON
resonance score
rank
pretty answer text
LLM output
```

Native counts require:

```text
raw source text
or
raw observation rows:
  center_symbol / neighbor_symbol / offset / observation_count
```

If raw observations are absent:

```text
write adapter/debug artifacts only
block native count promotion
preserve receipt
```

## Migration Strategy

Do not replace current `.awbin` files immediately.

Safe sequence:

```text
1. Keep current count files.
2. Add report-only overview/link-trail tools over current files.
3. Add resident read-only access maps in memory.
4. Define and test enhanced container format on tiny fixtures.
5. Prove equivalence with current query/rank behavior.
6. Only then consider promotion.
```

## First Non-Reasoning Tool

Before reasoning engines, build:

```text
dataset overview with source trails
```

It should read existing counts and postings and write:

```text
overview_summary.json
overview_summary.md
anchor_overviews.jsonl
relationship_trails.jsonl
run_receipt.json
no_mutation_receipt.json
```

This proves:

```text
counts can explain the field
without changing retrieval
without model reasoning
without fake summaries
```
