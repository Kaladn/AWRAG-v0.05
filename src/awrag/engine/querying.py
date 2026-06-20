from __future__ import annotations

from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

from ..nlp_resolver import resolve_answer
from .anchors import STOP_ANCHORS, anchorize, expand_query_anchors, symbol_bytes, symbol_hex
from .base import COUNT_BACKEND, safe_id, sha1_text, unique_stamp, utc_now, with_protected_notice, write_json
from .chat import apply_block_metadata_filter, build_metadata_filter
from .forensic import build_forensic_support_receipt
from .qualification import qualify_evidence
from .storage import (
    DatasetPaths,
    dataset_paths,
    ensure_dataset,
    iter_relation_records,
    read_block_anchor_rows,
    read_blocks,
    read_symbol_to_anchor,
)


def query(
    runtime_root: str | Path,
    dataset_id: str,
    question: str,
    *,
    top_k: int = 5,
    created_after: str | None = None,
    created_before: str | None = None,
    speaker: str | None = None,
) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    q_anchors = expand_query_anchors(anchorize(question))
    if not q_anchors:
        raise ValueError("question produced no anchors")
    q_counter = Counter(q_anchors)

    blocks = read_blocks(paths)
    block_anchor_rows = read_block_anchor_rows(paths)
    metadata_filter = build_metadata_filter(created_after=created_after, created_before=created_before, speaker=speaker)
    if metadata_filter["active"]:
        blocks, block_anchor_rows = apply_block_metadata_filter(blocks, block_anchor_rows, metadata_filter)
    relation_neighbors = top_relation_neighbors(paths, q_counter, limit=16)
    raw_candidate_blocks = score_blocks(paths, blocks, block_anchor_rows, q_counter, relation_neighbors, top_k=max(top_k * 5, 25))
    qualified = qualify_evidence(question, Counter(anchorize(question)), raw_candidate_blocks, top_k=top_k)

    answer_packet = {
        "instruction": "Use cited local evidence coordinates only. This packet is a facsimile output, not source evidence.",
        "citations_owned_by": "AWRAG",
        "qualification": qualified["summary"],
        "qualification_receipts": qualified["receipts"],
        "locations": qualified["locations"],
        "rejected_locations": qualified["rejected"],
    }
    final_answer = resolve_answer(question, answer_packet)
    forensic_receipt = build_forensic_support_receipt(question, answer_packet, final_answer)

    output = {
        "schema": "awrag_query_result@1",
        "created_at": utc_now(),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "question": question,
        "question_anchors": list(q_counter),
        "relation_neighbors": relation_neighbors,
        "count_backend": COUNT_BACKEND,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
        "metadata_filter": metadata_filter,
        "answer_packet": answer_packet,
        "final_answer": final_answer,
        "forensic_support_receipt": forensic_receipt,
    }
    output_path = paths.outputs / f"query_{unique_stamp()}_{sha1_text(question)[:8]}.json"
    write_json(output_path, output)
    output["output_path"] = str(output_path)
    return with_protected_notice(output)

