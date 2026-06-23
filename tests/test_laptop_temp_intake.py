from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import Future
from pathlib import Path

import pytest

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
        workers=2,
        reserve_ram_fraction=0.0,
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
    assert (run_root / "progress.json").is_file()
    assert (run_root / "run_events.jsonl").is_file()
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
    assert result["resource_plan"]["effective_workers"] == 2
    assert result["artifacts"]["resource_receipt"].endswith("resource_receipt.json")
    assert result["artifacts"]["progress"].endswith("progress.json")
    assert result["artifacts"]["run_events"].endswith("run_events.jsonl")

    progress = json.loads((run_root / "progress.json").read_text(encoding="utf-8"))
    assert progress["schema"] == "awrag_laptop_temp_intake_progress@1"
    assert progress["phase"] == "complete"
    assert progress["chunks_seen"] == 1
    assert progress["effective_workers"] == 2
    events = [json.loads(line) for line in (run_root / "run_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [row["event"] for row in events] == ["run_started", "chunk_processed", "run_complete"]


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
        workers=2,
        reserve_ram_fraction=0.0,
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
        workers=2,
        reserve_ram_fraction=0.0,
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
        workers=2,
        reserve_ram_fraction=0.0,
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
            "2",
            "--reserve-ram-fraction",
            "0",
            "--progress-snapshot-interval-sec",
            "0",
            "--json-output",
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
    assert (state_root / "cli-proof" / "progress.json").is_file()
    assert (state_root / "cli-proof" / "run_events.jsonl").is_file()


def test_laptop_temp_intake_resource_plan_auto_caps_workers(monkeypatch) -> None:
    monkeypatch.setattr(
        laptop_temp_module,
        "_detect_system_resources",
        lambda: {
            "logical_cpu_count": 8,
            "total_ram_bytes": 16 * 1024 * 1024 * 1024,
            "available_ram_bytes": 16 * 1024 * 1024 * 1024,
            "detection_method": "test",
        },
    )

    plan = _build_resource_plan(
        chunk_limit=1024 * 1024,
        requested_workers="auto",
        reserve_ram_fraction=0.50,
        reserve_ram_gb=None,
    )

    assert plan["schema"] == "awrag_laptop_temp_resource_plan@1"
    assert plan["effective_workers"] >= 2
    assert plan["requested_workers"] == "auto"
    assert plan["resources"]["logical_cpu_count"] >= 1
    assert "workers_auto_selected_from_cpu_and_ram" in plan["safety_decisions"]


def test_laptop_temp_intake_rejects_single_worker() -> None:
    with pytest.raises(ValueError, match="single-core execution is not allowed"):
        _build_resource_plan(
            chunk_limit=1024 * 1024,
            requested_workers=1,
            reserve_ram_fraction=0.0,
            reserve_ram_gb=None,
        )


def test_laptop_temp_intake_rejects_fixed_worker_count_that_cannot_be_honored(monkeypatch) -> None:
    monkeypatch.setattr(
        laptop_temp_module,
        "_detect_system_resources",
        lambda: {
            "logical_cpu_count": 4,
            "total_ram_bytes": 16 * 1024 * 1024 * 1024,
            "available_ram_bytes": 16 * 1024 * 1024 * 1024,
            "detection_method": "test",
        },
    )

    with pytest.raises(RuntimeError, match="requested workers=4 cannot be honored"):
        _build_resource_plan(
            chunk_limit=1024 * 1024,
            requested_workers=4,
            reserve_ram_fraction=0.0,
            reserve_ram_gb=None,
        )


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

    class FakeProcessPoolExecutor:
        def __init__(self, max_workers: int):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def submit(self, fn, **kwargs):
            future: Future = Future()
            try:
                future.set_result(fn(**kwargs))
            except BaseException as exc:  # noqa: BLE001 - test executor must preserve worker failure shape.
                future.set_exception(exc)
            return future

    monkeypatch.setattr(laptop_temp_module, "ProcessPoolExecutor", FakeProcessPoolExecutor)

    result = laptop_temp_module.laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="failure-proof",
        chunk_mb=1,
        max_chunks=2,
        workers=2,
        reserve_ram_fraction=0.0,
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


def test_laptop_temp_intake_oversized_skip_records_file_failure(tmp_path: Path) -> None:
    source = tmp_path / "large.txt"
    source.write_text("Alpha beta gamma.\n" * 200, encoding="utf-8")
    state_root = tmp_path / "State" / "laptop_temp_intake"

    result = laptop_temp_intake(
        source,
        state_root=state_root,
        run_id="oversized-skip",
        chunk_mb=1,
        max_chunks=3,
        workers=2,
        reserve_ram_fraction=0.0,
        max_file_mb=0.0001,
        oversized_file_policy="skip",
        show_progress=False,
    )

    assert result["chunks_seen"] == 0
    assert result["chunks_created"] == 0
    assert result["file_failures"] == 1
    assert result["production_merge"] is False
    assert result["global_lifetime_write"] is False
    failure_rows = (state_root / "oversized-skip" / "file_failures.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(failure_rows) == 1
    failure = json.loads(failure_rows[0])
    assert failure["schema"] == "awrag_laptop_temp_file_failure@1"
    assert failure["policy"] == "skip"
    events = [json.loads(line)["event"] for line in (state_root / "oversized-skip" / "run_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert "file_policy_applied" in events


def test_laptop_temp_intake_refuses_when_available_ram_is_below_reserve(monkeypatch) -> None:
    monkeypatch.setattr(
        laptop_temp_module,
        "_detect_system_resources",
        lambda: {
            "logical_cpu_count": 8,
            "total_ram_bytes": 16 * 1024 * 1024 * 1024,
            "available_ram_bytes": 2 * 1024 * 1024 * 1024,
            "detection_method": "test",
        },
    )

    with pytest.raises(MemoryError):
        laptop_temp_module._build_resource_plan(
            chunk_limit=1024 * 1024,
            requested_workers="auto",
            reserve_ram_fraction=0.50,
            reserve_ram_gb=None,
            refuse_below_reserve=True,
        )


def test_laptop_temp_intake_cli_operator_summary_mode(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Alpha beta.\n\nGamma delta.", encoding="utf-8")
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
            "summary-proof",
            "--chunk-mb",
            "1",
            "--max-chunks",
            "1",
            "--workers",
            "2",
            "--reserve-ram-fraction",
            "0",
            "--progress-snapshot-interval-sec",
            "0",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert "AWRAG laptop-temp-intake complete" in completed.stdout
    assert "progress:" in completed.stdout
    assert (state_root / "summary-proof" / "progress.json").is_file()


def test_laptop_temp_intake_external_launcher_is_present() -> None:
    script = Path(__file__).resolve().parents[1] / "Start_Laptop_Temp_Intake.ps1"
    text = script.read_text(encoding="utf-8")

    assert "Start-Process" in text
    assert "laptop-temp-intake" in text
    assert "--workers" in text
    assert "--reserve-ram-fraction" in text
    assert "--progress-snapshot-interval-sec" in text
    assert "progress.json" in text
