from __future__ import annotations

import pytest

from awrag.engine.hardware import enforce_minimum_runtime_requirements

GIB = 1024 * 1024 * 1024


def _resources(*, cpu: int = 4, ram_gib: int = 8, gpu_gib: int = 8) -> dict[str, object]:
    return {
        "logical_cpu_count": cpu,
        "total_ram_bytes": ram_gib * GIB,
        "available_ram_bytes": ram_gib * GIB,
        "ram_detection_method": "test",
        "gpu_detection_method": "test",
        "gpu_devices": [{"name": "test gpu", "memory_total_bytes": gpu_gib * GIB}],
        "max_gpu_memory_bytes": gpu_gib * GIB,
    }


def test_minimum_runtime_requirements_accept_four_cpu_eight_ram_eight_gpu() -> None:
    enforce_minimum_runtime_requirements(_resources(cpu=4, ram_gib=8, gpu_gib=8))


def test_minimum_runtime_requirements_reject_cpu_below_four() -> None:
    with pytest.raises(RuntimeError, match="logical_cpu_count=3 below minimum 4"):
        enforce_minimum_runtime_requirements(_resources(cpu=3, ram_gib=8, gpu_gib=8))


def test_minimum_runtime_requirements_reject_ram_below_eight_gib() -> None:
    with pytest.raises(RuntimeError, match="system_ram_bytes=.*below minimum"):
        enforce_minimum_runtime_requirements(_resources(cpu=4, ram_gib=7, gpu_gib=8))


def test_minimum_runtime_requirements_reject_gpu_below_eight_gib() -> None:
    with pytest.raises(RuntimeError, match="max_gpu_memory_bytes=.*below minimum"):
        enforce_minimum_runtime_requirements(_resources(cpu=4, ram_gib=8, gpu_gib=7))
