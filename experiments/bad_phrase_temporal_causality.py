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
from experiments.bad_phrase_law_suite import build_bad_phrase_law_suite, write_bad_phrase_law_suite
from experiments.bad_phrase_search import search_bad_phrase_entry
from experiments.hit_expander import make_chat_citation
from experiments.mini_local_counts import build_mini_local_counts
from experiments.temporal_causality_graph import build_temporal_causality_graph
from experiments.trigger_anchor_search import load_chat_blocks
from experiments.trigger_receipts import append_jsonl, write_json

SCHEMA = "bad_phrase_temporal_causality_run@1"


def run_bad_phrase_temporal_causality(
    *,
    runtime_root: str | Path,
    dataset_id: str,
    out: str | Path,
    date: str | None = None,
    expand_prev: int = 1,
    expand_next: int = 1,
    max_hits_per_phrase: int | None = None,
) -> dict[str, Any]:
    started = perf_counter()
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)
    tap = AwBackendTap(runtime_root, dataset_id)
    tap.require_ready()
    suite = build_bad_phrase_law_suite()
    law_path = write_bad_phrase_law_suite(output_dir / "bad_phrase_law_suite.json", suite)
    blocks = load_chat_blocks(tap, date=date)
    blocks_by_ordinal = {block.block_ordinal: block for block in blocks}

    hits_path = output_dir / "bad_phrase_hits.jsonl"
    expanded_path = output_dir / "bad_phrase_expanded_blocks.jsonl"
    for path in (hits_path, expanded_path):
        if path.exists():
            path.unlink()

    expanded_records: list[dict[str, Any]] = []
    hit_count = 0
    phrase_hit_counts: dict[str, int] = {}
    for entry in suite["entries"]:
        hits = search_bad_phrase_entry(blocks, entry, max_hits=max_hits_per_phrase)
        phrase_hit_counts[str(entry["surface"])] = len(hits)
        for hit in hits:
            hit_count += 1
            append_jsonl(hits_path, {
                "schema": "bad_phrase_hit@1",
                "surface": hit.surface,
                "phrase_class": hit.phrase_class,
                "severity": hit.severity,
                "block_ordinal": hit.block.block_ordinal,
                "message_id": hit.block.message_id,
                "conversation_id": hit.block.conversation_id,
                "timestamp": hit.block.timestamp,
                "date": hit.block.date,
                "role": hit.block.speaker,
                "positions": hit.positions,
                "matched_anchor_width": hit.matched_anchor_width,
                "citation": hit.block.marker,
                "needs_review": True,
                "confidence": 0.0,
                "interpretation_policy": "never_infer_fixed_emotion_or_intent_from_phrase_alone",
            })
            record = _expanded_bad_phrase_record(hit, blocks_by_ordinal, previous_blocks=expand_prev, next_blocks=expand_next)
            expanded_records.append(record)
            append_jsonl(expanded_path, record)

    mini_counts = build_mini_local_counts(expanded_records)
    mini_counts_path = write_json(output_dir / "bad_phrase_mini-local-counts.json", mini_counts)
    graph = build_temporal_causality_graph(expanded_records, mini_counts)
    graph_path = write_json(output_dir / "bad_phrase_temporal_causality_graph.json", graph)
    summary_path = _write_summary(
        output_dir / "bad_phrase_summary.md",
        suite_count=suite["count"],
        messages_read=len(blocks),
        hit_count=hit_count,
        expanded_count=len(expanded_records),
        graph_event_count=graph.get("event_count", 0),
        phrase_hit_counts=phrase_hit_counts,
        output_dir=output_dir,
        elapsed_seconds=max(0.000001, perf_counter() - started),
    )
    receipt = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "run_id": unique_stamp(),
        "dataset_id": tap.dataset_id,
        "runtime_root": str(Path(runtime_root).expanduser().resolve()),
        "date_filter": date,
        "messages_read": len(blocks),
        "bad_phrase_entries": suite["count"],
        "solo_or_phrase_hit_count": hit_count,
        "expanded_hit_count": len(expanded_records),
        "graph1_event_count": graph.get("event_count", 0),
        "confidence_policy": "all_events_start_0.0",
        "review_policy": "all_events_need_review_true",
        "interpretation_policy": "phrases_are_candidates_not_truth_or_diagnosis",
        "mutation": {
            "writes_core": False,
            "writes_aw_counts": False,
            "writes_aw_citations": False,
            "writes_aw_coordinates": False,
            "writes_experiment_output_only": True,
        },
        "output_paths": {
            "bad_phrase_law_suite": str(law_path),
            "bad_phrase_hits": str(hits_path),
            "bad_phrase_expanded_blocks": str(expanded_path),
            "bad_phrase_mini_local_counts": str(mini_counts_path),
            "bad_phrase_temporal_causality_graph": str(graph_path),
            "bad_phrase_summary": str(summary_path),
        },
    }
    receipt_path = write_json(output_dir / "bad_phrase_run_receipt.json", receipt)
    receipt["output_paths"]["bad_phrase_run_receipt"] = str(receipt_path)
    return receipt


