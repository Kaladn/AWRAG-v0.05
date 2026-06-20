# AW Packet Diff Forms V1

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

These forms exist so two machines compare AWRAG evidence packets before anyone
compares final answer wording.

## Law

```text
Do not compare answers first.
Compare packets first.
```

If packets match and wording differs:

```text
renderer / bot / human interpretation difference
```

If packets differ:

```text
repo / data / count / ranking / citation / scope difference
```

## AW_DIFF_REPORT_V1

Each machine fills this form independently.

```json
{
  "schema": "AW_DIFF_REPORT_V1",
  "run_id": "",
  "machine_id": "",
  "repo_commit": "",
  "branch": "",
  "git_status_short": "",
  "dataset_id": "",
  "query": "",
  "timestamp": "",
  "result": {
    "answer_summary": ""
  },
  "evidence": {
    "citations": [],
    "blocks": [],
    "documents": [],
    "coordinates": []
  },
  "supported": {
    "supported_claims": []
  },
  "partial": {
    "partial_claims": []
  },
  "unsupported": {
    "unsupported_claims": []
  },
  "conflicts": {
    "conflicts": []
  },
  "provenance": {
    "support_level": "",
    "ladder_hits": [],
    "dataset_scope": "",
    "excluded_scope": []
  },
  "retrieval": {
    "candidate_count": 0,
    "top_candidate": null,
    "top_3_candidates": [],
    "top_10_candidates": []
  },
  "artifact_hashes": {
    "raw_packet_sha256": "",
    "dataset_manifest_sha256": "",
    "dataset_lexicon_sha256": "",
    "anchor_counts_sha256": "",
    "relation_counts_sha256": "",
    "block_anchor_postings_sha256": "",
    "citations_sha256": "",
    "coordinate_index_sha256": "",
    "question_list_sha256": ""
  },
  "notes": {
    "operator_notes": ""
  }
}
```

## AW_MACHINE_DIFF_V1

This form compares two `AW_DIFF_REPORT_V1` forms.

```json
{
  "schema": "AW_MACHINE_DIFF_V1",
  "left_run": "",
  "right_run": "",
  "matches": {
    "same_commit": false,
    "same_branch": false,
    "same_git_status": false,
    "same_dataset": false,
    "same_query": false,
    "same_raw_packet_hash": false,
    "same_citations": false,
    "same_candidates": false,
    "same_native_count_hashes": false,
    "same_coordinate_hash": false
  },
  "differences": {
    "answer_summary_diff": [],
    "citation_diff": [],
    "candidate_order_diff": [],
    "support_level_diff": [],
    "scope_diff": [],
    "provenance_diff": [],
    "artifact_hash_diff": []
  },
  "root_cause": {
    "repo_difference": false,
    "data_difference": false,
    "count_or_index_difference": false,
    "retrieval_difference": false,
    "ranking_difference": false,
    "citation_difference": false,
    "renderer_difference": false,
    "unknown": false
  },
  "final_classification": "unknown",
  "operator_notes": ""
}
```

Allowed `final_classification` values:

```text
identical
near_identical
repo_difference
data_difference
count_or_index_difference
retrieval_difference
ranking_difference
citation_difference
rendering_difference
scope_difference
unknown
```

## Manual Procedure

1. Machine A fills `AW_DIFF_REPORT_V1`.
2. Machine B fills `AW_DIFF_REPORT_V1`.
3. Compare the two reports into `AW_MACHINE_DIFF_V1`.
4. Classify the disagreement layer.
5. Discuss final answer wording only after packet comparison is complete.

## Automation Gate

Automate only after two or three real machine diffs have been performed by hand.
The first automation target is structural comparison of already-filled forms,
not a new retrieval or ranking method.
