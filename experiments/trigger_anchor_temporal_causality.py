from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = REPO_ROOT / "src"
for path in (REPO_ROOT, REPO_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from awrag.engine import unique_stamp, utc_now  # noqa: E402
from experiments.aw_backend_tap import AwBackendTap
from experiments.hit_expander import expand_hit_neighborhood
from experiments.mini_local_counts import build_mini_local_counts
from experiments.temporal_causality_graph import build_temporal_causality_graph
from experiments.trigger_anchor_search import load_chat_blocks, search_solo_anchor
from experiments.trigger_anchor_seed import build_trigger_anchors, write_trigger_anchors
from experiments.trigger_receipts import append_jsonl, sample_review_records, write_json, write_summary

SCHEMA = "trigger_anchor_temporal_causality_run@1"


def run_trigger_anchor_temporal_causality(
    *,
    runtime_root: str | Path,
    dataset_id: str,
    out: str | Path,
    top_anchors: int = 100,
    date: str | None = None,
    expand_prev: int = 1,
    expand_next: int = 1,
    max_hits_per_anchor: int = 500,
    max_total_hits: int | None = None,
) -> dict[str, Any]:
    started = perf_counter()
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)
    tap = AwBackendTap(runtime_root, dataset_id)
    tap.require_ready()

    trigger_payload = build_trigger_anchors(top_anchors=top_anchors)
    trigger_anchors_path = write_trigger_anchors(output_dir / "trigger_anchors.json", trigger_payload)
    blocks = load_chat_blocks(tap, date=date)
    blocks_by_ordinal = {block.block_ordinal: block for block in blocks}

    hits_path = output_dir / "trigger_hits.jsonl"
    expanded_path = output_dir / "trigger_expanded_blocks.jsonl"
    if hits_path.exists(): hits_path.unlink()
    if expanded_path.exists(): expanded_path.unlink()

    expanded_records: list[dict[str, Any]] = []
    hit_count = 0
    for trigger in trigger_payload["anchors"]:
        hits = search_solo_anchor(blocks, trigger, max_hits=max_hits_per_anchor)
        for hit in hits:
            hit_count += 1
            append_jsonl(hits_path, {
                "schema": "trigger_hit@1",
                "anchor": hit.anchor,
                "anchor_class": hit.anchor_class,
                "block_ordinal": hit.block.block_ordinal,
                "message_id": hit.block.message_id,
                "conversation_id": hit.block.conversation_id,
                "timestamp": hit.block.timestamp,
                "date": hit.block.date,
                "role": hit.block.speaker,
                "positions": hit.positions,
                "citation": hit.block.marker,
                "needs_review": True,
                "confidence": 0.0,
            })
            expanded = expand_hit_neighborhood(blocks_by_ordinal, hit, previous_blocks=expand_prev, next_blocks=expand_next).to_record()
            expanded_records.append(expanded)
            append_jsonl(expanded_path, expanded)
            if max_total_hits is not None and len(expanded_records) >= max_total_hits:
                break
        if max_total_hits is not None and len(expanded_records) >= max_total_hits:
            break

    mini_counts = build_mini_local_counts(expanded_records)
    mini_counts_path = write_json(output_dir / "mini-local-counts.json", mini_counts)
    graph = build_temporal_causality_graph(expanded_records, mini_counts)
    graph_path = write_json(output_dir / "temporal_causality_graph.json", graph)
    elapsed = max(0.000001, perf_counter() - started)
    throughput = len(blocks) / elapsed
    output_paths = {
        "trigger_anchors": str(trigger_anchors_path),
        "trigger_hits": str(hits_path),
        "trigger_expanded_blocks": str(expanded_path),
        "mini_local_counts": str(mini_counts_path),
        "temporal_causality_graph": str(graph_path),
        "trigger_anchor_summary": str(output_dir / "trigger_anchor_summary.md"),
    }
    summary_path = write_summary(
        output_dir / "trigger_anchor_summary.md",
        trigger_count=trigger_payload["count"],
        hit_count=hit_count,
        expanded_count=len(expanded_records),
        mini_counts=mini_counts,
        graph=graph,
        output_paths=output_paths,
        throughput_messages_per_second=throughput,
        false_positive_samples=sample_review_records(expanded_records),
    )
    receipt = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "run_id": unique_stamp(),
        "dataset_id": tap.dataset_id,
        "runtime_root": str(Path(runtime_root).expanduser().resolve()),
        "date_filter": date,
        "messages_read": len(blocks),
        "trigger_anchor_count": trigger_payload["count"],
        "solo_hit_count": hit_count,
        "expanded_hit_count": len(expanded_records),
        "graph1_event_count": graph.get("event_count", 0),
        "throughput_messages_per_second": throughput,
        "confidence_policy": "all_events_start_0.0",
        "review_policy": "all_events_need_review_true",
        "mutation": {
            "writes_core": False,
            "writes_aw_counts": False,
            "writes_aw_citations": False,
            "writes_aw_coordinates": False,
            "writes_experiment_output_only": True,
        },
        "output_paths": output_paths | {"summary": str(summary_path)},
    }
    receipt_path = write_json(output_dir / "run_receipt.json", receipt)
    receipt["output_paths"]["run_receipt"] = str(receipt_path)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Trigger Anchor Temporal Causality v0 JSON test harness.")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--top-anchors", type=int, default=100)
    parser.add_argument("--date")
    parser.add_argument("--expand-prev", type=int, default=1)
    parser.add_argument("--expand-next", type=int, default=1)
    parser.add_argument("--max-hits-per-anchor", type=int, default=500)
    parser.add_argument("--max-total-hits", type=int)
    args = parser.parse_args(argv)
    receipt = run_trigger_anchor_temporal_causality(
        runtime_root=args.runtime_root,
        dataset_id=args.dataset_id,
        out=args.out,
        top_anchors=args.top_anchors,
        date=args.date,
        expand_prev=args.expand_prev,
        expand_next=args.expand_next,
        max_hits_per_anchor=args.max_hits_per_anchor,
        max_total_hits=args.max_total_hits,
    )
    print(json.dumps(receipt, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
