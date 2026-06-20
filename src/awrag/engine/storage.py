from __future__ import annotations

import json
import struct
from collections import Counter
from typing import Any, Iterable

from .anchors import SYMBOL_BYTES, SYMBOL_SYSTEM, symbol_bytes, symbol_for, symbol_hex
from .base import (
    COUNT_BACKEND,
    DatasetPaths,
    dataset_paths,
    public_paths,
    safe_id,
    utc_now,
    unique_stamp,
    with_protected_notice,
    write_json,
)

ANCHOR_RECORD = struct.Struct(">6sQ")
RELATION_RECORD = struct.Struct(">6s6shI")
BLOCK_ANCHOR_RECORD = struct.Struct(">6sIH")


def ensure_dataset(runtime_root: str | Path, dataset_id: str, *, owner: str = "operator_defined") -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    for path in (paths.root, paths.incoming, paths.state, paths.counts, paths.coordinates, paths.citations, paths.outputs, paths.receipts):
        path.mkdir(parents=True, exist_ok=True)
    if not paths.manifest_path.exists():
        write_json(paths.manifest_path, {
            "schema": "awrag_dataset_manifest@1",
            "created_at": utc_now(),
            "dataset_id": safe_id(dataset_id),
            "owner": owner,
            "scope": "dataset_local",
            "rag_allowed": True,
            "promotion_allowed": False,
            "global_training_allowed": False,
            "delete_with_dataset": True,
            "counts_are_memory": False,
            "counts_belong_to": "dataset",
            "count_backend": COUNT_BACKEND,
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
            "symbol_scope": "dataset_local_demo_only",
            "symbol_transferable": False,
            "anchorworks_lifetime_symbol_compatible": False,
        })
    if not paths.lexicon_path.exists():
        write_lexicon(paths, Counter())
    touch_binary_files(paths)
    return status(runtime_root, dataset_id)

def status(runtime_root: str | Path, dataset_id: str) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    touch_binary_files(paths)
    return with_protected_notice({
        "schema": "awrag_dataset_status@1",
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "dataset_root": str(paths.root),
        "count_backend": COUNT_BACKEND,
        "anchor_counts_path": str(paths.anchor_counts_path),
        "relation_counts_path": str(paths.relation_counts_path),
        "block_anchor_postings_path": str(paths.block_anchor_path),
        "dataset_lexicon_path": str(paths.lexicon_path),
        "anchor_count": record_count(paths.anchor_counts_path, ANCHOR_RECORD.size),
        "relation_count": record_count(paths.relation_counts_path, RELATION_RECORD.size),
        "block_anchor_posting_count": record_count(paths.block_anchor_path, BLOCK_ANCHOR_RECORD.size),
        "block_count": jsonl_count(paths.blocks_path),
        "citation_count": jsonl_count(paths.citations / "citations.jsonl"),
        "chat_metadata_row_count": jsonl_count(paths.chat_metadata_path),
        "chat_metadata_index_path": str(paths.chat_metadata_path),
        "persistent_memory": False,
    })

def touch_binary_files(paths: DatasetPaths) -> None:
    paths.counts.mkdir(parents=True, exist_ok=True)
    for path in (paths.anchor_counts_path, paths.relation_counts_path, paths.block_anchor_path):
        path.touch(exist_ok=True)
    paths.blocks_path.parent.mkdir(parents=True, exist_ok=True)
    paths.blocks_path.touch(exist_ok=True)

def write_binary_counts(
    paths: DatasetPaths,
    anchors: Counter[str],
    relations: Counter[tuple[str, str, int]],
    block_anchors: list[tuple[str, int, int]],
) -> None:
    paths.counts.mkdir(parents=True, exist_ok=True)
    with paths.anchor_counts_path.open("wb") as handle:
        for anchor, observations in sorted(anchors.items()):
            handle.write(ANCHOR_RECORD.pack(symbol_bytes(anchor), int(observations)))
    with paths.relation_counts_path.open("wb") as handle:
        for (anchor, neighbor, offset), observations in sorted(relations.items()):
            handle.write(RELATION_RECORD.pack(symbol_bytes(anchor), symbol_bytes(neighbor), int(offset), int(observations)))
    with paths.block_anchor_path.open("wb") as handle:
        for anchor, block_ordinal, position in sorted(block_anchors, key=lambda item: (symbol_for(item[0]), item[1], item[2])):
            handle.write(BLOCK_ANCHOR_RECORD.pack(symbol_bytes(anchor), int(block_ordinal), int(position)))

