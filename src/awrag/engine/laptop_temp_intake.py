from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from tqdm import tqdm

from .anchors import anchorize, assert_no_symbol_collisions, symbol_bytes, symbol_for
from .base import COUNT_BACKEND, SYMBOL_BYTES, SYMBOL_SYSTEM, safe_id, utc_now, unique_stamp, write_json
from .pipeline import split_blocks
from .storage import ANCHOR_RECORD, RELATION_RECORD

COUNT_MAGIC = b"AWLTCOUNT1\n"


def laptop_temp_intake(
    source: str | Path,
    *,
    state_root: str | Path = "State/laptop_temp_intake",
    run_id: str | None = None,
    chunk_mb: int = 50,
    max_chunks: int | None = None,
    window: int = 6,
    show_progress: bool = True,
    resume: bool = True,
) -> dict[str, Any]:
    """Prepare bounded, disposable chunk artifacts without touching production counts."""
    if chunk_mb <= 0:
        raise ValueError("chunk_mb must be positive")
    if max_chunks is not None and max_chunks < 0:
        raise ValueError("max_chunks cannot be negative")
    if window <= 0:
        raise ValueError("window must be positive")

    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    run_name = safe_id(run_id or unique_stamp())
    root = Path(state_root).expanduser().resolve() / run_name
    chunks_root = root / "chunks"
    chunks_root.mkdir(parents=True, exist_ok=True)

    files = list(_iter_source_files(source_path))
    if not files:
        raise FileNotFoundError(f"no source files found under {source_path}")

    chunk_limit = chunk_mb * 1024 * 1024
    manifest = {
        "schema": "awrag_laptop_temp_intake_manifest@1",
        "created_at": utc_now(),
        "run_id": run_name,
        "source": str(source_path),
        "state_root": str(root),
        "mode": "laptop_temp_chunk_prep",
        "production_merge": False,
        "global_lifetime_write": False,
        "count_backend": COUNT_BACKEND,
        "symbol_system": SYMBOL_SYSTEM,
        "symbol_bytes": SYMBOL_BYTES,
        "chunk_mb": int(chunk_mb),
        "max_chunks": max_chunks,
        "window": int(window),
        "resume": bool(resume),
        "files_found": len(files),
    }
    write_json(root / "manifest.json", manifest)
    write_json(root / "source_receipt.json", {
        "schema": "awrag_laptop_temp_intake_source_receipt@1",
        "created_at": utc_now(),
        "run_id": run_name,
        "source": str(source_path),
        "files": [{"path": str(path), "bytes": path.stat().st_size} for path in files],
    })

    total_chunks = _estimate_chunks(files, chunk_limit, max_chunks)
    bar = tqdm(total=total_chunks, unit="chunk", desc="laptop-temp-intake", disable=not show_progress)

    chunk_receipts: list[dict[str, Any]] = []
    aggregate = Counter()
    processed_chunks = 0
    skipped_chunks = 0
    chunk_index = 0
    try:
        for file_path in files:
            for chunk_bytes in _read_byte_chunks(file_path, chunk_limit):
                if max_chunks is not None and chunk_index >= max_chunks:
                    break
                chunk_index += 1
                existing_receipt = _load_verified_chunk_receipt(chunks_root, chunk_index) if resume else None
                if existing_receipt is not None:
                    receipt = dict(existing_receipt)
                    receipt["resume_status"] = "skipped_completed"
                    skipped_chunks += 1
                else:
                    receipt = _process_chunk(
                        chunk_index=chunk_index,
                        chunk_bytes=chunk_bytes,
                        source_file=file_path,
                        chunks_root=chunks_root,
                        window=window,
                    )
                    if not _verify_chunk_receipt(receipt):
                        raise RuntimeError(f"chunk receipt verification failed for chunk {chunk_index}")
                    receipt["resume_status"] = "processed"
                    processed_chunks += 1

                chunk_receipts.append(receipt)
                aggregate["raw_bytes"] += int(receipt["raw_bytes"])
                aggregate["anchors"] += int(receipt["anchor_observations"])
                aggregate["unique_anchors"] += int(receipt["unique_anchors"])
                aggregate["relations"] += int(receipt["relation_observations"])
                aggregate["symbol_bytes_written"] += int(receipt["symbol_bytes_written"])
                bar.update(1)
                bar.set_postfix({
                    "anchors": aggregate["anchors"],
                    "skipped": skipped_chunks,
                    "relations": aggregate["relations"],
                })
            if max_chunks is not None and chunk_index >= max_chunks:
                break
    finally:
        bar.close()

    summary = {
        "schema": "awrag_laptop_temp_intake_summary@1",
        "created_at": utc_now(),
        "run_id": run_name,
        "state_root": str(root),
        "chunks_seen": len(chunk_receipts),
        "chunks_created": int(processed_chunks),
        "chunks_skipped": int(skipped_chunks),
        "raw_bytes": int(aggregate["raw_bytes"]),
        "anchor_observations": int(aggregate["anchors"]),
        "unique_anchor_sum_by_chunk": int(aggregate["unique_anchors"]),
        "relation_observations": int(aggregate["relations"]),
        "symbol_bytes_written": int(aggregate["symbol_bytes_written"]),
        "receipt_verification": "passed",
        "production_merge": False,
        "global_lifetime_write": False,
        "artifacts": {
            "manifest": str(root / "manifest.json"),
            "source_receipt": str(root / "source_receipt.json"),
            "chunk_receipts": str(root / "chunk_receipts.jsonl"),
            "chunks": str(chunks_root),
        },
    }
    _write_jsonl(root / "chunk_receipts.jsonl", chunk_receipts)
    write_json(root / "run_summary.json", summary)
    return summary


