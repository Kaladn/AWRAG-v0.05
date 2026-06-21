from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import dataset_paths, intake
from experiments.clearspeak_map_speaker import SCHEMA, speak_from_map, speak_question_file

DATASET_ID = "map_speaker_dataset"


def _sizes(paths) -> dict[str, int]:
    return {
        "anchor": paths.anchor_counts_path.stat().st_size,
        "relation": paths.relation_counts_path.stat().st_size,
        "postings": paths.block_anchor_path.stat().st_size,
    }


def test_map_speaker_builds_count_lattice_evidence_frames(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Dataset-local counts speak through evidence frames.\n"
        "Counts connect anchors to source coordinates inside the native lattice.\n\n"
        "Unrelated adapter filler mentions tables and display surfaces only.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    paths = dataset_paths(runtime, DATASET_ID)
    before = _sizes(paths)

    result = speak_from_map(runtime, DATASET_ID, "How do counts speak through evidence?", top_k=2)

    after = _sizes(paths)
    assert before == after
    assert result["schema"] == SCHEMA
    assert result["model_used"] == "none"
    assert result["count_backend"] == "awrag_native_binary_counts@1"
    assert result["mutation"]["writes_counts"] is False
    assert result["loaded_lattice"]["strategy"] == "native_awbin_loaded_once_in_ram"
    assert result["loaded_lattice"]["relation_rows_loaded"] > 0
    assert result["passes"][0]["pass"] == "question"
    assert result["passes"][0]["seed_anchors"]
    frames = result["passes"][0]["candidate_frames"]
    assert frames
    assert frames[0]["citation"].startswith("[AWCIT-")
    assert "Counts connect anchors" in frames[0]["source_text"] or "Dataset-local counts speak" in frames[0]["source_text"]
    assert frames[0]["anchor_windows"]
    assert result["normal_surface_answer"]["status"] == "answered_from_awrag_evidence"
    assert result["normal_surface_answer"]["citations"]
    assert result["normal_surface_answer"]["citations"][0].startswith("[AWCIT-")
    assert Path(result["output_path"]).exists()
    persisted = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
    assert persisted["watermark_locked"] is True
    assert persisted["schema"] == SCHEMA


def test_map_speaker_can_run_mirror_answer_starter_as_separate_pass(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "The final hardware setting was voltage mode safe.\n"
        "The operator ended on voltage mode after checking the evidence receipt.\n\n"
        "A different block talks about unrelated packages and release reports.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = speak_from_map(
        runtime,
        DATASET_ID,
        "What setting did we end on?",
        mirror_starter="final setting was voltage mode",
        top_k=2,
    )

    assert [row["pass"] for row in result["passes"]] == ["question", "mirror_answer_starter"]
    mirror = result["passes"][1]
    assert "voltage" in mirror["seed_anchors"]
    assert "mode" in mirror["seed_anchors"]
    assert mirror["candidate_frames"]
    assert "voltage mode" in mirror["candidate_frames"][0]["source_text"].lower()
    normal = result["normal_surface_answer"]
    assert normal["status"] == "answered_from_supplied_answer_and_awrag_evidence"
    assert normal["text"].startswith("Final setting was voltage mode.")
    assert normal["citations"]
    assert normal["citations"][0] in normal["text"]


def test_map_speaker_batch_accepts_question_file_with_optional_mirror_starters(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Native relation counts create evidence clouds.\n"
        "Mirror starters can seed answer-shaped anchor swarms without changing counts.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    questions = tmp_path / "questions.txt"
    questions.write_text(
        "How do native counts create clouds?\n"
        "What can seed anchor swarms?\tMirror starters seed answer shaped anchor swarms\n",
        encoding="utf-8",
    )

    summary = speak_question_file(runtime, DATASET_ID, questions, top_k=2)

    assert summary["schema"] == "awrag_clearspeak_map_speaker_batch@0"
    assert summary["question_count"] == 2
    assert summary["completed"] == 2
    assert summary["failed"] == 0
    assert len(summary["output_paths"]) == 2
    assert summary["loaded_lattice"]["strategy"] == "native_awbin_loaded_once_in_ram"
    assert summary["loaded_lattice"]["relation_rows_loaded"] > 0
    second = json.loads(Path(summary["output_paths"][1]).read_text(encoding="utf-8"))
    assert second["mirror_answer_starter"] == "Mirror starters seed answer shaped anchor swarms"
    assert [row["pass"] for row in second["passes"]] == ["question", "mirror_answer_starter"]
    assert second["normal_surface_answer"]["status"] == "answered_from_supplied_answer_and_awrag_evidence"
    assert second["normal_surface_answer"]["text"].startswith("Mirror starters seed answer shaped anchor swarms.")
