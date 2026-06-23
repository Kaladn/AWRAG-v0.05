from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path

import pytest

from awrag.engine import intake
from awrag.engine import pipeline as pipeline_module
from awrag.engine.pipeline import _build_intake_resource_plan

GIB = 1024 * 1024 * 1024


def _test_resources(
    *,
    cpu: int = 8,
    total_gib: int = 16,
    available_gib: int = 14,
    gpu_gib: int = 8,
) -> dict[str, object]:
    return {
        "logical_cpu_count": cpu,
        "total_ram_bytes": total_gib * GIB,
        "available_ram_bytes": available_gib * GIB,
        "ram_detection_method": "test",
        "gpu_detection_method": "test",
        "gpu_devices": [{"name": "test gpu", "memory_total_bytes": gpu_gib * GIB}],
        "max_gpu_memory_bytes": gpu_gib * GIB,
    }


def test_intake_resource_plan_honors_four_workers_eight_gb_budget(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_module,
        "_detect_system_resources",
        lambda: _test_resources(),
    )
    files = []
    for index in range(4):
        path = tmp_path / f"source_{index}.txt"
        path.write_text("alpha beta", encoding="utf-8")
        files.append(path)

    plan = _build_intake_resource_plan(
        files=files,
        requested_workers=4,
        reserve_ram_fraction=0.15,
        ram_budget_gb=8,
    )

    assert plan["schema"] == "awrag_intake_resource_plan@1"
    assert plan["requested_workers"] == "4"
    assert plan["effective_workers"] == 4
    assert plan["ram_budget_gb"] == 8.0
    assert plan["reserve_ram_fraction"] == 0.15
    assert plan["parallel_execution"] is True
    assert plan["parallel_execution_possible"] is None
    assert plan["production_ingest"] is True
    assert plan["minimum_runtime_requirements_enforced"] is True
    assert plan["single_core_allowed"] is False


def test_intake_resource_plan_rejects_low_core() -> None:
    with pytest.raises(ValueError, match="single-core/low-core execution is not allowed"):
        _build_intake_resource_plan(
            files=[Path("source.txt")],
            requested_workers=3,
            reserve_ram_fraction=0.15,
            ram_budget_gb=8,
        )


def test_production_intake_preflight_rejects_machine_below_minimum(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_module,
        "_detect_system_resources",
        lambda: _test_resources(cpu=3, total_gib=16, available_gib=14, gpu_gib=8),
    )
    path = tmp_path / "source.txt"
    path.write_text("alpha beta", encoding="utf-8")

    with pytest.raises(RuntimeError, match="MINIMUM_RUNTIME_REQUIREMENTS_NOT_MET"):
        _build_intake_resource_plan(
            files=[path],
            requested_workers=4,
            reserve_ram_fraction=0.15,
            ram_budget_gb=8,
        )


def test_debug_tiny_single_core_is_explicit_and_nonproduction(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_module,
        "_detect_system_resources",
        lambda: _test_resources(cpu=1, total_gib=2, available_gib=1, gpu_gib=0),
    )
    source = tmp_path / "tiny.md"
    source.write_text("Alpha beta debug block.", encoding="utf-8")

    result = intake(
        tmp_path / "runtime",
        "debug_tiny",
        source,
        workers=1,
        reserve_ram_fraction=0.15,
        ram_budget_gb=1,
        debug_tiny_single_core=True,
    )

    assert result["intake_engine"] == "awrag_debug_tiny_block_intake@1"
    assert result["production_ingest"] is False
    assert result["debug_tiny_single_core"] is True
    assert result["workers_effective"] == 1
    assert result["workers_actual"] == 1
    assert result["parallel_execution"] is False
    assert result["resource_plan"]["single_core_allowed"] is True
    assert result["resource_plan"]["minimum_runtime_requirements_enforced"] is False
    assert "debug_tiny_single_core_nonproduction" in result["resource_plan"]["safety_decisions"]


def test_parallel_intake_receipt_records_worker_and_ram_plan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_module,
        "_detect_system_resources",
        lambda: _test_resources(),
    )
    source = tmp_path / "source"
    source.mkdir()
    for index in range(4):
        (source / f"{index}.md").write_text(
            f"Uhaul trailer rental repeats in source {index}.\n\n"
            f"Counts create evidence trails in source {index}.",
            encoding="utf-8",
        )

    result = intake(
        tmp_path / "runtime",
        "parallel_intake",
        source,
        workers=4,
        reserve_ram_fraction=0.15,
        ram_budget_gb=8,
    )

    assert result["intake_engine"] == "awrag_parallel_block_intake@1"
    assert result["workers_requested"] == "4"
    assert result["workers_effective"] == 4
    assert result["parallel_execution"] is True
    assert result["parallel_execution_possible"] is True
    assert result["resource_plan"]["ram_budget_gb"] == 8.0
    assert result["resource_plan"]["reserve_ram_fraction"] == 0.15
    assert result["source_file_count"] == 4
    assert result["block_count"] == 8


def test_single_multiblock_source_still_uses_worker_pool(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_module,
        "_detect_system_resources",
        lambda: _test_resources(),
    )
    max_workers_seen: list[int] = []

    class FakeProcessPoolExecutor:
        def __init__(self, max_workers: int):
            max_workers_seen.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def submit(self, fn, *args):
            future: Future = Future()
            try:
                future.set_result(fn(*args))
            except BaseException as exc:  # noqa: BLE001 - test executor must preserve worker failure shape.
                future.set_exception(exc)
            return future

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", FakeProcessPoolExecutor)
    source = tmp_path / "single_source.md"
    source.write_text(
        "Alpha beta first block.\n\n"
        "Gamma delta second block.\n\n"
        "Evidence counts third block.\n\n"
        "Worker pool fourth block.",
        encoding="utf-8",
    )

    result = intake(
        tmp_path / "runtime",
        "single_multiblock",
        source,
        workers=4,
        reserve_ram_fraction=0.15,
        ram_budget_gb=8,
    )

    assert max_workers_seen == [4]
    assert result["source_file_count"] == 1
    assert result["workers_effective"] == 4
    assert result["parallel_execution"] is True
    assert result["block_count"] == 4
