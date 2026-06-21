from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import intake
from experiments.aw_backend_tap import AwBackendTap
from experiments.bad_phrase_law_suite import build_bad_phrase_law_suite
from experiments.bad_phrase_search import search_bad_phrase_entry
from experiments.bad_phrase_temporal_causality import run_bad_phrase_temporal_causality
from experiments.trigger_anchor_search import load_chat_blocks


def _build_dataset(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "chat_source.md"
    source.write_text(
        "## CHAT_TURN_1\n"
        "CHAT_TITLE: Prior action\n"
        "CHAT_CREATED_AT: 2026-06-20T10:00:00Z\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TEXT:\n"
        "I changed the path and wrote a receipt.\n\n"
        "## CHAT_TURN_2\n"
        "CHAT_TITLE: Intent review\n"
        "CHAT_CREATED_AT: 2026-06-20T10:01:00Z\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TEXT:\n"
        "you did it on purpose and that is bullshit.\n\n"
        "## CHAT_TURN_3\n"
        "CHAT_TITLE: Followup\n"
        "CHAT_CREATED_AT: 2026-06-20T10:02:00Z\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TEXT:\n"
        "I will keep that as a review-only failure signal.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    dataset_id = "bad_phrase_chat_dataset"
    intake(runtime, dataset_id, source)
    return runtime, dataset_id


def test_bad_phrase_search_finds_grouped_intent_phrase(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    blocks = load_chat_blocks(AwBackendTap(runtime, dataset_id))
    hits = search_bad_phrase_entry(blocks, {"surface": "did it on purpose", "anchors": ["did", "it", "on", "purpose"], "class": "intentionality_attribution_candidate", "severity": "strong"})
    assert hits
    assert hits[0].matched_anchor_width == 2
    assert hits[0].positions


def test_bad_phrase_temporal_runner_writes_full_review_outputs(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    out = tmp_path / "bad_phrase_out"
    receipt = run_bad_phrase_temporal_causality(runtime_root=runtime, dataset_id=dataset_id, out=out)
    required = [
        "bad_phrase_law_suite.json",
        "bad_phrase_hits.jsonl",
        "bad_phrase_expanded_blocks.jsonl",
        "bad_phrase_mini-local-counts.json",
        "bad_phrase_temporal_causality_graph.json",
        "bad_phrase_summary.md",
        "bad_phrase_run_receipt.json",
    ]
    for name in required:
        assert (out / name).exists(), name
    graph = json.loads((out / "bad_phrase_temporal_causality_graph.json").read_text(encoding="utf-8"))
    assert graph["event_count"] == receipt["expanded_hit_count"]
    assert all(event["needs_review"] is True for event in graph["events"])
    assert all(event["confidence"] == 0.0 for event in graph["events"])
    assert any(event["trigger_anchor"] == "did it on purpose" for event in graph["events"])
