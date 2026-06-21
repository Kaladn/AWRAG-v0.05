from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import anchorize  # noqa: E402

SCHEMA = "mini_local_counts@1"


def build_mini_local_counts(expanded_records: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    prior_counts: dict[str, Counter[str]] = defaultdict(Counter)
    next_counts: dict[str, Counter[str]] = defaultdict(Counter)
    role_counts: dict[str, Counter[str]] = defaultdict(Counter)
    date_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cross_day_counts: dict[str, Counter[str]] = defaultdict(Counter)
    assistant_shape_before: dict[str, Counter[str]] = defaultdict(Counter)
    user_reaction_after_shape: dict[str, Counter[str]] = defaultdict(Counter)

    for record in expanded_records:
        trigger = str(record.get("anchor") or "").lower()
        cls = str(record.get("anchor_class") or "unknown")
        if not trigger:
            continue
        class_counts[cls] += 1
        role_counts[trigger][str(record.get("role") or "unknown")] += 1
        date_counts[str(record.get("date") or "unknown")][trigger] += 1
        for block in list(record.get("previous_blocks") or []):
            for anchor in _block_anchors(block):
                anchor_counts[anchor] += 1
                prior_counts[trigger][anchor] += 1
                if record.get("date"):
                    cross_day_counts[str(record.get("date"))][anchor] += 1
            if str(block.get("speaker") or "").lower() == "assistant":
                assistant_shape_before[trigger][_answer_shape(block.get("text", ""))] += 1
        for anchor in _block_anchors(record.get("hit_block") or {}):
            anchor_counts[anchor] += 1
        for block in list(record.get("next_blocks") or []):
            for anchor in _block_anchors(block):
                anchor_counts[anchor] += 1
                next_counts[trigger][anchor] += 1
            if str((record.get("hit_block") or {}).get("speaker") or "").lower() == "assistant":
                user_reaction_after_shape[_answer_shape((record.get("hit_block") or {}).get("text", ""))][trigger] += 1

    return {
        "schema": SCHEMA,
        "source": "trigger_expanded_blocks",
        "counts": {
            "anchor_counts": dict(anchor_counts.most_common()),
            "anchor_class_counts": dict(class_counts.most_common()),
            "trigger_to_prior_anchor_counts": _nested_counter(prior_counts),
            "trigger_to_next_anchor_counts": _nested_counter(next_counts),
            "trigger_to_role_counts": _nested_counter(role_counts),
            "assistant_response_shape_before_trigger": _nested_counter(assistant_shape_before),
            "user_reaction_after_assistant_shape": _nested_counter(user_reaction_after_shape),
            "date_to_trigger_counts": _nested_counter(date_counts),
            "cross_day_anchor_counts": _nested_counter(cross_day_counts),
        },
    }


def _block_anchors(block: dict[str, Any]) -> list[str]:
    text = str(block.get("text") or "")
    out = []
    for anchor in anchorize(text):
        value = str(anchor).strip().lower()
        if len(value) < 2:
            continue
        out.append(value)
    return out


def _answer_shape(text: str) -> str:
    lower = str(text or "").lower()
    if "citation" in lower or "[awcit-" in lower:
        return "citation_or_receipt_shape"
    if "do not" in lower or "no " in lower or "must" in lower:
        return "boundary_instruction_shape"
    if "test" in lower or "pass" in lower or "failed" in lower:
        return "test_report_shape"
    if "plan" in lower or "step" in lower:
        return "plan_shape"
    return "plain_response_shape"


def _nested_counter(rows: dict[str, Counter[str]], *, limit: int = 50) -> dict[str, dict[str, int]]:
    return {key: dict(counter.most_common(limit)) for key, counter in sorted(rows.items())}
