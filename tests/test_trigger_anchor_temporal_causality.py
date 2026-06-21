from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import intake
from experiments.aw_backend_tap import AwBackendTap
from experiments.hit_expander import expand_hit_neighborhood
from experiments.mini_local_counts import build_mini_local_counts
from experiments.temporal_causality_graph import build_temporal_causality_graph
from experiments.trigger_anchor_search import load_chat_blocks, search_solo_anchor
from experiments.trigger_anchor_seed import build_trigger_anchors
from experiments.trigger_anchor_temporal_causality import run_trigger_anchor_temporal_causality


def _build_dataset(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "chat_source.md"
    source.write_text(
        "## CHAT_TURN_1\n"
        "CHAT_TITLE: Build receipt\n"
        "CHAT_CREATED_AT: 2026-06-20T10:00:00Z\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TEXT:\n"
        "The module stayed isolated and wrote receipts.\n\n"
        "## CHAT_TURN_2\n"
        "CHAT_TITLE: Build receipt\n"
        "CHAT_CREATED_AT: 2026-06-20T10:01:00Z\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TEXT:\n"
        "good job that works and the boundary is correct.\n\n"
        "## CHAT_TURN_3\n"
        "CHAT_TITLE: Bad bridge\n"
        "CHAT_CREATED_AT: 2026-06-20T10:02:00Z\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TEXT:\n"
        "no that bridge is trash remove it.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    dataset_id = "trigger_chat_dataset"
    intake(runtime, dataset_id, source)
    return runtime, dataset_id


def test_trigger_anchor_seed_returns_review_only_candidates() -> None:
    payload = build_trigger_anchors(top_anchors=10)
    assert payload["schema"] == "trigger_anchors@1"
    assert payload["count"] == 10
    assert all(row["needs_review"] is True for row in payload["anchors"])
    assert all(row["authority"] == "corpus_state_signal" for row in payload["anchors"])


def test_trigger_search_and_expansion_include_previous_current_next(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    tap = AwBackendTap(runtime, dataset_id)
    blocks = load_chat_blocks(tap)
    hits = search_solo_anchor(blocks, {"anchor": "good", "class": "praise"})
    assert hits
    expanded = expand_hit_neighborhood({row.block_ordinal: row for row in blocks}, hits[0]).to_record()
    assert expanded["previous_blocks"]
    assert expanded["hit_block"]
    assert expanded["next_blocks"]
    assert expanded["citation"]["marker"].startswith("[AWCIT-")
    assert expanded["needs_review"] is True
    assert expanded["confidence"] == 0.0


def test_mini_counts_and_graph_keep_events_reviewable(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    tap = AwBackendTap(runtime, dataset_id)
    blocks = load_chat_blocks(tap)
    hits = search_solo_anchor(blocks, {"anchor": "trash", "class": "anger_frustration"})
    expanded = [expand_hit_neighborhood({row.block_ordinal: row for row in blocks}, hits[0]).to_record()]
    counts = build_mini_local_counts(expanded)
    graph = build_temporal_causality_graph(expanded, counts)
    assert counts["schema"] == "mini_local_counts@1"
    assert graph["schema"] == "temporal_causality_graph@1"
    assert graph["events"][0]["needs_review"] is True
    assert graph["events"][0]["confidence"] == 0.0
    assert graph["events"][0]["citations"][0]["marker"].startswith("[AWCIT-")


def test_trigger_anchor_temporal_causality_runner_writes_required_files(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    out = tmp_path / "trigger_out"
    receipt = run_trigger_anchor_temporal_causality(
        runtime_root=runtime,
        dataset_id=dataset_id,
        out=out,
        top_anchors=20,
        max_hits_per_anchor=10,
        max_total_hits=8,
    )
    required = [
        "trigger_anchors.json",
        "trigger_hits.jsonl",
        "trigger_expanded_blocks.jsonl",
        "mini-local-counts.json",
        "temporal_causality_graph.json",
        "trigger_anchor_summary.md",
    ]
    for name in required:
        assert (out / name).exists(), name
    graph = json.loads((out / "temporal_causality_graph.json").read_text(encoding="utf-8"))
    assert graph["event_count"] == receipt["expanded_hit_count"]
    assert all(row["needs_review"] is True for row in graph["events"])
