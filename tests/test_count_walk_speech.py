from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import count_walk_speech, intake


DATASET_ID = "count_walk_dataset"


def test_count_walk_speech_uses_count_selected_local_spine(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Uhaul trailer rental repeats because uhaul trailer rental is the dominant local phrase.\n"
        "Uhaul trailer rental support repeats in the same evidence block.\n\n"
        "Tractor trailer appears once and should not be the dominant continuation.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = count_walk_speech(
        runtime,
        DATASET_ID,
        "What trailer rental phrase repeats?",
        tmp_path / "speech",
        starter="uhaul",
        top_k=3,
        max_steps=6,
        branch_k=4,
    )

    assert result["schema"] == "awrag_count_walk_speech_result@1"
    assert result["model_used"] == "none"
    assert result["walk_status"] == "walk_complete"
    assert Path(result["evidence_trace_path"]).exists()
    assert Path(result["pretty_answer_path"]).exists()

    trace = json.loads(Path(result["evidence_trace_path"]).read_text(encoding="utf-8"))
    assert trace["speech_policy"]["method"] == "count_selected_local_spine_walk"
    assert trace["speech_policy"]["document_text_lookup_used_for_speech_body"] is False
    assert trace["selected_location"]["citation"].startswith("[AWCIT-")
    assert trace["start"]["mode"] == "starter_exact_match"
    assert trace["walked_anchors"][0] == "uhaul"
    assert "trailer" in trace["walked_anchors"]
    assert trace["steps"]
    assert trace["steps"][0]["branch_candidates"]
    assert trace["steps"][0]["chosen_by"] == "highest_native_relation_count_inside_count_selected_local_spine"
    assert trace["steps"][0]["chosen"]["native_relation_count"] > 0

    no_mutation = json.loads((tmp_path / "speech" / "receipts" / "no_mutation_receipt.json").read_text(encoding="utf-8"))
    assert no_mutation["dataset_artifacts_mutated"] is False
    assert no_mutation["mutated_artifacts"] == []
    assert no_mutation["model_used"] == "none"


def test_count_walk_speech_refuses_when_required_starter_is_not_in_local_spine(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Uhaul trailer rental repeats in admitted evidence.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = count_walk_speech(
        runtime,
        DATASET_ID,
        "What trailer rental phrase repeats?",
        tmp_path / "speech",
        starter="apple pie",
        top_k=2,
        max_steps=6,
    )

    trace = json.loads(Path(result["evidence_trace_path"]).read_text(encoding="utf-8"))
    assert trace["walk_status"] == "starter_not_found"
    assert trace["stop_reason"] == "starter anchors were not found inside count-selected local spine"
    assert trace["walked_anchors"] == []
    assert trace["steps"] == []
