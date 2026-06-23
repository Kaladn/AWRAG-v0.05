# Index Readiness Gate

## Purpose

AWRAG may not answer questions from raw files, staged markdown, or partial runtime artifacts.

The query path must prove that the dataset index exists before questioning.

## Core Law

```text
No index, no questioning.
```

## Surface Separation

```text
canonical MD / block text
  -> evidence display surface
  -> citation surface
  -> human-readable audit surface

index / count artifacts
  -> query engine surface
  -> math surface
  -> candidate selection surface

speech
  -> downstream packet surface
```

AW does not answer because it searched markdown.

AW answers because count math selected evidence blocks.

Markdown/block text is used to display and cite what the math selected.

## Required Query Artifacts

Before query is allowed, the dataset must have non-empty:

```text
dataset_manifest.json
state/blocks.jsonl
state/dataset_lexicon.json
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
citations/citations.jsonl
coordinates/coordinate_index.jsonl
receipts/intake_*.json
```

## Runtime Status

`awrag status` reports:

```text
index_readiness
index_status
query_allowed
```

Valid ready state:

```text
index_status = INDEX_READY
query_allowed = true
```

Invalid state:

```text
index_status = INDEX_NOT_READY
query_allowed = false
```

## Query Behavior

`awrag query` must stop before reading blocks or postings if the index is not ready.

Failure shape:

```text
INDEX_NOT_READY: query_allowed=false; <reason list>
```

## What This Prevents

```text
flat-file fallback
raw markdown answering
querying staged files without intake
querying partial runtime artifacts
querying empty count files
querying stale or inconsistent index state
```

## Final Rule

```text
MD/source blocks = citation surface
index/count files = query surface
speech = downstream packet surface
```

