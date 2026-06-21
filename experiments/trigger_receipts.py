from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return target


def append_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def write_summary(
    path: str | Path,
    *,
    trigger_count: int,
    hit_count: int,
    expanded_count: int,
    mini_counts: dict[str, Any],
    graph: dict[str, Any],
    output_paths: dict[str, str],
    throughput_messages_per_second: float,
    false_positive_samples: list[dict[str, Any]],
) -> Path:
    class_counts = mini_counts.get("counts", {}).get("anchor_class_counts", {})
    top_anchors = list(mini_counts.get("counts", {}).get("anchor_counts", {}).items())[:20]
    lines = [
        "# Trigger Anchor Temporal Causality v0",
        "",
        "JSON-first test harness. Candidate labels are not truth, diagnosis, or promotion.",
        "",
        f"Trigger anchors: {trigger_count}",
        f"Solo hits: {hit_count}",
        f"Expanded neighborhoods: {expanded_count}",
        f"Graph 1 events: {graph.get('event_count', 0)}",
        f"Throughput messages/sec: {throughput_messages_per_second:.2f}",
        "",
        "## Anchor Class Counts",
    ]
    for key, value in class_counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Top Context Anchors"])
    for key, value in top_anchors:
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Output Paths"])
    for key, value in output_paths.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## False Positive / Review Samples"])
    for row in false_positive_samples[:5]:
        lines.append(f"- {row.get('anchor')} / {row.get('anchor_class')} at {row.get('timestamp')} -> needs_review={row.get('needs_review')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def sample_review_records(records: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    out = []
    for record in records:
        out.append({
            "anchor": record.get("anchor"),
            "anchor_class": record.get("anchor_class"),
            "timestamp": record.get("timestamp"),
            "role": record.get("role"),
            "needs_review": record.get("needs_review", True),
            "citation": record.get("citation"),
        })
        if len(out) >= limit:
            break
    return out