def iter_anchor_records(paths: DatasetPaths) -> Iterable[tuple[bytes, int]]:
    with paths.anchor_counts_path.open("rb") as handle:
        while chunk := handle.read(ANCHOR_RECORD.size):
            if len(chunk) == ANCHOR_RECORD.size:
                symbol, observations = ANCHOR_RECORD.unpack(chunk)
                yield symbol, int(observations)

def iter_relation_records(paths: DatasetPaths) -> Iterable[tuple[bytes, bytes, int, int]]:
    with paths.relation_counts_path.open("rb") as handle:
        while chunk := handle.read(RELATION_RECORD.size):
            if len(chunk) == RELATION_RECORD.size:
                anchor, neighbor, offset, observations = RELATION_RECORD.unpack(chunk)
                yield anchor, neighbor, int(offset), int(observations)

def read_block_anchor_rows(paths: DatasetPaths) -> list[tuple[bytes, int, int]]:
    rows: list[tuple[bytes, int, int]] = []
    with paths.block_anchor_path.open("rb") as handle:
        while chunk := handle.read(BLOCK_ANCHOR_RECORD.size):
            if len(chunk) == BLOCK_ANCHOR_RECORD.size:
                symbol, block_ordinal, position = BLOCK_ANCHOR_RECORD.unpack(chunk)
                rows.append((symbol, int(block_ordinal), int(position)))
    return rows

def write_blocks_jsonl(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    paths.blocks_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.blocks_path.open("w", encoding="utf-8", newline="\n") as handle:
        for block in blocks:
            handle.write(json.dumps(block, ensure_ascii=True) + "\n")

def read_blocks(paths: DatasetPaths) -> dict[int, dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    if not paths.blocks_path.exists():
        return blocks
    for line in paths.blocks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        block = json.loads(line)
        blocks[int(block["block_ordinal"])] = block
    return blocks

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
        "anchor_count": len(rows),
        "anchors": rows,
    })

def read_symbol_to_anchor(paths: DatasetPaths) -> dict[str, str]:
    if not paths.lexicon_path.exists():
        return {}
    payload = json.loads(paths.lexicon_path.read_text(encoding="utf-8"))
    return {str(row["symbol"]): str(row["anchor"]) for row in payload.get("anchors", [])}

def write_citation_jsonl(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    path = paths.citations / "citations.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(blocks, key=lambda item: str(item["citation_id"])):
            handle.write(json.dumps(with_protected_notice({
                "schema": "awrag_citation@1",
                "citation_id": row["citation_id"],
                "marker": row["marker"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "text_hash": row["text_hash"],
                "scope": "dataset_local",
            }), ensure_ascii=True) + "\n")

def write_coordinate_index(paths: DatasetPaths, blocks: list[dict[str, Any]]) -> None:
    path = paths.coordinates / "coordinate_index.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(blocks, key=lambda item: (str(item["file_path"]), int(item["line_start"]))):
            handle.write(json.dumps(with_protected_notice({
                "schema": "awrag_coordinate@1",
                "block_id": row["block_id"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "citation_id": row["citation_id"],
                "scope": "dataset_local",
            }), ensure_ascii=True) + "\n")

def write_chat_metadata_index(paths: DatasetPaths, rows: list[dict[str, Any]]) -> None:
    path = paths.chat_metadata_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=lambda item: (str(item.get("created_at", "")), int(item["block_ordinal"]))):
            handle.write(json.dumps(with_protected_notice(row), ensure_ascii=True) + "\n")

def record_count(path: Path, record_size: int) -> int:
    if not path.exists():
        return 0
    return path.stat().st_size // record_size

def jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

