from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from awrag.engine.anchors import anchorize, symbol_bytes
from awrag.engine.storage import RELATION_RECORD


SCHEMA = "awrag_question_cloud_preflight@1"


@dataclass(frozen=True)
class ArtifactState:
    path: str
    exists: bool
    size: int
    sha256: str | None
    modified_ns: int | None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="question_cloud_preflight",
        description="Report-only question cloud preflight. No search, topK, answers, or mutation.",
    )
    parser.add_argument("--query-map", type=Path, required=True)
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--relation-counts", type=Path, required=True)
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--block-anchor-postings", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset", default="SciFact")
    parser.add_argument("--max-expected", type=int, default=8)
    args = parser.parse_args()

    result = run_preflight(
        query_map_path=args.query_map,
        lexicon_path=args.lexicon,
        relation_counts_path=args.relation_counts,
        anchor_counts_path=args.anchor_counts,
        block_anchor_path=args.block_anchor_postings,
        out_dir=args.out,
        dataset=args.dataset,
        max_expected=args.max_expected,
    )
    print(json.dumps(result, ensure_ascii=True))


def run_preflight(
    *,
    query_map_path: Path,
    lexicon_path: Path,
    relation_counts_path: Path,
    anchor_counts_path: Path,
    block_anchor_path: Path,
    out_dir: Path,
    dataset: str,
    max_expected: int = 8,
) -> dict[str, Any]:
    required = [query_map_path, lexicon_path, relation_counts_path, anchor_counts_path, block_anchor_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"required input artifacts missing: {missing}")

    before = _artifact_states(required)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "receipts").mkdir(parents=True, exist_ok=True)

    queries = _load_test_queries(query_map_path)
    lexicon_rows = _load_lexicon(lexicon_path)
    anchor_counts = {row["anchor"]: int(row.get("observations", 0)) for row in lexicon_rows}
    symbol_to_anchor = {_normalize_symbol_hex(str(row["symbol"])): str(row["anchor"]) for row in lexicon_rows}

    all_question_anchors = sorted({anchor for row in queries for anchor in anchorize(row["question"])})
    relation_cloud = _load_relation_cloud_for_anchors(
        relation_counts_path,
        wanted_anchors=all_question_anchors,
        symbol_to_anchor=symbol_to_anchor,
        max_expected=max_expected,
    )

    records = [
        _audit_question(
            row,
            anchor_counts=anchor_counts,
            relation_cloud=relation_cloud,
            lexicon_anchors=sorted(anchor_counts),
            max_expected=max_expected,
        )
        for row in queries
    ]

    approved = [row for row in records if row["approved"]]
    changed = [row for row in records if row["suggested_question"]]
    review = [row for row in records if row["requires_human_review"]]

    _write_jsonl(out_dir / "questions_original_vs_suggested.jsonl", records)
    _write_jsonl(out_dir / "questions_approved.jsonl", approved)
    _write_jsonl(out_dir / "questions_changed.jsonl", changed)
    _write_jsonl(out_dir / "questions_human_review.jsonl", review)

    after = _artifact_states(required)
    mutation_detected = before != after

    summary = _summary_payload(
        dataset=dataset,
        query_map_path=query_map_path,
        lexicon_path=lexicon_path,
        relation_counts_path=relation_counts_path,
        anchor_counts_path=anchor_counts_path,
        block_anchor_path=block_anchor_path,
        records=records,
        mutation_detected=mutation_detected,
        before=before,
        after=after,
    )
    _write_json(out_dir / "QUESTION_CLOUD_PREFLIGHT_SUMMARY.json", summary)
    _write_markdown(out_dir / "QUESTION_CLOUD_PREFLIGHT_SUMMARY.md", summary)

    _write_json(out_dir / "receipts" / "run_receipt.json", {
        "schema": "awrag_question_cloud_preflight_run_receipt@1",
        "mode": "report_only",
        "search_ran": False,
        "topk_ran": False,
        "answering_ran": False,
        "gold_comparison_ran": False,
        "model_used": "none",
        "embeddings_used": False,
        "reranker_used": False,
        "records_written": len(records),
        "output_dir": str(out_dir),
    })
    _write_json(out_dir / "receipts" / "inputs_receipt.json", {
        "schema": "awrag_question_cloud_preflight_inputs_receipt@1",
        "dataset": dataset,
        "query_map_path": str(query_map_path),
        "lexicon_path": str(lexicon_path),
        "relation_counts_path": str(relation_counts_path),
        "anchor_counts_path": str(anchor_counts_path),
        "block_anchor_postings_path": str(block_anchor_path),
        "question_count": len(queries),
        "dataset_anchor_count": len(anchor_counts),
        "question_anchor_count": len(all_question_anchors),
        "question_anchor_extraction": "awrag.engine.anchors.anchorize",
    })
    _write_json(out_dir / "receipts" / "no_mutation_receipt.json", {
        "schema": "awrag_question_cloud_preflight_no_mutation_receipt@1",
        "mutation_detected": mutation_detected,
        "before": [state.__dict__ for state in before],
        "after": [state.__dict__ for state in after],
    })
    return {
        "schema": SCHEMA,
        "questions_processed": len(records),
        "questions_approved_unchanged": len(approved),
        "questions_with_suggested_changes": len(changed),
        "questions_needing_human_review": len(review),
        "mutation_detected": mutation_detected,
        "output_dir": str(out_dir),
    }


