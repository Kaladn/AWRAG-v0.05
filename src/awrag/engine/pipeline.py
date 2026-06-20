from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .base import MAX_BLOCK_LINES
from .native import run_native_counts


def intake(runtime_root: str | Path, dataset_id: str, source: str | Path, *, owner: str = "operator_defined", window: int = 6) -> dict[str, Any]:
    return run_native_counts([
        "intake",
        "--runtime-root",
        str(runtime_root),
        "--dataset-id",
        dataset_id,
        "--source",
        str(source),
        "--owner",
        owner,
        "--window",
        str(window),
    ])


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