def _process_chunk(
    *,
    chunk_index: int,
    chunk_bytes: bytes,
    source_file: Path,
    chunks_root: Path,
    window: int,
) -> dict[str, Any]:
    stem = f"chunk_{chunk_index:06d}"
    raw_path = chunks_root / f"{stem}.raw"
    symbols_path = chunks_root / f"{stem}.symbols.bin"
    lexicon_path = chunks_root / f"{stem}.lexicon_delta.json"
    counts_path = chunks_root / f"{stem}.counts.bin"
    receipt_path = chunks_root / f"{stem}.receipt.json"

    raw_path.write_bytes(chunk_bytes)
    input_mode = "symbolized_binary" if _looks_symbolized(source_file, chunk_bytes) else "raw_text"

    if input_mode == "symbolized_binary":
        symbols = _symbol_stream(chunk_bytes)
        symbols_path.write_bytes(b"".join(symbols))
        anchor_counts: Counter[str] = Counter()
        _write_symbol_count_artifact(counts_path, symbols, window=window)
        write_json(lexicon_path, {
            "schema": "awrag_laptop_temp_chunk_lexicon_delta@1",
            "chunk_index": chunk_index,
            "source_file": str(source_file),
            "input_mode": input_mode,
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
            "anchor_count": 0,
            "anchors": [],
            "note": "Input was already symbolized; no anchor strings were assigned in this chunk.",
        })
        anchor_observations = len(symbols)
        relation_observations = _symbol_relation_observation_count(len(symbols), window=window)
    else:
        text = chunk_bytes.decode("utf-8", errors="replace")
        anchors = _anchors_from_text(text)
        anchor_counts = Counter(anchors)
        assert_no_symbol_collisions(anchor_counts)
        relations = _relation_counts(anchors, window=window)
        with symbols_path.open("wb") as handle:
            for anchor in anchors:
                handle.write(symbol_bytes(anchor))
        write_json(lexicon_path, {
            "schema": "awrag_laptop_temp_chunk_lexicon_delta@1",
            "chunk_index": chunk_index,
            "source_file": str(source_file),
            "input_mode": input_mode,
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
            "anchor_count": len(anchor_counts),
            "anchors": [
                {
                    "anchor": anchor,
                    "symbol": symbol_for(anchor),
                    "observations": int(count),
                    "scope": "chunk_local_temp",
                }
                for anchor, count in sorted(anchor_counts.items())
            ],
        })
        _write_count_artifact(counts_path, anchor_counts, relations)
        anchor_observations = len(anchors)
        relation_observations = sum(relations.values())

    receipt = {
        "schema": "awrag_laptop_temp_chunk_receipt@1",
        "created_at": utc_now(),
        "chunk_index": chunk_index,
        "source_file": str(source_file),
        "input_mode": input_mode,
        "raw_bytes": len(chunk_bytes),
        "raw_path": str(raw_path),
        "symbols_path": str(symbols_path),
        "lexicon_delta_path": str(lexicon_path),
        "counts_path": str(counts_path),
        "receipt_path": str(receipt_path),
        "anchor_observations": anchor_observations,
        "unique_anchors": len(anchor_counts),
        "relation_observations": relation_observations,
        "symbol_bytes_written": symbols_path.stat().st_size,
        "counts_bytes_written": counts_path.stat().st_size,
        "production_merge": False,
        "global_lifetime_write": False,
    }
    write_json(receipt_path, receipt)
    return receipt


def _load_verified_chunk_receipt(chunks_root: Path, chunk_index: int) -> dict[str, Any] | None:
    receipt_path = chunks_root / f"chunk_{chunk_index:06d}.receipt.json"
    if not receipt_path.exists():
        return None
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not _verify_chunk_receipt(receipt):
        return None
    return receipt


def _verify_chunk_receipt(receipt: dict[str, Any]) -> bool:
    if receipt.get("schema") != "awrag_laptop_temp_chunk_receipt@1":
        return False
    if receipt.get("production_merge") is not False:
        return False
    if receipt.get("global_lifetime_write") is not False:
        return False

    raw_path = Path(str(receipt.get("raw_path", "")))
    symbols_path = Path(str(receipt.get("symbols_path", "")))
    lexicon_path = Path(str(receipt.get("lexicon_delta_path", "")))
    counts_path = Path(str(receipt.get("counts_path", "")))
    receipt_path = Path(str(receipt.get("receipt_path", "")))
    paths = [raw_path, symbols_path, lexicon_path, counts_path, receipt_path]
    if any(not path.exists() or not path.is_file() or path.stat().st_size <= 0 for path in paths):
        return False
    if int(receipt.get("symbol_bytes_written", -1)) != symbols_path.stat().st_size:
        return False
    if int(receipt.get("counts_bytes_written", -1)) != counts_path.stat().st_size:
        return False
    return True


