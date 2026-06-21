from __future__ import annotations

from experiments.scaffold_records import ScaffoldAttemptRecord

SCHEMA_CITATION_MIRROR = "awrag_scaffold_citation_mirror@0"
SCHEMA_CROSSLINK = "awrag_scaffold_crosslink@0"


def citation_mirror_rows(attempt: ScaffoldAttemptRecord) -> list[dict]:
    rows = []
    seen = set()
    for crossing in attempt.crossings:
        marker = str(crossing.get("citation") or "").strip()
        if not marker or marker in seen:
            continue
        seen.add(marker)
        rows.append({
            "schema": SCHEMA_CITATION_MIRROR,
            "attempt_id": attempt.attempt_id,
            "question_id": attempt.question_id,
            "citation": marker,
            "block_ordinal": crossing.get("block_ordinal"),
            "file_path": crossing.get("file_path"),
            "line_start": crossing.get("line_start"),
            "line_end": crossing.get("line_end"),
            "frame_id": crossing.get("frame_id"),
            "mirror_role": "generated_citation_side_index",
            "source_boundary": "awrag_dataset_local_citation",
        })
    return rows


def crosslink_rows(attempt: ScaffoldAttemptRecord) -> list[dict]:
    rows = []
    anchors = [anchor for anchor in attempt.major_anchors if anchor]
    citations = attempt.citations
    for index, anchor in enumerate(anchors[:8]):
        rows.append({
            "schema": SCHEMA_CROSSLINK,
            "attempt_id": attempt.attempt_id,
            "question_id": attempt.question_id,
            "crosslink_type": "content",
            "source": attempt.question_id,
            "target": anchor,
            "weight": max(1, len(anchors) - index),
            "citations": citations[:4],
            "reason": "question_answer_anchor_presence",
        })
    for left, right in zip(anchors, anchors[1:]):
        rows.append({
            "schema": SCHEMA_CROSSLINK,
            "attempt_id": attempt.attempt_id,
            "question_id": attempt.question_id,
            "crosslink_type": "idea",
            "source": left,
            "target": right,
            "weight": 1,
            "citations": citations[:4],
            "reason": "adjacent_answer_anchor_path",
        })
    for left, right in zip(citations, citations[1:]):
        rows.append({
            "schema": SCHEMA_CROSSLINK,
            "attempt_id": attempt.attempt_id,
            "question_id": attempt.question_id,
            "crosslink_type": "context",
            "source": left,
            "target": right,
            "weight": 1,
            "citations": [left, right],
            "reason": "same_attempt_citation_context",
        })
    return rows
