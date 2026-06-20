from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .anchors import anchorize, assert_no_symbol_collisions
from .base import MAX_BLOCK_LINES, public_paths, safe_id, sha1_text, utc_now, unique_stamp, with_protected_notice
from .base import COUNT_BACKEND, dataset_paths, write_json
from .chat import parse_chat_metadata_block
from .storage import (
    ensure_dataset,
    write_binary_counts,
    write_blocks_jsonl,
    write_chat_metadata_index,
    write_citation_jsonl,
    write_coordinate_index,
    write_lexicon,
)


def intake(runtime_root: str | Path, dataset_id: str, source: str | Path, *, owner: str = "operator_defined", window: int = 6) -> dict[str, Any]:
    ensure_dataset(runtime_root, dataset_id, owner=owner)
    paths = dataset_paths(runtime_root, dataset_id)
    source_path = Path(source).expanduser().resolve()
    files = list(iter_files(source_path))
    if not files:
        raise FileNotFoundError(source_path)

    anchor_observations: Counter[str] = Counter()
    relation_observations: Counter[tuple[str, str, int]] = Counter()
    block_anchor_rows: list[tuple[str, int, int]] = []
    block_rows: list[dict[str, Any]] = []
    chat_metadata_rows: list[dict[str, Any]] = []
    source_receipts: list[dict[str, Any]] = []

    for file_path in files:
        file_digest = sha1_text(str(file_path))
        text = file_path.read_text(encoding="utf-8", errors="replace")
        blocks = split_blocks(text)
        source_receipts.append({"path": str(file_path), "block_count": len(blocks)})
        active_chat_metadata: dict[str, Any] = {}
        for block_index, block in enumerate(blocks, start=1):
            block_ordinal = len(block_rows)
            block_id = f"{file_digest}:{block_index}"
            parsed_metadata = parse_chat_metadata_block(block["text"])
            if parsed_metadata:
                active_chat_metadata = parsed_metadata
            anchors = anchorize(block["text"])
            citation_id = f"AWCIT-{sha1_text(block_id)[:10]}"
            block_row = {
                "block_ordinal": block_ordinal,
                "block_id": block_id,
                "file_path": str(file_path),
                "line_start": block["line_start"],
                "line_end": block["line_end"],
                "text": block["text"],
                "citation_id": citation_id,
                "marker": f"[{citation_id}]",
                "text_hash": sha1_text(block["text"]),
            }
            if active_chat_metadata:
                block_row["chat_metadata"] = dict(active_chat_metadata)
                chat_metadata_rows.append({
                    "schema": "awrag_chat_metadata_index_row@1",
                    "dataset_id": safe_id(dataset_id),
                    "scope": "dataset_local",
                    "block_ordinal": block_ordinal,
                    "block_id": block_id,
                    "citation_id": citation_id,
                    "marker": f"[{citation_id}]",
                    "file_path": str(file_path),
                    "line_start": block["line_start"],
                    "line_end": block["line_end"],
                    **active_chat_metadata,
                })
            block_rows.append(block_row)
            for position, anchor in enumerate(anchors):
                anchor_observations[anchor] += 1
                block_anchor_rows.append((anchor, block_ordinal, position))
                for offset in range(-window, window + 1):
                    if offset == 0:
                        continue
                    neighbor_index = position + offset
                    if 0 <= neighbor_index < len(anchors):
                        relation_observations[(anchor, anchors[neighbor_index], offset)] += 1

    assert_no_symbol_collisions(anchor_observations)
    write_binary_counts(paths, anchor_observations, relation_observations, block_anchor_rows)
    write_blocks_jsonl(paths, block_rows)
    write_lexicon(paths, anchor_observations)
    write_citation_jsonl(paths, block_rows)
    write_coordinate_index(paths, block_rows)
    write_chat_metadata_index(paths, chat_metadata_rows)

    receipt = {
        "schema": "awrag_intake_receipt@1",
        "created_at": utc_now(),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "source": str(source_path),
        "source_file_count": len(files),
        "block_count": len(block_rows),
        "citation_count": len(block_rows),
        "chat_metadata_row_count": len(chat_metadata_rows),
        "unique_anchor_count": len(anchor_observations),
        "anchor_observation_count": sum(anchor_observations.values()),
        "relation_observation_count": sum(relation_observations.values()),
        "count_backend": COUNT_BACKEND,
        "persistent_memory": False,
        "promotion_allowed": False,
        "sources": source_receipts,
        "paths": public_paths(paths),
    }
    receipt_path = paths.receipts / f"intake_{unique_stamp()}.json"
    write_json(receipt_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    return with_protected_notice(receipt)

def iter_files(path: Path) -> Iterable[Path]:
    suffixes = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".jsonl"}
    if path.is_file() and path.suffix.lower() in suffixes:
        yield path
        return
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file() and item.suffix.lower() in suffixes and not any(part.startswith(".") for part in item.parts):
                yield item

def split_blocks(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    blocks: list[dict[str, Any]] = []
    current: list[str] = []
    start = 1
    for index, line in enumerate(lines, start=1):
        if line.strip():
            if not current:
                start = index
            current.append(line)
            continue
        if current:
            blocks.extend(chunk_block(current, start))
            current = []
    if current:
        blocks.extend(chunk_block(current, start))
    if not blocks and text:
        blocks.append({"line_start": 1, "line_end": max(1, len(lines)), "text": text})
    return blocks

def chunk_block(lines: list[str], start_line: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for offset in range(0, len(lines), MAX_BLOCK_LINES):
        chunk = lines[offset:offset + MAX_BLOCK_LINES]
        chunks.append({
            "line_start": start_line + offset,
            "line_end": start_line + offset + len(chunk) - 1,
            "text": "\n".join(chunk),
        })
    return chunks
