from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from awrag.engine import laptop_temp_intake as laptop_temp_module
from awrag.engine.laptop_temp_intake import _build_resource_plan, laptop_temp_intake


def test_laptop_temp_intake_writes_chunk_receipts(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "\n\n".join(
            [
                "Alpha beta gamma delta.",
                "Second paragraph keeps anchors moving.",
                "Third paragraph gives the proof run more content.",
            ]
        ),
        encoding="utf-8",
    )
    state_root = tmp_path / "State" / "laptop_temp_intake"

    result = laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="proof",
        chunk_mb=1,
        max_chunks=3,
        workers=1,
        show_progress=False,
    )

    run_root = state_root / "proof"
    chunks = run_root / "chunks"
    assert result["chunks_seen"] == 1
    assert result["chunks_created"] == 1
    assert result["chunks_skipped"] == 0
    assert result["receipt_verification"] == "passed"
    assert (run_root / "manifest.json").is_file()
    assert (run_root / "resource_receipt.json").is_file()
    assert (run_root / "source_receipt.json").is_file()
    assert (run_root / "run_summary.json").is_file()
    assert (run_root / "chunk_receipts.jsonl").is_file()
    assert (chunks / "chunk_000001.raw").stat().st_size > 0
    assert (chunks / "chunk_000001.symbols.bin").stat().st_size > 0
    assert (chunks / "chunk_000001.counts.bin").stat().st_size > 0

    receipt = json.loads((chunks / "chunk_000001.receipt.json").read_text(encoding="utf-8"))
    assert receipt["input_mode"] == "raw_text"
    assert receipt["production_merge"] is False
    assert receipt["global_lifetime_write"] is False
    assert result["resource_plan"]["effective_workers"] == 1
    assert result["artifacts"]["resource_receipt"].endswith("resource_receipt.json")


def test_laptop_temp_intake_resume_skips_verified_chunks(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for index in range(2):
        (source / f"{index}.txt").write_text(f"Alpha {index} beta.\n\nGamma delta.", encoding="utf-8")
    state_root = tmp_path / "State" / "laptop_temp_intake"

    first = laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="resume-proof",
        chunk_mb=1,
        max_chunks=2,
        workers=1,
        show_progress=False,
    )
    receipt_path = state_root / "resume-proof" / "chunks" / "chunk_000001.receipt.json"
    first_mtime = receipt_path.stat().st_mtime_ns

    second = laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="resume-proof",
        chunk_mb=1,
        max_chunks=2,
        workers=1,
        show_progress=False,
    )

    assert first["chunks_created"] == 2
    assert second["chunks_seen"] == 2
    assert second["chunks_created"] == 0
    assert second["chunks_skipped"] == 2
    assert second["receipt_verification"] == "passed"
    assert receipt_path.stat().st_mtime_ns == first_mtime


def test_laptop_temp_intake_does_not_write_production_dataset_files(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Alpha beta.\n\nGamma delta.", encoding="utf-8")
    state_root = tmp_path / "State" / "laptop_temp_intake"
    production_runtime = tmp_path / "runtime"

    result = laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="no-production-write",
        chunk_mb=1,
        max_chunks=1,
        workers=1,
        show_progress=False,
    )

    assert result["production_merge"] is False
    assert result["global_lifetime_write"] is False
    assert not production_runtime.exists()
    assert not list(state_root.rglob("anchor_counts.awbin"))
    assert not list(state_root.rglob("relation_counts.awbin"))
    assert not list(state_root.rglob("block_anchor_postings.awbin"))
    assert not list(state_root.rglob("dataset_manifest.json"))


def test_laptop_temp_intake_cli_runs_without_production_dataset(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for index in range(3):
        (source / f"{index}.txt").write_text(f"Alpha {index} beta.\n\nGamma delta.", encoding="utf-8")
    state_root = tmp_path / "State" / "laptop_temp_intake"

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "awrag.cli",
            "laptop-temp-intake",
            "--source",
            str(source),
            "--state-root",
            str(state_root),
            "--run-id",
            "cli-proof",
            "--chunk-mb",
            "1",
            "--max-chunks",
            "3",
            "--workers",
            "1",
            "--no-progress",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["chunks_seen"] == 3
    assert payload["chunks_created"] == 3
    assert payload["chunks_skipped"] == 0
    assert payload["production_merge"] is False
    assert payload["global_lifetime_write"] is False
    assert (state_root / "cli-proof" / "chunks" / "chunk_000003.receipt.json").is_file()


def test_laptop_temp_intake_resource_plan_auto_caps_workers() -> None:
    plan = _build_resource_plan(
        chunk_limit=1024 * 1024,
        requested_workers="auto",
        reserve_ram_fraction=0.50,
        reserve_ram_gb=None,
    )

    assert plan["schema"] == "awrag_laptop_temp_resource_plan@1"
    assert plan["effective_workers"] >= 1
    assert plan["requested_workers"] == "auto"
    assert plan["resources"]["logical_cpu_count"] >= 1
    assert "workers_auto_selected_from_cpu_and_ram" in plan["safety_decisions"]


def test_laptop_temp_intake_chunk_failure_is_logged_and_run_continues(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for index in range(2):
        (source / f"{index}.txt").write_text(f"Alpha {index} beta.\n\nGamma delta.", encoding="utf-8")
    state_root = tmp_path / "State" / "laptop_temp_intake"
    original_process_chunk = laptop_temp_module._process_chunk

    def flaky_process_chunk(**kwargs):
        if kwargs["chunk_index"] == 1:
            raise ValueError("synthetic poisoned chunk")
        return original_process_chunk(**kwargs)

    monkeypatch.setattr(laptop_temp_module, "_process_chunk", flaky_process_chunk)

    result = laptop_temp_module.laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="failure-proof",
        chunk_mb=1,
        max_chunks=2,
        workers=1,
        show_progress=False,
    )

    assert result["chunks_seen"] == 2
    assert result["chunks_created"] == 1
    assert result["chunks_failed"] == 1
    assert result["receipt_verification"] == "passed_with_failed_chunks"
    assert result["production_merge"] is False
    assert result["global_lifetime_write"] is False
    failure_path = state_root / "failure-proof" / "chunks" / "chunk_000001.failure.json"
    assert failure_path.is_file()
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert failure["schema"] == "awrag_laptop_temp_chunk_failure@1"
    assert failure["error_type"] == "ValueError"
