from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


NATIVE_COMPUTE_ENGINE = "awrag_native_cpp_counts@1"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def native_source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "native" / "awrag_counts"


def native_build_root() -> Path:
    return repo_root() / "build" / "native_awrag_counts"


def native_executable_path() -> Path:
    for root in (repo_root() / "build").glob("native_awrag_counts_*"):
        exe = root / "Release" / "awrag-counts.exe"
        if exe.exists():
            return exe
    return native_build_root() / "Release" / "awrag-counts.exe"


def build_native_counts() -> Path:
    exe = native_executable_path()
    source_files = list(native_source_dir().rglob("*"))
    latest_source_mtime = max((path.stat().st_mtime for path in source_files if path.is_file()), default=0.0)
    if exe.exists() and exe.stat().st_mtime >= latest_source_mtime:
        return exe
    source = native_source_dir()
    build_base = repo_root() / "build"
    build_base.mkdir(parents=True, exist_ok=True)
    configured = False
    last_error: subprocess.CalledProcessError | None = None
    generators = (
        ("Visual Studio 18 2026", "vs2026"),
        ("Visual Studio 17 2022", "vs2022"),
    )
    for generator, suffix in generators:
        build = build_base / f"native_awrag_counts_{suffix}"
        build.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["cmake", "-S", str(source), "-B", str(build), "-G", generator, "-A", "x64"],
                check=True,
                cwd=repo_root(),
            )
            subprocess.run(["cmake", "--build", str(build), "--config", "Release"], check=True, cwd=repo_root())
            exe = build / "Release" / "awrag-counts.exe"
            if exe.exists():
                return exe
            configured = True
            raise FileNotFoundError(exe)
        except subprocess.CalledProcessError as exc:
            if configured:
                raise
            last_error = exc
    if not configured:
        assert last_error is not None
        raise last_error
    raise FileNotFoundError(native_executable_path())


def run_native_counts(args: list[str]) -> dict[str, Any]:
    exe = build_native_counts()
    completed = subprocess.run(
        [str(exe), *args],
        check=True,
        cwd=repo_root(),
        text=True,
        capture_output=True,
    )
    output = completed.stdout.strip()
    if not output:
        return {"ok": True, "compute_engine": NATIVE_COMPUTE_ENGINE}
    return json.loads(output.splitlines()[-1])