def batch_questions(
    runtime_root: str | Path,
    dataset_id: str,
    questions_path: str | Path,
    *,
    top_k: int = 5,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Run a plain question list through the existing single-question query path."""
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    source = Path(questions_path).expanduser().resolve()
    questions = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    run_id = unique_stamp()
    run_dir = paths.outputs / f"batch_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    completed = 0
    failures: list[dict[str, Any]] = []
    output_paths: list[str] = []
    question_results: list[dict[str, Any]] = []

    items = _progress_iter(enumerate(questions, start=1), total=len(questions), enabled=show_progress)
    for index, question in items:
        item_started = perf_counter()
        try:
            result = query(runtime_root, dataset_id, question, top_k=top_k)
            elapsed = perf_counter() - item_started
            completed += 1
            output_path = str(result["output_path"])
            output_paths.append(output_path)
            question_results.append({
                "index": index,
                "question": question,
                "status": "completed",
                "output_path": output_path,
                "query_time_seconds": elapsed,
                "model_used": result.get("model_used", "none"),
            })
        except Exception as exc:  # pragma: no cover - defensive batch receipt path
            elapsed = perf_counter() - item_started
            failure = {
                "index": index,
                "question": question,
                "status": "failed",
                "error": str(exc),
                "query_time_seconds": elapsed,
                "model_used": "none",
            }
            failures.append(failure)
            question_results.append(failure)

    total_elapsed = perf_counter() - started
    average = total_elapsed / len(questions) if questions else 0.0
    summary = with_protected_notice({
        "schema": "awrag_batch_run_summary@1",
        "run_id": run_id,
        "created_at": utc_now(),
        "dataset": safe_id(dataset_id),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "questions_path": str(source),
        "question_count": len(questions),
        "completed": completed,
        "failed": len(failures),
        "output_paths": output_paths,
        "question_results": question_results,
        "failures": failures,
        "avg_query_time": average,
        "avg_query_time_seconds": average,
        "total_time_seconds": total_elapsed,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
    })
    summary_path = run_dir / "batch_run_summary.json"
    write_json(summary_path, summary)
    summary["summary_path"] = str(summary_path)
    return summary

def _progress_iter(iterable: Iterable[Any], *, total: int, enabled: bool) -> Iterable[Any]:
    if not enabled:
        return iterable
    try:
        from tqdm import tqdm
    except Exception:  # pragma: no cover - fallback only when tqdm is unavailable
        return iterable
    return tqdm(iterable, total=total, desc="AWRAG batch", unit="question")

def top_relation_neighbors(paths: DatasetPaths, q_counter: Counter[str], *, limit: int) -> list[dict[str, Any]]:
    scores: Counter[bytes] = Counter()
    blocked_symbols = {symbol_bytes(anchor) for anchor in q_counter} | {symbol_bytes(anchor) for anchor in STOP_ANCHORS}
    query_symbols = {symbol_bytes(anchor): weight for anchor, weight in q_counter.items()}
    symbol_to_anchor = read_symbol_to_anchor(paths)
    for anchor_symbol, neighbor_symbol, _offset, observations in iter_relation_records(paths):
        weight = query_symbols.get(anchor_symbol)
        if not weight or neighbor_symbol in blocked_symbols:
            continue
        scores[neighbor_symbol] += observations * weight
    return [
        {"anchor": symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)), "symbol": symbol_hex(symbol), "score": score}
        for symbol, score in scores.most_common(limit)
    ]

def score_blocks(
    paths: DatasetPaths,
    blocks: dict[int, dict[str, Any]],
    block_anchor_rows: list[tuple[bytes, int, int]],
    q_counter: Counter[str],
    relation_neighbors: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    weights: Counter[bytes] = Counter()
    direct_symbols = {symbol_bytes(anchor) for anchor in q_counter}
    symbol_to_anchor = read_symbol_to_anchor(paths)
    for anchor, count in q_counter.items():
        weights[symbol_bytes(anchor)] += 80 * count
    for index, row in enumerate(relation_neighbors):
        weights[bytes.fromhex(str(row["symbol"])[2:])] += max(1, 4 - index // 4)

    posting_counts: Counter[bytes] = Counter(symbol for symbol, _block, _pos in block_anchor_rows)
    block_lengths: Counter[int] = Counter(block for _symbol, block, _pos in block_anchor_rows)
    block_scores: Counter[int] = Counter()
    hits: dict[int, set[bytes]] = {}
    direct_hits: Counter[int] = Counter()
    seen_postings: set[tuple[bytes, int]] = set()

    for symbol, block_ordinal, _position in block_anchor_rows:
        weight = weights.get(symbol)
        if not weight:
            continue
        posting_key = (symbol, block_ordinal)
        if posting_key in seen_postings:
            continue
        seen_postings.add(posting_key)
        document_frequency = posting_counts[symbol]
        adjusted_weight = weight / max(1.0, document_frequency ** 0.5)
        block_scores[block_ordinal] += adjusted_weight
        hits.setdefault(block_ordinal, set()).add(symbol)
        if symbol in direct_symbols:
            direct_hits[block_ordinal] += 1

    ranked_rows: list[tuple[int, float, float, int]] = []
    for block_ordinal, score in block_scores.items():
        anchor_count = block_lengths.get(block_ordinal, 1)
        density = float(score) / max(1.0, anchor_count ** 0.5)
        ranked_rows.append((block_ordinal, float(score), density, anchor_count))
    ranked = sorted(ranked_rows, key=lambda item: (-direct_hits[item[0]], -item[2], -item[1], item[0]))

    out: list[dict[str, Any]] = []
    for block_ordinal, score, density, anchor_count in ranked[:top_k]:
        block = blocks.get(block_ordinal)
        if not block:
            continue
        matched_symbols = hits.get(block_ordinal, set())
        out.append({
            "citation": str(block["marker"]),
            "file_path": str(block["file_path"]),
            "line_start": int(block["line_start"]),
            "line_end": int(block["line_end"]),
            "score": round(float(score), 4),
            "density_score": round(float(density), 4),
            "block_anchor_count": anchor_count,
            "direct_hit_count": int(direct_hits[block_ordinal]),
            "direct_matched_anchors": sorted(symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)) for symbol in matched_symbols & direct_symbols),
            "matched_anchors": sorted(symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)) for symbol in matched_symbols),
            "text": str(block["text"]),
        })
    return out
