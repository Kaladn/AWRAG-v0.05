from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .anchors import SYMBOL_BYTES, SYMBOL_SYSTEM, symbol_for
from .base import DatasetPaths, dataset_paths, safe_id, with_protected_notice, write_json
from .native import NATIVE_COMPUTE_ENGINE, native_executable_path, run_native_counts


@dataclass(frozen=True)
class NativeRecordContract:
    size: int


ANCHOR_RECORD = NativeRecordContract(14)
RELATION_RECORD = NativeRecordContract(18)
BLOCK_ANCHOR_RECORD = NativeRecordContract(12)


def ensure_dataset(runtime_root: str | Path, dataset_id: str, *, owner: str = "operator_defined") -> dict[str, Any]:
    run_native_counts([
        "init",
        "--runtime-root",
        str(runtime_root),
        "--dataset-id",
        dataset_id,
        "--owner",
        owner,
    ])
    return status(runtime_root, dataset_id)


def status(runtime_root: str | Path, dataset_id: str) -> dict[str, Any]:
    return run_native_counts([
        "status",
        "--runtime-root",
        str(runtime_root),
        "--dataset-id",
        dataset_id,
    ])


def touch_binary_files(paths: DatasetPaths) -> None:
    for path in (paths.counts, paths.state, paths.coordinates, paths.citations, paths.outputs, paths.receipts):
        path.mkdir(parents=True, exist_ok=True)
    for path in (paths.anchor_counts_path, paths.relation_counts_path, paths.block_anchor_path, paths.blocks_path):
        path.touch(exist_ok=True)


def record_count(path: Path, record_size: int) -> int:
    if not path.exists():
        return 0
    return path.stat().st_size // record_size


def jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def read_blocks(paths: DatasetPaths) -> dict[int, dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    if not paths.blocks_path.exists():
        return blocks
    for line in paths.blocks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        blocks[int(row["block_ordinal"])] = row
    return blocks


def read_symbol_to_anchor(paths: DatasetPaths) -> dict[str, str]:
    if not paths.lexicon_path.exists():
        return {}
    payload = json.loads(paths.lexicon_path.read_text(encoding="utf-8"))
    return {str(row["symbol"]): str(row["anchor"]) for row in payload.get("anchors", [])}


def write_lexicon(paths: DatasetPaths, anchors: Counter[str]) -> None:
    rows = [
        {
            "anchor": anchor,
            "symbol": symbol_for(anchor),
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
            "observations": int(observations),
            "scope": "dataset_local",
            "symbol_scope": "dataset_local_demo_only",
            "transferable": False,
            "lifetime_allowed": False,
            "anchorworks_lifetime_symbol_compatible": False,
            "promotion_allowed": False,
        }
        for anchor, observations in sorted(anchors.items())
    ]
    write_json(paths.lexicon_path, {
        "schema": "awrag_dataset_lexicon@1",
        "dataset_id": paths.root.name,
        "scope": "dataset_local",
        "symbol_system": SYMBOL_SYSTEM,
        "symbol_bytes": SYMBOL_BYTES,
        "symbol_scope": "dataset_local_demo_only",
        "symbol_transferable": False,
        "lifetime_allowed": False,
        "anchorworks_lifetime_symbol_compatible": False,
        "compute_engine": NATIVE_COMPUTE_ENGINE,
        "anchor_count": len(rows),
        "anchors": rows,
    })


def write_blocks_jsonl(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    paths.blocks_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.blocks_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in blocks:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_citation_jsonl(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    path = paths.citations / "citations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in blocks:
            handle.write(json.dumps(with_protected_notice(row), ensure_ascii=True) + "\n")


def write_coordinate_index(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    path = paths.coordinates / "coordinate_index.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in blocks:
            handle.write(json.dumps(with_protected_notice(row), ensure_ascii=True) + "\n")


def write_chat_metadata_index(paths: DatasetPaths, rows: list[dict[str, Any]]) -> None:
    path = paths.chat_metadata_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(with_protected_notice(row), ensure_ascii=True) + "\n")


def write_binary_counts(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("AWRAG binary counts are written only by the native C++ compute engine")


def iter_anchor_records(*_args: Any, **_kwargs: Any) -> Iterable[tuple[bytes, int]]:
    raise RuntimeError("AWRAG count walking is owned by the native C++ compute engine")


def iter_relation_records(*_args: Any, **_kwargs: Any) -> Iterable[tuple[bytes, bytes, int, int]]:
    raise RuntimeError("AWRAG count walking is owned by the native C++ compute engine")


def read_block_anchor_rows(*_args: Any, **_kwargs: Any) -> list[tuple[bytes, int, int]]:
    raise RuntimeError("AWRAG block-anchor count walking is owned by the native C++ compute engine")
