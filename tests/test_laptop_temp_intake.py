from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from awrag.engine.laptop_temp_intake import laptop_temp_intake


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
        show_progress=False,
    )

    run_root = state_root / "proof"
    chunks = run_root / "chunks"
    assert result["chunks_seen"] == 1
    assert result["chunks_created"] == 1
    assert result["chunks_skipped"] == 0
    assert result["receipt_verification"] == "passed"
    assert (run_root / "manifest.json").is_file()
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