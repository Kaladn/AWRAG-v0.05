from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = REPO_ROOT / "src"
for path in (REPO_ROOT, REPO_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from awrag.engine import anchorize, unique_stamp, utc_now  # noqa: E402
from experiments.aw_backend_tap import AwBackendTap
from experiments.clearspeak_map_speaker import speak_from_loaded_map
from experiments.generation_binary import load_generation_binary, write_generation_binary
from experiments.generation_lexicon import build_generation_lexicon_from_aw_file, write_generation_lexicon
from experiments.resident_dataset_tap import ResidentDatasetTap
from experiments.scaffold_crosslinks import citation_mirror_rows, crosslink_rows
from experiments.scaffold_grader import grade_attempt
from experiments.scaffold_primer_questions import PRIMER_QUESTIONS
from experiments.scaffold_receipts import ScaffoldReceiptWriter
from experiments.scaffold_records import (
    ScaffoldAttemptRecord,
    ScaffoldBehaviorRecord,
    ScaffoldCorrectionRecord,
    ScaffoldFailureRecord,
    ScaffoldQuestionRecord,
    ScaffoldRunSummary,
)

SCHEMA = "awrag_scaffold_loop_v0@0"


def run_scaffold_loop(
    runtime_root: str | Path,
    dataset_id: str,
    *,
    output_dir: str | Path | None = None,
    generation_binary_path: str | Path | None = None,
    seeds: list[str] | None = None,
    primer_count: int = 100,
    max_records: int = 48,
    packet_size: int = 10,
    followups_per_answer: int = 2,
    top_k: int = 3,
    candidate_depth: int = 30,
) -> dict[str, Any]:
    tap = AwBackendTap(runtime_root, dataset_id)
    tap.require_ready()
    run_id = unique_stamp()
    out_dir = Path(output_dir) if output_dir else Path(runtime_root).expanduser().resolve().parent / "reports" / "scaffold_loop_v0" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = ScaffoldReceiptWriter(out_dir)
    writer.write_manifest({
        "schema": SCHEMA,
        "run_id": run_id,
        "created_at": utc_now(),
        "runtime_root": str(Path(runtime_root).expanduser().resolve()),
        "dataset_id": tap.dataset_id,
        "mode": "chat_data_self_scaffold_experiment",
        "mutation_allowed": False,
        "writes_core": False,
        "writes_dataset_runtime": False,
        "packet_size": packet_size,
        "followups_are_answer_formed": True,
        "backend_tap": tap.status(include_sha256=False),
    })
    tap.write_tap_receipt(out_dir)
    resident = ResidentDatasetTap(tap)
    resident.write_load_receipt(out_dir)
    generation_path = Path(generation_binary_path) if generation_binary_path else _build_generation_helper(tap, out_dir)
    generation = load_generation_binary(generation_path, dataset_id=tap.dataset_id, set_id=f"{tap.dataset_id}_generation_helper_v0")

    seed_rows = seeds if seeds is not None else PRIMER_QUESTIONS[:primer_count]
    queue: deque[ScaffoldQuestionRecord] = deque(
        _question_record(text, tap.dataset_id, index=index, parent_id=None, depth=0, source="primer_seed")
        for index, text in enumerate(seed_rows[:primer_count], start=1)
    )

    attempts = failures = corrections = behaviors = packet_index = 0
    questions_seen: set[str] = set()
    anchors_seen: Counter[str] = Counter()
    packet_paths: list[str] = []

    while queue and attempts < max_records:
        packet_index += 1
        packet_payload: dict[str, Any] = {
            "schema": "awrag_scaffold_question_packet@0",
            "run_id": run_id,
            "packet_index": packet_index,
            "packet_size": packet_size,
            "dataset_id": tap.dataset_id,
            "questions": [],
            "attempts": [],
            "failures": [],
            "corrections": [],
            "behaviors": [],
            "formed_followups": [],
            "citation_mirror": [],
            "crosslinks": [],
        }
        current_packet = _pop_packet(queue, packet_size, max_records - attempts)
        for question in current_packet:
            if question.question_id in questions_seen or attempts >= max_records:
                continue
            questions_seen.add(question.question_id)
            writer.append_question(question.to_dict())
            packet_payload["questions"].append(question.to_dict())
            result = speak_from_loaded_map(resident, question.question, top_k=top_k, candidate_depth=candidate_depth, write_receipt=False)
            attempt = _attempt_from_result(result, question, tap.dataset_id)
            writer.append_attempt(attempt)
            packet_payload["attempts"].append(attempt.to_dict())
            attempts += 1
            for anchor in attempt.major_anchors:
                anchors_seen[anchor] += 1
            for row in citation_mirror_rows(attempt):
                writer.append_citation_mirror(row)
                packet_payload["citation_mirror"].append(row)
            for row in crosslink_rows(attempt):
                writer.append_crosslink(row)
                packet_payload["crosslinks"].append(row)
            grade = grade_attempt(attempt, generation=generation)
            if grade.passed:
                behavior = ScaffoldBehaviorRecord(
                    schema="awrag_scaffold_behavior@0",
                    behavior_id=_stable_id("behavior", attempt.attempt_id),
                    attempt_id=attempt.attempt_id,
                    question_id=attempt.question_id,
                    status="trusted_behavior_candidate",
                    reason="passed deterministic scaffold gate",
                    promotable=False,
                    metadata={"promotion_requires_human_review": True},
                )
                writer.append_behavior(behavior)
                packet_payload["behaviors"].append(behavior.to_dict())
                behaviors += 1
                for followup in followup_questions_from_answer(attempt, max_followups=followups_per_answer):
                    if attempts + len(queue) >= max_records:
                        break
                    formed = _question_record(followup, tap.dataset_id, index=attempts + len(queue) + 1, parent_id=attempt.question_id, depth=question.depth + 1, source="answer_formed_followup")
                    queue.append(formed)
                    packet_payload["formed_followups"].append(formed.to_dict())
            else:
                failure = ScaffoldFailureRecord(
                    schema="awrag_scaffold_failure@0",
                    failure_id=_stable_id("failure", attempt.attempt_id, grade.failure_explanation),
                    attempt_id=attempt.attempt_id,
                    question_id=attempt.question_id,
                    failure_types=grade.failure_types,
                    failure_explanation=grade.failure_explanation,
                    retry_guidance=grade.retry_guidance,
                    missing_variables=grade.missing_variables,
                    unsupported_terms=grade.unsupported_terms,
                    metadata=grade.metadata,
                )
                writer.append_failure(failure)
                packet_payload["failures"].append(failure.to_dict())
                failures += 1
                correction = ScaffoldCorrectionRecord(
                    schema="awrag_scaffold_correction@0",
                    correction_id=_stable_id("correction", failure.failure_id),
                    failure_id=failure.failure_id,
                    question_id=attempt.question_id,
                    correction_notes=grade.retry_guidance or ["keep diagnostic; do not promote"],
                    next_question=None,
                    metadata={"status": "diagnostic_only"},
                )
                writer.append_correction(correction)
                packet_payload["corrections"].append(correction.to_dict())
                corrections += 1
        packet_paths.append(str(writer.write_packet(packet_index, packet_payload)))

    summary = ScaffoldRunSummary(
        schema="awrag_scaffold_run_summary@0",
        run_id=run_id,
        dataset_id=tap.dataset_id,
        runtime_root=str(Path(runtime_root).expanduser().resolve()),
        output_dir=str(out_dir),
        question_count=len(questions_seen),
        attempt_count=attempts,
        failure_count=failures,
        correction_count=corrections,
        behavior_count=behaviors,
        max_records=max_records,
        completed=True,
        recommendation="keep_diagnostic" if failures else "promote_with_human_review_only",
        metadata={
            "packet_count": len(packet_paths),
            "packet_paths": packet_paths,
            "top_anchors": anchors_seen.most_common(25),
            "generation_binary_path": str(generation_path),
            "resident_load": resident.load_stats(),
            "citation_mirror_path": str(writer.citation_mirror_path),
            "crosslinks_path": str(writer.crosslinks_path),
        },
    )
    summary_json, summary_md = writer.write_summary(summary)
    return {
        "schema": SCHEMA,
        "run_id": run_id,
        "dataset_id": tap.dataset_id,
        "output_dir": str(out_dir),
        "summary_path": str(summary_json),
        "summary_markdown_path": str(summary_md),
        "packet_paths": packet_paths,
        "attempt_count": attempts,
        "failure_count": failures,
        "correction_count": corrections,
        "behavior_count": behaviors,
        "resident_load": resident.load_stats(),
    }


def followup_questions_from_answer(attempt: ScaffoldAttemptRecord, *, max_followups: int = 2) -> list[str]:
    """Form follow-up questions only from the prior answer scaffold."""
    out: list[str] = []
    anchors = [anchor for anchor in attempt.major_anchors if len(anchor) >= 4 and any(ch.isalpha() for ch in anchor)]
    for left, right in zip(anchors, anchors[1:]):
        out.append(f"What does the cited evidence connect between {left} and {right}?")
        if len(out) >= max_followups:
            return out
    for anchor in anchors:
        out.append(f"What does the cited evidence say about {anchor}?")
        if len(out) >= max_followups:
            break
    return out


def _pop_packet(queue: deque[ScaffoldQuestionRecord], packet_size: int, remaining: int) -> list[ScaffoldQuestionRecord]:
    rows = []
    for _ in range(min(packet_size, remaining)):
        if not queue:
            break
        rows.append(queue.popleft())
    return rows


def _question_record(text: str, dataset_id: str, *, index: int, parent_id: str | None, depth: int, source: str) -> ScaffoldQuestionRecord:
    return ScaffoldQuestionRecord(
        schema="awrag_scaffold_question@0",
        question_id=_stable_id("question", text, parent_id or "root", str(depth)),
        parent_id=parent_id,
        depth=depth,
        question=text,
        source_dataset=dataset_id,
        source=source,
        major_anchors=_major_anchors_from_text(text),
        metadata={"index": index},
    )


def _attempt_from_result(result: dict[str, Any], question: ScaffoldQuestionRecord, dataset_id: str) -> ScaffoldAttemptRecord:
    normal = result.get("normal_surface_answer", {})
    passes = list(result.get("passes", []))
    frames = []
    for row in passes:
        frames.extend(row.get("candidate_frames", []))
    citations: list[str] = []
    crossings: list[dict[str, Any]] = []
    major: list[str] = []
    for frame in frames:
        citation = str(frame.get("citation") or "").strip()
        if citation and citation not in citations:
            citations.append(citation)
        crossings.append({
            "citation": citation,
            "block_ordinal": frame.get("block_ordinal"),
            "file_path": frame.get("file_path"),
            "line_start": frame.get("line_start") or frame.get("start_line"),
            "line_end": frame.get("line_end") or frame.get("end_line"),
            "frame_id": frame.get("frame_id"),
            "score": frame.get("score"),
            "density_score": frame.get("density_score"),
        })
        for anchor in list(frame.get("direct_matched_anchors", [])) + list(frame.get("matched_anchors", [])):
            value = str(anchor).strip().lower()
            if value and value not in major:
                major.append(value)
    if not major:
        major = _major_anchors_from_text(str(normal.get("text") or question.question))
    return ScaffoldAttemptRecord(
        schema="awrag_scaffold_attempt@0",
        attempt_id=_stable_id("attempt", question.question_id, str(result.get("created_at"))),
        question_id=question.question_id,
        parent_id=question.parent_id,
        depth=question.depth,
        question=question.question,
        answer_text=str(normal.get("text") or ""),
        major_anchors=major[:12],
        citations=citations[:8],
        crossings=crossings[:8],
        evidence_frame_count=len(frames),
        source_dataset=dataset_id,
        output_path=result.get("output_path"),
        metadata={
            "surface_answer_status": normal.get("status"),
            "question_anchors": result.get("question_anchors", []),
            "pass_count": len(passes),
        },
    )


def _major_anchors_from_text(text: str, *, limit: int = 8) -> list[str]:
    blocked = {"what", "did", "does", "the", "data", "chat", "about", "with", "from", "that", "this", "mean", "means"}
    out: list[str] = []
    for anchor in anchorize(text):
        value = str(anchor).strip().lower()
        if len(value) < 3 or value in blocked or not any(ch.isalpha() for ch in value):
            continue
        if value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _build_generation_helper(tap: AwBackendTap, output_dir: Path) -> Path:
    lexicon = build_generation_lexicon_from_aw_file(tap.paths.lexicon_path, set_id=f"{tap.dataset_id}_generation_helper_v0", domain="chat_dataset")
    lexicon_path = output_dir / "generation_helper_lexicon.json"
    binary_path = output_dir / "generation.awgenbin"
    write_generation_lexicon(lexicon_path, lexicon)
    write_generation_binary(binary_path, lexicon)
    return binary_path


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run isolated Scaffold Loop v0 over an existing AWRAG dataset.")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--generation-binary")
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--primer-count", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=48)
    parser.add_argument("--packet-size", type=int, default=10)
    parser.add_argument("--followups-per-answer", type=int, default=2)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-depth", type=int, default=30)
    args = parser.parse_args(argv)
    summary = run_scaffold_loop(
        args.runtime_root,
        args.dataset_id,
        output_dir=args.output_dir,
        generation_binary_path=args.generation_binary,
        seeds=args.seed or None,
        primer_count=args.primer_count,
        max_records=args.max_records,
        packet_size=args.packet_size,
        followups_per_answer=args.followups_per_answer,
        top_k=args.top_k,
        candidate_depth=args.candidate_depth,
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
