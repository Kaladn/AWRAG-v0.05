from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import intake
from experiments.aw_backend_tap import AwBackendTap
from experiments.resident_dataset_tap import ResidentDatasetTap
from experiments.scaffold_grader import grade_attempt
from experiments.scaffold_loop_v0 import followup_questions_from_answer, run_scaffold_loop
from experiments.scaffold_primer_questions import PRIMER_QUESTIONS
from experiments.scaffold_records import ScaffoldAttemptRecord


def _build_dataset(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "chat_source.md"
    source.write_text(
        "## CHAT_TURN_1\n"
        "CHAT_TITLE: Voltage decision\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TEXT:\n"
        "We ended on voltage mode safe after checking the receipt.\n\n"
        "## CHAT_TURN_2\n"
        "CHAT_TITLE: Generation helper\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TEXT:\n"
        "Generation helper lexicon should use observed anchors and approved glue only.\n\n"
        "## CHAT_TURN_3\n"
        "CHAT_TITLE: Scaffold memory\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TEXT:\n"
        "Failures enter memory as failures and corrected attempts become behavior candidates.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    dataset_id = "scaffold_chat_dataset"
    intake(runtime, dataset_id, source)
    return runtime, dataset_id


def test_primer_question_set_has_one_hundred_ordered_entries() -> None:
    assert len(PRIMER_QUESTIONS) == 100
    assert PRIMER_QUESTIONS[0] == "What does it mean to live a good life?"
    assert PRIMER_QUESTIONS[-1] == "What should a thinking system do when it does not know enough?"


def test_backend_tap_reports_existing_dataset_without_mutating_counts(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    tap = AwBackendTap(runtime, dataset_id)
    before = tap.status()
    receipt_path = tap.write_tap_receipt(tmp_path / "out")
    after = tap.status()
    assert receipt_path.exists()
    assert before["relation_count"] == after["relation_count"]
    assert before["block_anchor_posting_count"] == after["block_anchor_posting_count"]
    assert before["count_backend"] == "awrag_native_binary_counts@1"
    assert before["required_files_present"] is True


def test_resident_dataset_tap_loads_locked_lookup_view(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    resident = ResidentDatasetTap(AwBackendTap(runtime, dataset_id))
    assert resident.locked is True
    assert resident.load_stats()["strategy"] == "native_awbin_loaded_once_in_ram"
    assert resident.load_stats()["relation_rows_loaded"] > 0
    assert resident.lookup_anchor_blocks("voltage")
    assert resident.lookup_anchor_neighbors("voltage")
    first = resident.lookup_anchor_blocks("voltage")[0]
    assert resident.get_citation(first["citation"])["marker"] == first["citation"]
    assert "voltage mode" in (resident.get_block_text(first["block_ordinal"]) or "")


def test_scaffold_grader_records_failures_without_promotion() -> None:
    attempt = ScaffoldAttemptRecord(
        schema="awrag_scaffold_attempt@0",
        attempt_id="attempt_1",
        question_id="question_1",
        parent_id=None,
        depth=0,
        question="What did we decide?",
        answer_text="This proves everything from general knowledge.",
        major_anchors=[],
        citations=[],
        crossings=[],
        evidence_frame_count=0,
        source_dataset="dataset",
    )
    grade = grade_attempt(attempt)
    assert grade.passed is False
    assert "missing_citation" in grade.failure_types
    assert "weak_crossing" in grade.failure_types
    assert "evidence_speech_boundary_leak" in grade.failure_types
    assert "missing_variables" in grade.failure_types


def test_followups_are_formed_from_answer_attempt_not_static_children() -> None:
    attempt = ScaffoldAttemptRecord(
        schema="awrag_scaffold_attempt@0",
        attempt_id="attempt_2",
        question_id="question_2",
        parent_id=None,
        depth=0,
        question="What did the chat data say?",
        answer_text="voltage and mode safe. [AWCIT-1]",
        major_anchors=["voltage", "mode", "safe"],
        citations=["[AWCIT-1]"],
        crossings=[],
        evidence_frame_count=1,
        source_dataset="dataset",
    )
    followups = followup_questions_from_answer(attempt, max_followups=2)
    assert followups == [
        "What does the cited evidence connect between voltage and mode?",
        "What does the cited evidence connect between mode and safe?",
    ]


def test_scaffold_loop_writes_packets_mirror_and_crosslinks_only(tmp_path: Path) -> None:
    runtime, dataset_id = _build_dataset(tmp_path)
    output_dir = tmp_path / "scaffold_out"
    result = run_scaffold_loop(
        runtime,
        dataset_id,
        output_dir=output_dir,
        seeds=[
            "What did the chat data say about voltage mode?",
            "What did the chat data say about generation helper?",
        ],
        primer_count=2,
        max_records=4,
        packet_size=2,
        top_k=2,
        candidate_depth=10,
    )
    assert result["attempt_count"] >= 2
    assert Path(result["summary_path"]).exists()
    assert (output_dir / "attempts.jsonl").exists()
    assert (output_dir / "citation_mirror.jsonl").exists()
    assert (output_dir / "crosslinks.jsonl").exists()
    assert result["packet_paths"]
    packet = json.loads(Path(result["packet_paths"][0]).read_text(encoding="utf-8"))
    assert packet["schema"] == "awrag_scaffold_question_packet@0"
    assert packet["citation_mirror"]
    assert packet["crosslinks"]
    summary = json.loads(Path(result["summary_path"]).read_text(encoding="utf-8"))
    assert summary["metadata"]["resident_load"]["strategy"] == "native_awbin_loaded_once_in_ram"
    assert result["resident_load"]["locked"] is True