def _load_test_queries(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("test_queries")
    if not isinstance(rows, list) or not rows:
        raise ValueError("query map does not contain test_queries")
    required = {"query_id", "question"}
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or not required.issubset(row):
            raise ValueError("test query row is missing query_id or question")
        out.append({
            "question_id": str(row["query_id"]),
            "line_number": row.get("line_number"),
            "test_line_number": row.get("test_line_number"),
            "question": str(row["question"]),
        })
    return out


def _load_lexicon(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("anchors")
    if not isinstance(rows, list) or not rows:
        raise ValueError("lexicon has no anchors")
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or "anchor" not in row or "symbol" not in row:
            continue
        out.append(row)
    if not out:
        raise ValueError("lexicon has no usable anchor rows")
    return out


def _load_relation_cloud_for_anchors(
    path: Path,
    *,
    wanted_anchors: list[str],
    symbol_to_anchor: dict[str, str],
    max_expected: int,
) -> dict[str, list[dict[str, Any]]]:
    wanted_symbols = {symbol_bytes(anchor): anchor for anchor in wanted_anchors}
    relation_totals: dict[str, Counter[str]] = defaultdict(Counter)
    with path.open("rb") as handle:
        while chunk := handle.read(RELATION_RECORD.size):
            if len(chunk) != RELATION_RECORD.size:
                continue
            source_symbol, neighbor_symbol, offset, observations = RELATION_RECORD.unpack(chunk)
            source_anchor = wanted_symbols.get(source_symbol)
            neighbor_anchor = symbol_to_anchor.get(_symbol_hex(neighbor_symbol))
            if source_anchor and neighbor_anchor:
                relation_totals[source_anchor][neighbor_anchor] += int(observations)
            neighbor_query_anchor = wanted_symbols.get(neighbor_symbol)
            source_anchor_text = symbol_to_anchor.get(_symbol_hex(source_symbol))
            if neighbor_query_anchor and source_anchor_text:
                relation_totals[neighbor_query_anchor][source_anchor_text] += int(observations)
    return {
        anchor: [
            {"anchor": neighbor, "count": count}
            for neighbor, count in counts.most_common(max_expected)
            if neighbor != anchor
        ]
        for anchor, counts in relation_totals.items()
    }


def _audit_question(
    row: dict[str, Any],
    *,
    anchor_counts: dict[str, int],
    relation_cloud: dict[str, list[dict[str, Any]]],
    lexicon_anchors: list[str],
    max_expected: int,
) -> dict[str, Any]:
    question = row["question"]
    extracted = anchorize(question)
    unique = list(dict.fromkeys(extracted))
    present = [anchor for anchor in unique if anchor in anchor_counts]
    absent = [anchor for anchor in unique if anchor not in anchor_counts]
    rare = [
        anchor
        for anchor in unique
        if anchor in anchor_counts and int(anchor_counts.get(anchor, 0)) <= 1
    ]

    low_fit = [
        {"anchor": anchor, "reason": "not_in_dataset_lexicon", "observations": 0}
        for anchor in absent
    ]
    low_fit.extend(
        {"anchor": anchor, "reason": "rare_in_dataset_cloud", "observations": int(anchor_counts[anchor])}
        for anchor in rare
    )

    coverage = (len(present) / len(unique)) if unique else 0.0
    weighted_fit = _weighted_fit(unique, anchor_counts)
    expected = _missing_expected(unique, relation_cloud, max_expected=max_expected)
    suggestions = [_suggest_anchor(anchor, lexicon_anchors, anchor_counts) for anchor in absent]
    suggestions = [item for item in suggestions if item is not None]

    suggested_question = None
    change_reason = None
    if absent and len(suggestions) == len(absent):
        suggested_question = _apply_suggestions(question, suggestions)
        if suggested_question != question:
            change_reason = "absent anchors had high-fit dataset-cloud correction candidates"
        else:
            suggested_question = None

    requires_review = bool(absent and not suggested_question) or not unique
    approved = bool(unique) and not absent and coverage >= 1.0
    if rare and not absent:
        approved = True

    if approved:
        cloud_fit_status = "approved_unchanged"
    elif suggested_question:
        cloud_fit_status = "suggested_reshape"
    else:
        cloud_fit_status = "human_review_required"

    return {
        "schema": "awrag_question_cloud_preflight_record@1",
        "question_id": row["question_id"],
        "original_question": question,
        "extracted_anchors": unique,
        "approved": approved,
        "cloud_fit_status": cloud_fit_status,
        "cloud_fit": {
            "present_anchor_count": len(present),
            "unique_anchor_count": len(unique),
            "coverage": round(coverage, 6),
            "weighted_fit": round(weighted_fit, 6),
        },
        "low_fit_anchors": low_fit,
        "missing_expected_anchors": expected,
        "suggested_question": suggested_question,
        "change_reason": change_reason,
        "requires_human_review": requires_review,
        "trace": {
            "present_anchors": present,
            "absent_anchors": absent,
            "rare_anchors": rare,
            "suggestion_candidates": suggestions,
            "relation_cloud_used": True,
            "retrieval_ran": False,
            "topk_ran": False,
            "answering_ran": False,
        },
    }


def _weighted_fit(anchors: list[str], anchor_counts: dict[str, int]) -> float:
    if not anchors:
        return 0.0
    weights = [math.log1p(max(0, int(anchor_counts.get(anchor, 0)))) for anchor in anchors]
    possible = sum(max(1.0, weight) for weight in weights)
    actual = sum(weight for anchor, weight in zip(anchors, weights) if anchor in anchor_counts)
    return actual / possible if possible else 0.0


def _missing_expected(
    anchors: list[str],
    relation_cloud: dict[str, list[dict[str, Any]]],
    *,
    max_expected: int,
) -> list[dict[str, Any]]:
    present = set(anchors)
    totals: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)
    for anchor in anchors:
        for item in relation_cloud.get(anchor, []):
            neighbor = str(item["anchor"])
            if neighbor in present:
                continue
            totals[neighbor] += int(item["count"])
            sources[neighbor].add(anchor)
    return [
        {
            "anchor": anchor,
            "relation_count": int(count),
            "source_question_anchors": sorted(sources[anchor]),
        }
        for anchor, count in totals.most_common(max_expected)
    ]


def _suggest_anchor(
    anchor: str,
    lexicon_anchors: list[str],
    anchor_counts: dict[str, int],
) -> dict[str, Any] | None:
    if len(anchor) < 3:
        return None
    best: tuple[float, str] | None = None
    first = anchor[:1]
    candidates = [
        candidate for candidate in lexicon_anchors
        if candidate[:1] == first and abs(len(candidate) - len(anchor)) <= 3
    ]
    for candidate in candidates:
        ratio = SequenceMatcher(None, anchor, candidate).ratio()
        if ratio < 0.86:
            continue
        score = ratio + min(0.10, math.log1p(anchor_counts.get(candidate, 0)) / 100.0)
        if best is None or score > best[0]:
            best = (score, candidate)
    if best is None:
        return None
    score, candidate = best
    return {
        "raw_anchor": anchor,
        "suggested_anchor": candidate,
        "fit_score": round(score, 6),
        "suggested_observations": int(anchor_counts.get(candidate, 0)),
        "reason": "lexicon_near_match_with_dataset_observations",
    }


def _apply_suggestions(question: str, suggestions: list[dict[str, Any]]) -> str:
    updated = question
    for item in suggestions:
        raw = str(item["raw_anchor"])
        suggested = str(item["suggested_anchor"])
        updated = updated.replace(raw.capitalize(), suggested.capitalize())
        updated = updated.replace(raw.upper(), suggested.upper())
        updated = updated.replace(raw, suggested)
    return updated


def _summary_payload(
    *,
    dataset: str,
    query_map_path: Path,
    lexicon_path: Path,
    relation_counts_path: Path,
    anchor_counts_path: Path,
    block_anchor_path: Path,
    records: list[dict[str, Any]],
    mutation_detected: bool,
    before: list[ArtifactState],
    after: list[ArtifactState],
) -> dict[str, Any]:
    low_fit_counts: Counter[str] = Counter()
    missing_expected_counts: Counter[str] = Counter()
    for row in records:
        for item in row["low_fit_anchors"]:
            low_fit_counts[str(item["anchor"])] += 1
        for item in row["missing_expected_anchors"]:
            missing_expected_counts[str(item["anchor"])] += 1
    return {
        "schema": "awrag_question_cloud_preflight_summary@1",
        "dataset": dataset,
        "questions_processed": len(records),
        "questions_approved_unchanged": sum(1 for row in records if row["approved"]),
        "questions_with_suggested_changes": sum(1 for row in records if row["suggested_question"]),
        "questions_needing_human_review": sum(1 for row in records if row["requires_human_review"]),
        "most_common_low_fit_anchors": low_fit_counts.most_common(25),
        "most_common_missing_expected_anchors": missing_expected_counts.most_common(25),
        "mutation_detected": mutation_detected,
        "inputs": {
            "query_map_path": str(query_map_path),
            "lexicon_path": str(lexicon_path),
            "relation_counts_path": str(relation_counts_path),
            "anchor_counts_path": str(anchor_counts_path),
            "block_anchor_postings_path": str(block_anchor_path),
        },
        "artifact_state_before": [state.__dict__ for state in before],
        "artifact_state_after": [state.__dict__ for state in after],
        "no_search": True,
        "no_topk": True,
        "no_answering": True,
    }


def _write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Question Cloud Preflight Summary",
        "",
        "Report-only question lineup. No retrieval, topK, answering, or gold comparison ran.",
        "",
        "```text",
        f"dataset: {summary['dataset']}",
        f"questions_processed: {summary['questions_processed']}",
        f"questions_approved_unchanged: {summary['questions_approved_unchanged']}",
        f"questions_with_suggested_changes: {summary['questions_with_suggested_changes']}",
        f"questions_needing_human_review: {summary['questions_needing_human_review']}",
        f"mutation_detected: {summary['mutation_detected']}",
        "```",
        "",
        "## Most Common Low-Fit Anchors",
        "",
    ]
    for anchor, count in summary["most_common_low_fit_anchors"][:20]:
        lines.append(f"- `{anchor}`: {count}")
    if not summary["most_common_low_fit_anchors"]:
        lines.append("- none")
    lines.extend(["", "## Most Common Missing Expected Anchors", ""])
    for anchor, count in summary["most_common_missing_expected_anchors"][:20]:
        lines.append(f"- `{anchor}`: {count}")
    if not summary["most_common_missing_expected_anchors"]:
        lines.append("- none")
    lines.extend([
        "",
        "## Receipts",
        "",
        "- `receipts/run_receipt.json`",
        "- `receipts/inputs_receipt.json`",
        "- `receipts/no_mutation_receipt.json`",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _artifact_states(paths: Iterable[Path]) -> list[ArtifactState]:
    return [_artifact_state(path) for path in paths]


def _artifact_state(path: Path) -> ArtifactState:
    exists = path.exists()
    stat = path.stat() if exists else None
    return ArtifactState(
        path=str(path),
        exists=exists,
        size=int(stat.st_size) if stat else 0,
        sha256=_sha256(path) if exists else None,
        modified_ns=int(stat.st_mtime_ns) if stat else None,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _symbol_hex(raw: bytes) -> str:
    return "0x" + raw.hex().upper()


def _normalize_symbol_hex(value: str) -> str:
    text = str(value or "").strip()
    if text.lower().startswith("0x"):
        return "0x" + text[2:].upper()
    return text


if __name__ == "__main__":
    main()
