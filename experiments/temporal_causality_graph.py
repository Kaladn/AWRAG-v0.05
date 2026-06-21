from __future__ import annotations

import hashlib
from typing import Any

import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import anchorize  # noqa: E402

SCHEMA = "temporal_causality_graph@1"


def build_temporal_causality_graph(expanded_records: list[dict[str, Any]], mini_counts: dict[str, Any]) -> dict[str, Any]:
    events = []
    for index, record in enumerate(expanded_records, start=1):
        trigger = str(record.get("anchor") or "")
        event_id = f"tcg-{index:06d}-{_digest(record)[:8]}"
        prior = _top_context_anchors(record.get("previous_blocks") or [])
        hit = _top_context_anchors([record.get("hit_block") or {}])
        nxt = _top_context_anchors(record.get("next_blocks") or [])
        events.append({
            "schema": "temporal_causality_event@1",
            "event_id": event_id,
            "date": record.get("date"),
            "timestamp": record.get("timestamp"),
            "trigger_anchor": trigger,
            "trigger_class": record.get("anchor_class"),
            "prior_context_anchors": prior,
            "hit_context_anchors": hit,
            "next_context_anchors": nxt,
            "inferred_event_shape": _event_shape(record, prior, hit, nxt),
            "citations": [record.get("citation")],
            "confidence": 0.0,
            "needs_review": True,
            "diagnostic_warning": "Candidate temporal state event only; review expanded context before interpretation.",
        })
    return {
        "schema": SCHEMA,
        "event_count": len(events),
        "events": events,
        "count_refs": {
            "anchor_class_counts": mini_counts.get("counts", {}).get("anchor_class_counts", {}),
            "date_to_trigger_counts": mini_counts.get("counts", {}).get("date_to_trigger_counts", {}),
        },
    }


def _top_context_anchors(blocks: list[dict[str, Any]], *, limit: int = 12) -> list[str]:
    counts: dict[str, int] = {}
    blocked = {"chat_text", "chat_title", "chat_speaker", "the", "and", "that", "this", "with", "you"}
    for block in blocks:
        for anchor in anchorize(str(block.get("text") or "")):
            key = str(anchor).strip().lower()
            if len(key) < 3 or key in blocked:
                continue
            counts[key] = counts.get(key, 0) + 1
    return [key for key, _value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _event_shape(record: dict[str, Any], prior: list[str], hit: list[str], nxt: list[str]) -> str:
    role = str(record.get("role") or "unknown").lower()
    cls = str(record.get("anchor_class") or "unknown")
    if role == "user" and cls == "praise":
        return "candidate_user_approval_or_positive_signal_after_prior_context"
    if role == "user" and cls in {"anger_frustration", "correction_control"}:
        return "candidate_user_correction_or_boundary_signal_after_prior_context"
    if role == "assistant" and cls == "coding_building":
        return "candidate_assistant_system_building_response"
    return "candidate_contextual_state_signal"


def _digest(record: dict[str, Any]) -> str:
    raw = "|".join(str(record.get(key) or "") for key in ("anchor", "timestamp", "role"))
    raw += "|" + str((record.get("hit_block") or {}).get("block_id") or "")
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()
