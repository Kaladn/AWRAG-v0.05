from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import (  # noqa: E402
    COUNT_BACKEND,
    SYMBOL_BYTES,
    SYMBOL_SYSTEM,
    iter_relation_records,
    read_block_anchor_rows,
    read_blocks,
    read_symbol_to_anchor,
    symbol_bytes,
    symbol_hex,
    utc_now,
)
from experiments.aw_backend_tap import AwBackendTap

SCHEMA = "awrag_resident_dataset_tap@0"


@dataclass(frozen=True)
class ResidentLoadReceipt:
    schema: str
    created_at: str
    dataset_id: str
    count_backend: str
    symbol_system: str
    symbol_bytes: int
    locked: bool
    load_seconds: float
    index_seconds: float
    relation_rows_loaded: int
    relation_centers_loaded: int
    block_anchor_postings_loaded: int
    blocks_loaded: int
    symbols_loaded: int
    memory_estimate_bytes: int
    files: list[dict[str, Any]]


class ResidentDatasetTap:
    """Locked resident read view over AW dataset artifacts."""

    def __init__(self, backend: AwBackendTap) -> None:
        backend.require_ready()
        self.backend = backend
        self.runtime_root = backend.runtime_root
        self.dataset_id = backend.dataset_id
        self.paths = backend.paths
        self._locked = False
        load_started = perf_counter()
        self.symbol_to_anchor = read_symbol_to_anchor(self.paths)
        self.anchor_to_symbol = {
            anchor.lower(): bytes.fromhex(symbol[2:])
            for symbol, anchor in self.symbol_to_anchor.items()
            if symbol.startswith("0x")
        }
        self.blocks = read_blocks(self.paths)
        self.block_anchor_rows = read_block_anchor_rows(self.paths)
        self.block_sequences = self._block_anchor_sequences()
        self.citation_to_ordinal = {str(block.get("marker", "")): ordinal for ordinal, block in self.blocks.items()}
        self.block_id_to_ordinal = {str(block.get("block_id", "")): ordinal for ordinal, block in self.blocks.items()}
        index_started = perf_counter()
        self.anchor_to_blocks: dict[bytes, list[tuple[int, int]]] = defaultdict(list)
        self.block_to_anchor_rows: dict[int, list[tuple[int, bytes, str]]] = defaultdict(list)
        for symbol, block_ordinal, position in self.block_anchor_rows:
            anchor = self.symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol))
            self.anchor_to_blocks[symbol].append((block_ordinal, position))
            self.block_to_anchor_rows[block_ordinal].append((position, symbol, anchor))
        self.relations_by_center: dict[bytes, list[tuple[bytes, int, int]]] = defaultdict(list)
        relation_rows_loaded = 0
        for center_symbol, neighbor_symbol, offset, observations in iter_relation_records(self.paths):
            if offset == 0:
                continue
            self.relations_by_center[center_symbol].append((neighbor_symbol, offset, observations))
            relation_rows_loaded += 1
        self.relation_rows_loaded = relation_rows_loaded
        self.index_elapsed_seconds = round(perf_counter() - index_started, 6)
        self.load_elapsed_seconds = round(perf_counter() - load_started, 6)
        self._locked = True

    @property
    def locked(self) -> bool:
        return self._locked

    def load_stats(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "strategy": "native_awbin_loaded_once_in_ram",
            "dataset_id": self.dataset_id,
            "locked": self.locked,
            "relation_rows_loaded": self.relation_rows_loaded,
            "relation_centers_loaded": len(self.relations_by_center),
            "block_anchor_postings_loaded": len(self.block_anchor_rows),
            "blocks_loaded": len(self.blocks),
            "symbols_loaded": len(self.symbol_to_anchor),
            "load_elapsed_seconds": self.load_elapsed_seconds,
            "index_elapsed_seconds": self.index_elapsed_seconds,
            "memory_estimate_bytes": self.memory_estimate_bytes(),
            "count_backend": COUNT_BACKEND,
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
        }

    def load_receipt(self) -> ResidentLoadReceipt:
        stats = self.load_stats()
        return ResidentLoadReceipt(
            schema=SCHEMA,
            created_at=utc_now(),
            dataset_id=self.dataset_id,
            count_backend=COUNT_BACKEND,
            symbol_system=SYMBOL_SYSTEM,
            symbol_bytes=SYMBOL_BYTES,
            locked=self.locked,
            load_seconds=stats["load_elapsed_seconds"],
            index_seconds=stats["index_elapsed_seconds"],
            relation_rows_loaded=stats["relation_rows_loaded"],
            relation_centers_loaded=stats["relation_centers_loaded"],
            block_anchor_postings_loaded=stats["block_anchor_postings_loaded"],
            blocks_loaded=stats["blocks_loaded"],
            symbols_loaded=stats["symbols_loaded"],
            memory_estimate_bytes=stats["memory_estimate_bytes"],
            files=[row.__dict__ for row in self.backend.file_rows()],
        )

    def write_load_receipt(self, output_dir: str | Path) -> Path:
        target = Path(output_dir) / "resident_dataset_tap_load_receipt.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.load_receipt().__dict__, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return target

    def lookup_anchor_blocks(self, anchor_id: str | bytes, limit: int = 10) -> list[dict[str, Any]]:
        symbol = self._coerce_symbol(anchor_id)
        by_block: dict[int, list[int]] = defaultdict(list)
        for block_ordinal, position in self.anchor_to_blocks.get(symbol, []):
            by_block[block_ordinal].append(position)
        out = []
        for block_ordinal, positions in sorted(by_block.items(), key=lambda item: (-len(item[1]), item[0]))[:limit]:
            block = self.blocks.get(block_ordinal, {})
            out.append({
                "block_ordinal": block_ordinal,
                "block_id": block.get("block_id"),
                "citation": block.get("marker"),
                "file_path": block.get("file_path"),
                "line_start": block.get("line_start"),
                "line_end": block.get("line_end"),
                "positions": sorted(positions),
                "observation_count": len(positions),
            })
        return out

    def lookup_anchor_neighbors(self, anchor_id: str | bytes, limit: int = 10) -> list[dict[str, Any]]:
        symbol = self._coerce_symbol(anchor_id)
        counts: Counter[tuple[bytes, int]] = Counter()
        for neighbor_symbol, offset, observations in self.relations_by_center.get(symbol, []):
            counts[(neighbor_symbol, offset)] += observations
        return [
            {
                "anchor": self.symbol_to_anchor.get(symbol_hex(neighbor_symbol), symbol_hex(neighbor_symbol)),
                "symbol": symbol_hex(neighbor_symbol),
                "relative_position": offset,
                "observations": observations,
            }
            for (neighbor_symbol, offset), observations in counts.most_common(limit)
        ]

    def lookup_block_anchors(self, block_id: str | int, limit: int = 50) -> list[dict[str, Any]]:
        block_ordinal = self._coerce_block_ordinal(block_id)
        return [
            {"position": position, "anchor": anchor, "symbol": symbol_hex(symbol)}
            for position, symbol, anchor in sorted(self.block_to_anchor_rows.get(block_ordinal, []))[:limit]
        ]

    def get_citation(self, block_or_citation_id: str | int) -> dict[str, Any] | None:
        if isinstance(block_or_citation_id, int):
            block = self.blocks.get(block_or_citation_id)
            return self._citation_from_block(block_or_citation_id, block) if block else None
        value = str(block_or_citation_id)
        block_ordinal = self.citation_to_ordinal.get(value)
        if block_ordinal is None:
            block_ordinal = self.block_id_to_ordinal.get(value)
        if block_ordinal is None:
            for ordinal, block in self.blocks.items():
                if str(block.get("citation_id")) == value:
                    block_ordinal = ordinal
                    break
        if block_ordinal is None:
            return None
        return self._citation_from_block(block_ordinal, self.blocks.get(block_ordinal, {}))

    def get_block_text(self, block_id: str | int) -> str | None:
        block_ordinal = self._coerce_block_ordinal(block_id)
        block = self.blocks.get(block_ordinal)
        return str(block.get("text")) if block else None

    def memory_estimate_bytes(self) -> int:
        return (
            len(self.relations_by_center) * 96
            + self.relation_rows_loaded * 24
            + len(self.block_anchor_rows) * 18
            + len(self.blocks) * 512
            + len(self.symbol_to_anchor) * 80
        )

    def _block_anchor_sequences(self) -> dict[int, list[str]]:
        rows_by_block: dict[int, list[tuple[int, str]]] = defaultdict(list)
        for symbol, block_ordinal, position in self.block_anchor_rows:
            rows_by_block[block_ordinal].append((position, self.symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol))))
        return {block_ordinal: [anchor for _position, anchor in sorted(rows)] for block_ordinal, rows in rows_by_block.items()}

    def _coerce_symbol(self, anchor_id: str | bytes) -> bytes:
        if isinstance(anchor_id, bytes):
            return anchor_id
        value = str(anchor_id).strip()
        if value.startswith("0x") and len(value) == 14:
            return bytes.fromhex(value[2:])
        return self.anchor_to_symbol.get(value.lower(), symbol_bytes(value))

    def _coerce_block_ordinal(self, block_id: str | int) -> int:
        if isinstance(block_id, int):
            return block_id
        value = str(block_id)
        if value.isdigit():
            return int(value)
        if value in self.block_id_to_ordinal:
            return self.block_id_to_ordinal[value]
        if value in self.citation_to_ordinal:
            return self.citation_to_ordinal[value]
        raise KeyError(f"unknown block id: {block_id}")

    @staticmethod
    def _citation_from_block(block_ordinal: int, block: dict[str, Any] | None) -> dict[str, Any]:
        block = block or {}
        return {
            "block_ordinal": block_ordinal,
            "block_id": block.get("block_id"),
            "citation_id": block.get("citation_id"),
            "marker": block.get("marker"),
            "file_path": block.get("file_path"),
            "line_start": block.get("line_start"),
            "line_end": block.get("line_end"),
        }


def load_resident_dataset_tap(runtime_root: str | Path, dataset_id: str) -> ResidentDatasetTap:
    return ResidentDatasetTap(AwBackendTap(runtime_root, dataset_id))
