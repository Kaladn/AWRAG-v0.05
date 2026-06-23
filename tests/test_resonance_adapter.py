from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import adapt_resonance_sample


def test_resonance_adapter_processes_whole_artifact_dataset_without_symbols(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "plots").mkdir()
    (source / "__pycache__").mkdir()

    (source / "context_map.json").write_text(
        json.dumps({
            "basement": {"-1": ["the"], "1": ["door", "creatures"]},
            "creatures": {"-1": ["basement"], "1": ["evil"]},
            "evil": {"-1": ["the"], "1": ["basement"]},
        }),
        encoding="utf-8",
    )
    (source / "context_clouds.json").write_text(
        json.dumps({
            "basement": {
                "members": ["creatures", "evil"],
                "strengths": {"creatures": 1.0, "evil": 0.8},
            },
            "creatures": {
                "members": ["basement"],
                "strengths": {"basement": 1.0},
            },
            "evil": {
                "members": ["basement"],
                "strengths": {"basement": 0.8},
            },
        }),
        encoding="utf-8",
    )
    (source / "analysis_results.json").write_text(
        json.dumps({"context_windows": {"basement": {}, "creatures": {}}}),
        encoding="utf-8",
    )
    (source / "summary_report.md").write_text("# sample\n", encoding="utf-8")
    (source / "standalone_context_parser.py").write_text("# parser\n", encoding="utf-8")
    (source / "plots" / "resonance_heatmap.png").write_bytes(b"png")
    (source / "__pycache__" / "junk.pyc").write_bytes(b"cache")

    out = tmp_path / "out"
    result = adapt_resonance_sample(source, out, dataset_id="basement_resonance", copy_source=True, top_n=2)

    assert result["whole_dataset_records_written"] == 3
    assert result["symbols_assigned"] is False
    assert result["source_mutated"] is False
    assert (out / "resonance_adapter_summary.json").exists()
    assert (out / "resonance_adapter_summary.md").exists()
    assert (out / "resonance_anchor_records.jsonl").exists()
    assert (out / "source_copy" / "context_map.json").exists()
    assert not (out / "source_copy" / "__pycache__" / "junk.pyc").exists()

    summary = json.loads((out / "resonance_adapter_summary.json").read_text(encoding="utf-8"))
    assert summary["context_anchor_count"] == 3
    assert summary["cloud_anchor_count"] == 3
    assert summary["cloud_membership_count"] == 4
    assert summary["symbol_plan"]["symbols_assigned_now"] is False

    run_receipt = json.loads((out / "receipts" / "run_receipt.json").read_text(encoding="utf-8"))
    assert run_receipt["aw_intake_ran"] is False
    assert run_receipt["counts_written"] is False
    assert run_receipt["lexicon_written"] is False
    assert run_receipt["symbols_assigned"] is False
    assert run_receipt["binaries_written"] is False

    source_receipt = json.loads((out / "receipts" / "source_receipt.json").read_text(encoding="utf-8"))
    assert source_receipt["cache_residue_present"] is True


def test_resonance_adapter_symbolizes_without_faking_native_counts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "context_map.json").write_text(
        json.dumps({
            "trailer": {"-1": ["uhaul", "tractor"], "1": ["rental"]},
            "uhaul": {"1": ["trailer"]},
        }),
        encoding="utf-8",
    )
    (source / "context_clouds.json").write_text(
        json.dumps({
            "trailer": {
                "members": ["uhaul", "tractor", "rental"],
                "strengths": {"uhaul": 1.0, "tractor": 0.2, "rental": 0.8},
            },
            "uhaul": {
                "members": ["trailer"],
                "strengths": {"trailer": 1.0},
            },
        }),
        encoding="utf-8",
    )
    (source / "analysis_results.json").write_text(
        json.dumps({"context_windows": {"trailer": {}}}),
        encoding="utf-8",
    )
    (source / "summary_report.md").write_text("# sample\n", encoding="utf-8")

    out = tmp_path / "out"
    result = adapt_resonance_sample(source, out, dataset_id="trailer_field", symbolize=True, top_n=3)

    assert result["symbols_assigned"] is True
    assert result["binary_plan"]["binaries_written_now"] is False
    assert "symbol_lexicon" in result["outputs"]
    assert "binary_count_readiness_receipt" in result["outputs"]

    lexicon = json.loads((out / "symbolized" / "dataset_symbol_lexicon.json").read_text(encoding="utf-8"))
    assert lexicon["active_aw_query_lexicon"] is False
    assert {row["anchor"] for row in lexicon["anchors"]} == {"rental", "tractor", "trailer", "uhaul"}

    context_edges = (out / "symbolized" / "resonance_context_edges.jsonl").read_text(encoding="utf-8").splitlines()
    assert context_edges
    first_edge = json.loads(context_edges[0])
    assert first_edge["raw_observation_count_available"] is False

    binary_receipt = json.loads((out / "receipts" / "binary_count_readiness_receipt.json").read_text(encoding="utf-8"))
    assert binary_receipt["native_awbin_counts_written"] is False
    assert binary_receipt["do_not_fake_counts_from_rank_or_resonance"] is True

