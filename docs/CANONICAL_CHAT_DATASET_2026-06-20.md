# Canonical Chat Dataset Receipt: 2026-06-20

This document records the canonical local chat dataset state used for AWRAG
chat-memory and forensic-reconstruction work on 2026-06-20.

The raw chat corpus is not committed to this repository. The repository keeps
the canonical receipt only. The admitted chat data remains dataset-local in the
operator runtime.

## Canonical Dataset

```text
dataset_id: previous_chats_chatgpt_combined
scope: dataset_local
count_backend: awrag_native_binary_counts@1
symbol_system: awrag_public_6b@1
lifetime_memory: false
promotion_allowed: false
sql_database_backend: false
```

## Source Scopes

```text
previous_chats_chatgpt_2024_12_25
previous_chats_chatgpt_2026_06_delta
```

## Append-Delta Law

```text
old dataset is preserved
new export is staged as delta
combined dataset is rebuilt from old + delta
counts are recalculated for the combined dataset
receipts must prove the count math
lifetime/user counts are not written
```

## Current Canonical Counts

```text
old staged messages: 3,077
old blocks: 31,153
old metadata rows: 31,151
old Ashley hits: 0

delta staged messages: 38,769
delta blocks: 543,684
delta metadata rows: 543,683
delta Ashley hits: 168

combined expected messages: 41,846
combined blocks: 574,837
combined metadata rows: 574,834
combined Ashley hits: 168

combined unique anchors: 119,742
combined anchor observations: 14,782,582
combined relation observations: 157,493,188
```

## Runtime Receipt Identifiers

These receipt names identify the local operator runtime receipts. They are not
repository payloads and the repo does not store operator-local absolute paths:

```text
reasoning_runs/2026-06-20/append_delta_receipts/append_delta_precount_receipt.json
reasoning_runs/2026-06-20/append_delta_receipts/append_delta_final_receipt.json
```

## Review Boundary

This canonical chat dataset is for local AWRAG retrieval, metadata narrowing,
forensic reconstruction, and doctrine archaeology. It is not world truth, not
lifetime memory, and not a global training corpus.
