from __future__ import annotations

import json
from pathlib import Path

import pytest

from awrag.engine import dataset_overview, intake


DATASET_ID = "overview_dataset"


def test_dataset_overview_writes_count_field_reports_with_source_trails(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Uhaul trailer rental uses trailer hitches for local hauling.\n"
        "Uhaul trailer rental repeats because the trailer field is strong.\n\n"
        "Tractor trailer appears once in this evidence field.\n\n"
        "Uhaul trailer support repeats. Uhaul trailer rental stays common.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = dataset_overview(runtime, DATASET_ID, tmp_path / "overview", top_anchors=8, top_relations=20, trail_limit=3)

    assert result["schema"] == "awrag_dataset_overview_summary@1"
    assert result["model_used"] == "none"
    assert result["model_may_search"] is False
    assert result["query_ran"] is False
    assert result["intake_ran"] is False
    assert result["counts_written"] is False
    assert result["reasoning_engine_used"] is False
    assert result["readiness"]["status"] == "INDEX_READY"

    output_root = Path(result["output_root"])
    summary_path = output_root / "overview_summary.json"
    markdown_path = output_root / "overview_summary.md"
    anchor_path = output_root / "anchor_overviews.jsonl"
    relation_path = output_root / "relationship_trails.jsonl"
    mutation_path = output_root / "receipts" / "no_mutation_receipt.json"

    for path in (summary_path, markdown_path, anchor_path, relation_path, mutation_path):
        assert path.exists()
        assert path.stat().st_size > 0

    anchors = [json.loads(line) for line in anchor_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    anchor_names = {row["anchor"] for row in anchors}
    assert "trailer" in anchor_names
    assert "uhaul" in anchor_names
    assert any(row["source_trails"] for row in anchors)

    relations = [json.loads(line) for line in relation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(
        {row["center_anchor"], row["neighbor_anchor"]} == {"uhaul", "trailer"}
        for row in relations
    )
    assert any(row["source_trails"] for row in relations)

    mutation = json.loads(mutation_path.read_text(encoding="utf-8"))
    assert mutation["dataset_artifacts_mutated"] is False
    assert mutation["mutated_artifacts"] == []
    assert mutation["query_ran"] is False
    assert mutation["intake_ran"] is False


def test_dataset_overview_refuses_when_index_is_not_ready(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="INDEX_NOT_READY"):
        dataset_overview(tmp_path / "runtime", DATASET_ID, tmp_path / "overview")
