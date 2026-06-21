from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import (  # noqa: E402
    ANCHOR_RECORD,
    BLOCK_ANCHOR_RECORD,
    COUNT_BACKEND,
    RELATION_RECORD,
    SYMBOL_BYTES,
    SYMBOL_SYSTEM,
    dataset_paths,
    jsonl_count,
    protected_notice,
    read_blocks,
    read_symbol_to_anchor,
    record_count,
    safe_id,
    utc_now,
)

SCHEMA = "awrag_backend_tap@0"


@dataclass(frozen=True)
class TapFile:
    name: str
    path: str
    exists: bool
    size_bytes: int
    modified_time_ns: int | None
    record_count: int | None = None
    jsonl_rows: int | None = None
    sha256: str | None = None


class AwBackendTap:
    """Read-only adapter over an existing AWRAG dataset.

    This resolves paths and reads existing artifacts. It does not call helpers
    that create/touch dataset files.
    """

    def __init__(self, runtime_root: str | Path, dataset_id: str) -> None:
        self.runtime_root = str(Path(runtime_root).expanduser().resolve())
        self.dataset_id = safe_id(dataset_id)
        self.paths = dataset_paths(self.runtime_root, self.dataset_id)

    def file_rows(self, *, include_sha256: bool = False) -> list[TapFile]:
        return [
            self._file_row("dataset_manifest", self.paths.manifest_path, include_sha256=include_sha256),
            self._file_row("dataset_lexicon", self.paths.lexicon_path, include_sha256=include_sha256),
            self._file_row("blocks", self.paths.blocks_path, jsonl=True, include_sha256=include_sha256),
            self._file_row("chat_metadata", self.paths.chat_metadata_path, jsonl=True, include_sha256=include_sha256),
            self._file_row("citations", self.paths.citations / "citations.jsonl", jsonl=True, include_sha256=include_sha256),
            self._file_row("coordinates", self.paths.coordinates / "coordinate_index.jsonl", jsonl=True, include_sha256=include_sha256),
            self._file_row("anchor_counts", self.paths.anchor_counts_path, record_size=ANCHOR_RECORD.size, include_sha256=include_sha256),
            self._file_row("relation_counts", self.paths.relation_counts_path, record_size=RELATION_RECORD.size, include_sha256=include_sha256),
            self._file_row("block_anchor_postings", self.paths.block_anchor_path, record_size=BLOCK_ANCHOR_RECORD.size, include_sha256=include_sha256),
        ]

    def status(self, *, include_sha256: bool = False) -> dict[str, Any]:
        files = self.file_rows(include_sha256=include_sha256)
        by_name = {row.name: row for row in files}
        return {
            "schema": SCHEMA,
            "created_at": utc_now(),
            "mode": "read_only_backend_tap",
            "mutation_allowed": False,
            "runtime_root": self.runtime_root,
            "dataset_id": self.dataset_id,
            "dataset_root": str(self.paths.root),
            "count_backend": COUNT_BACKEND,
            "symbol_system": SYMBOL_SYSTEM,
            "symbol_bytes": SYMBOL_BYTES,
            "persistent_memory": False,
            "required_files_present": self.required_files_present(),
            "anchor_count": by_name["anchor_counts"].record_count or 0,
            "relation_count": by_name["relation_counts"].record_count or 0,
            "block_anchor_posting_count": by_name["block_anchor_postings"].record_count or 0,
            "block_count": by_name["blocks"].jsonl_rows or 0,
            "citation_count": by_name["citations"].jsonl_rows or 0,
            "chat_metadata_row_count": by_name["chat_metadata"].jsonl_rows or 0,
            "files": [row.__dict__ for row in files],
            "protected_notice": protected_notice(),
        }

    def required_files_present(self) -> bool:
        required = [self.paths.lexicon_path, self.paths.blocks_path, self.paths.anchor_counts_path, self.paths.relation_counts_path, self.paths.block_anchor_path]
        return all(path.exists() for path in required)

    def require_ready(self) -> None:
        required = {"dataset_lexicon", "blocks", "anchor_counts", "relation_counts", "block_anchor_postings"}
        missing = [row.name for row in self.file_rows() if row.name in required and not row.exists]
        if missing:
            raise FileNotFoundError("AWRAG dataset is missing required files: " + ", ".join(missing))

    def read_manifest(self) -> dict[str, Any]:
        if not self.paths.manifest_path.exists():
            return {}
        return json.loads(self.paths.manifest_path.read_text(encoding="utf-8"))

    def read_blocks(self) -> dict[int, dict[str, Any]]:
        return read_blocks(self.paths)

    def read_symbol_to_anchor(self) -> dict[str, str]:
        return read_symbol_to_anchor(self.paths)

    def iter_chat_metadata(self, *, limit: int | None = None) -> Iterable[dict[str, Any]]:
        if not self.paths.chat_metadata_path.exists():
            return
        count = 0
        with self.paths.chat_metadata_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                yield json.loads(line)
                count += 1
                if limit is not None and count >= limit:
                    break

    def write_tap_receipt(self, output_dir: str | Path, *, include_sha256: bool = False) -> Path:
        target = Path(output_dir) / "aw_backend_tap_receipt.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.status(include_sha256=include_sha256), ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return target

    def _file_row(self, name: str, path: Path, *, record_size: int | None = None, jsonl: bool = False, include_sha256: bool = False) -> TapFile:
        exists = path.exists()
        stat = path.stat() if exists else None
        return TapFile(
            name=name,
            path=str(path),
            exists=exists,
            size_bytes=int(stat.st_size) if stat else 0,
            modified_time_ns=int(stat.st_mtime_ns) if stat else None,
            record_count=record_count(path, record_size) if exists and record_size else None,
            jsonl_rows=jsonl_count(path) if exists and jsonl else None,
            sha256=_sha256_file(path) if include_sha256 and exists else None,
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