def _anchors_from_text(text: str) -> list[str]:
    anchors: list[str] = []
    for block in split_blocks(text):
        anchors.extend(anchorize(str(block["text"])))
    return anchors


def _relation_counts(anchors: list[str], *, window: int) -> Counter[tuple[str, str, int]]:
    out: Counter[tuple[str, str, int]] = Counter()
    for position, anchor in enumerate(anchors):
        for offset in range(-window, window + 1):
            if offset == 0:
                continue
            neighbor_index = position + offset
            if 0 <= neighbor_index < len(anchors):
                out[(anchor, anchors[neighbor_index], offset)] += 1
    return out


def _write_count_artifact(path: Path, anchors: Counter[str], relations: Counter[tuple[str, str, int]]) -> None:
    header = {
        "schema": "awrag_laptop_temp_chunk_counts_bin@1",
        "count_backend": COUNT_BACKEND,
        "symbol_system": SYMBOL_SYSTEM,
        "symbol_bytes": SYMBOL_BYTES,
        "input_mode": "raw_text",
        "anchor_record_size": ANCHOR_RECORD.size,
        "relation_record_size": RELATION_RECORD.size,
        "anchor_records": len(anchors),
        "relation_records": len(relations),
    }
    with path.open("wb") as handle:
        _write_count_header(handle, header)
        for anchor, observations in sorted(anchors.items()):
            handle.write(ANCHOR_RECORD.pack(symbol_bytes(anchor), int(observations)))
        for (anchor, neighbor, offset), observations in sorted(relations.items()):
            handle.write(RELATION_RECORD.pack(symbol_bytes(anchor), symbol_bytes(neighbor), int(offset), int(observations)))


def _write_symbol_count_artifact(path: Path, symbols: list[bytes], *, window: int) -> None:
    symbol_counts = Counter(symbols)
    relation_counts: Counter[tuple[bytes, bytes, int]] = Counter()
    for position, symbol in enumerate(symbols):
        for offset in range(-window, window + 1):
            if offset == 0:
                continue
            neighbor_index = position + offset
            if 0 <= neighbor_index < len(symbols):
                relation_counts[(symbol, symbols[neighbor_index], offset)] += 1
    header = {
        "schema": "awrag_laptop_temp_chunk_counts_bin@1",
        "count_backend": COUNT_BACKEND,
        "symbol_system": SYMBOL_SYSTEM,
        "symbol_bytes": SYMBOL_BYTES,
        "input_mode": "symbolized_binary",
        "anchor_record_size": ANCHOR_RECORD.size,
        "relation_record_size": RELATION_RECORD.size,
        "anchor_records": len(symbol_counts),
        "relation_records": len(relation_counts),
    }
    with path.open("wb") as handle:
        _write_count_header(handle, header)
        for symbol, observations in sorted(symbol_counts.items()):
            handle.write(ANCHOR_RECORD.pack(symbol, int(observations)))
        for (symbol, neighbor, offset), observations in sorted(relation_counts.items()):
            handle.write(RELATION_RECORD.pack(symbol, neighbor, int(offset), int(observations)))


def _write_count_header(handle: Any, header: dict[str, Any]) -> None:
    header_bytes = json.dumps(header, ensure_ascii=True, sort_keys=True).encode("utf-8")
    handle.write(COUNT_MAGIC)
    handle.write(struct.pack(">I", len(header_bytes)))
    handle.write(header_bytes)


def _looks_symbolized(source_file: Path, chunk_bytes: bytes) -> bool:
    return source_file.name.endswith(".symbols.bin") and len(chunk_bytes) >= SYMBOL_BYTES


def _symbol_stream(chunk_bytes: bytes) -> list[bytes]:
    usable = len(chunk_bytes) - (len(chunk_bytes) % SYMBOL_BYTES)
    return [chunk_bytes[index:index + SYMBOL_BYTES] for index in range(0, usable, SYMBOL_BYTES)]


def _symbol_relation_observation_count(symbol_count: int, *, window: int) -> int:
    total = 0
    for position in range(symbol_count):
        total += min(window, position)
        total += min(window, symbol_count - position - 1)
    return total


def _iter_source_files(source: Path) -> Iterable[Path]:
    if source.is_file():
        yield source
        return
    for path in sorted(source.rglob("*")):
        if path.is_file():
            yield path


def _read_byte_chunks(path: Path, chunk_size: int) -> Iterable[bytes]:
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            yield chunk


def _estimate_chunks(files: list[Path], chunk_size: int, max_chunks: int | None) -> int:
    total = 0
    for path in files:
        size = path.stat().st_size
        total += max(1, (size + chunk_size - 1) // chunk_size)
        if max_chunks is not None and total >= max_chunks:
            return max_chunks
    return total


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")