def _expanded_bad_phrase_record(hit, blocks_by_ordinal: dict[int, Any], *, previous_blocks: int, next_blocks: int) -> dict[str, Any]:
    ordinal = hit.block.block_ordinal
    previous = [blocks_by_ordinal[idx].to_dict() for idx in range(ordinal - previous_blocks, ordinal) if idx in blocks_by_ordinal]
    nxt = [blocks_by_ordinal[idx].to_dict() for idx in range(ordinal + 1, ordinal + 1 + next_blocks) if idx in blocks_by_ordinal]
    return {
        "schema": "bad_phrase_expanded_block@1",
        "anchor": hit.surface,
        "anchor_class": hit.phrase_class,
        "severity": hit.severity,
        "hit_message_id": hit.block.message_id,
        "conversation_id": hit.block.conversation_id,
        "timestamp": hit.block.timestamp,
        "date": hit.block.date,
        "role": hit.block.speaker,
        "positions": hit.positions,
        "matched_anchor_width": hit.matched_anchor_width,
        "previous_blocks": previous,
        "hit_block": hit.block.to_dict(),
        "next_blocks": nxt,
        "citation": make_chat_citation(hit.block),
        "needs_review": True,
        "confidence": 0.0,
        "interpretation_policy": "review previous/current/next before interpreting phrase meaning",
    }


def _write_summary(
    path: Path,
    *,
    suite_count: int,
    messages_read: int,
    hit_count: int,
    expanded_count: int,
    graph_event_count: int,
    phrase_hit_counts: dict[str, int],
    output_dir: Path,
    elapsed_seconds: float,
) -> Path:
    top = sorted(phrase_hit_counts.items(), key=lambda item: (-item[1], item[0]))[:25]
    lines = [
        "# Bad Phrase Law Suite Full Chat Pass",
        "",
        "JSON-first review harness. Bad phrases are candidates, not truth, intent, diagnosis, or fixed emotion.",
        "",
        f"Messages read: {messages_read}",
        f"Law entries: {suite_count}",
        f"Hits: {hit_count}",
        f"Expanded neighborhoods: {expanded_count}",
        f"Graph 1 events: {graph_event_count}",
        f"Elapsed seconds: {elapsed_seconds:.3f}",
        "",
        "## Top Phrase Hits",
    ]
    for phrase, count in top:
        lines.append(f"- {phrase}: {count}")
    lines.extend([
        "",
        "## Required Review Law",
        "- Every event starts confidence 0.0.",
        "- Every event is needs_review true.",
        "- Previous/current/next context is required before interpretation.",
        "- Profanity, threat language, and intentionality phrases are not fixed emotional meanings.",
        "",
        "## Output Folder",
        f"`{output_dir}`",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bad phrase law suite against an AWRAG chat dataset.")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--date")
    parser.add_argument("--expand-prev", type=int, default=1)
    parser.add_argument("--expand-next", type=int, default=1)
    parser.add_argument("--max-hits-per-phrase", type=int)
    args = parser.parse_args(argv)
    receipt = run_bad_phrase_temporal_causality(
        runtime_root=args.runtime_root,
        dataset_id=args.dataset_id,
        out=args.out,
        date=args.date,
        expand_prev=args.expand_prev,
        expand_next=args.expand_next,
        max_hits_per_phrase=args.max_hits_per_phrase,
    )
    print(json.dumps(receipt, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
