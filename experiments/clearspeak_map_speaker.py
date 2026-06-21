from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
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
    anchorize,
    dataset_paths,
    ensure_dataset,
    expand_query_anchors,
    iter_relation_records,
    read_block_anchor_rows,
    read_blocks,
    read_symbol_to_anchor,
    score_blocks,
    sha1_text,
    symbol_bytes,
    symbol_hex,
    unique_stamp,
    utc_now,
    write_json,
)

SCHEMA = "awrag_clearspeak_map_speaker_receipt@0"
BATCH_SCHEMA = "awrag_clearspeak_map_speaker_batch@0"
DEFAULT_CLOUD_K = 6
DEFAULT_WINDOW_RADIUS = 6


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _seed_anchors(text: str) -> list[str]:
    return _unique_ordered(expand_query_anchors(anchorize(text)))


def _compact_text(value: str, limit: int = 700) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."

def _normal_sentence(value: str) -> str:
    compact = _compact_text(value, 420).strip()
    if not compact:
        return ""
    compact = compact[0].upper() + compact[1:]
    if compact[-1] not in ".?!":
        compact += "."
    return compact


def _unique_citations(frames: list[dict[str, Any]], limit: int = 3) -> list[str]:
    citations: list[str] = []
    for frame in frames:
        citation = str(frame.get("citation") or "").strip()
        if citation and citation not in citations:
            citations.append(citation)
        if len(citations) >= limit:
            break
    return citations


def _normal_surface_answer(
    question: str,
    mirror_starter: str | None,
    passes: list[dict[str, Any]],
) -> dict[str, Any]:
    preferred_pass = "mirror_answer_starter" if mirror_starter else "question"
    selected = next(
        (row for row in passes if row.get("pass") == preferred_pass and row.get("candidate_frames")),
        None,
    )
    if selected is None:
        selected = next((row for row in passes if row.get("candidate_frames")), None)
    if selected is None:
        return {
            "schema": "awrag_map_speaker_surface_answer@0",
            "status": "not_enough_evidence",
            "question": question,
            "text": "I do not have enough cited AWRAG evidence to answer normally.",
            "citations": [],
            "evidence_pass": None,
            "frame_ids": [],
            "surface_source": "none",
        }

    frames = list(selected.get("candidate_frames", []))
    citations = _unique_citations(frames)
    if mirror_starter and selected.get("pass") == "mirror_answer_starter":
        answer = _normal_sentence(mirror_starter)
        status = "answered_from_supplied_answer_and_awrag_evidence"
        surface_source = "supplied_answer_supported_by_awrag"
    else:
        answer = _normal_sentence(str(frames[0].get("source_text") or frames[0].get("surface_text") or ""))
        status = "answered_from_awrag_evidence"
        surface_source = "awrag_top_evidence_text"

    cited_text = " ".join(citations)
    if cited_text:
        answer = f"{answer} {cited_text}"
    return {
        "schema": "awrag_map_speaker_surface_answer@0",
        "status": status,
        "question": question,
        "text": answer,
        "citations": citations,
        "evidence_pass": selected.get("pass"),
        "frame_ids": [str(frame.get("frame_id")) for frame in frames[: len(citations) or 1]],
        "surface_source": surface_source,
    }


def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_lock_row(path: Path, *, include_sha256: bool) -> dict[str, Any]:
    exists = path.exists()
    stat = path.stat() if exists else None
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": int(stat.st_size) if stat else 0,
        "modified_time_ns": int(stat.st_mtime_ns) if stat else None,
        "sha256": _sha256_file(path) if include_sha256 and exists else None,
    }


def _resident_artifact_lock(paths, *, include_sha256: bool = False) -> dict[str, Any]:
    files = {
        "dataset_manifest": paths.manifest_path,
        "dataset_lexicon": paths.lexicon_path,
        "blocks": paths.blocks_path,
        "citations": paths.citations / "citations.jsonl",
        "coordinates": paths.coordinates / "coordinate_index.jsonl",
        "anchor_counts": paths.anchor_counts_path,
        "relation_counts": paths.relation_counts_path,
        "block_anchor_postings": paths.block_anchor_path,
    }
    return {
        "schema": "awrag_resident_artifact_lock@1",
        "created_at": utc_now(),
        "mode": "read_only_dataset_artifact_lock",
        "mutation_allowed": False,
        "sha256_enabled": include_sha256,
        "files": {name: _file_lock_row(path, include_sha256=include_sha256) for name, path in files.items()},
    }


def _compare_artifact_locks(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    before_files = before.get("files", {})
    after_files = after.get("files", {})
    for name, before_row in before_files.items():
        after_row = after_files.get(name)
        if after_row is None:
            mismatches.append({"file": name, "reason": "missing_after"})
            continue
        for key in ("exists", "size_bytes", "modified_time_ns", "sha256"):
            if before_row.get(key) != after_row.get(key):
                mismatches.append({
                    "file": name,
                    "field": key,
                    "before": before_row.get(key),
                    "after": after_row.get(key),
                })
    return {
        "schema": "awrag_resident_system_lock_verification@1",
        "created_at": utc_now(),
        "status": "locked_unchanged" if not mismatches else "artifact_changed",
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def _relation_cloud(paths, seed_anchors: list[str], cloud_k: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    symbol_to_anchor = read_symbol_to_anchor(paths)
    seed_symbols = {symbol_bytes(anchor): anchor for anchor in seed_anchors}
    buckets: dict[str, dict[int, Counter[bytes]]] = {
        anchor: defaultdict(Counter) for anchor in seed_anchors
    }

    for center_symbol, neighbor_symbol, offset, observations in iter_relation_records(paths):
        if offset == 0 or center_symbol not in seed_symbols:
            continue
        center_anchor = seed_symbols[center_symbol]
        buckets[center_anchor][offset][neighbor_symbol] += observations

    cloud: dict[str, Any] = {}
    flat_neighbors: Counter[bytes] = Counter()
    for seed_anchor in seed_anchors:
        position_rows: dict[str, list[dict[str, Any]]] = {}
        for offset in range(-DEFAULT_WINDOW_RADIUS, DEFAULT_WINDOW_RADIUS + 1):
            if offset == 0:
                continue
            rows = []
            for neighbor_symbol, observations in buckets[seed_anchor][offset].most_common(cloud_k):
                neighbor_hex = symbol_hex(neighbor_symbol)
                rows.append(
                    {
                        "anchor": symbol_to_anchor.get(neighbor_hex, neighbor_hex),
                        "symbol": neighbor_hex,
                        "relative_position": offset,
                        "observations": observations,
                    }
                )
                flat_neighbors[neighbor_symbol] += observations
            position_rows[str(offset)] = rows
        cloud[seed_anchor] = position_rows

    relation_neighbors = [
        {
            "anchor": symbol_to_anchor.get(symbol_hex(neighbor_symbol), symbol_hex(neighbor_symbol)),
            "symbol": symbol_hex(neighbor_symbol),
            "score": observations,
        }
        for neighbor_symbol, observations in flat_neighbors.most_common(cloud_k * 12)
    ]
    return cloud, relation_neighbors


def _block_anchor_sequences(paths) -> dict[int, list[str]]:
    symbol_to_anchor = read_symbol_to_anchor(paths)
    rows_by_block: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for symbol, block_ordinal, position in read_block_anchor_rows(paths):
        rows_by_block[block_ordinal].append(
            (position, symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)))
        )
    return {
        block_ordinal: [anchor for _position, anchor in sorted(rows)]
        for block_ordinal, rows in rows_by_block.items()
    }


def _windows_for_block(
    sequence: list[str],
    focus_anchors: set[str],
    *,
    radius: int,
    max_windows: int = 4,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for position, anchor in enumerate(sequence):
        if anchor not in focus_anchors:
            continue
        start = max(0, position - radius)
        end = min(len(sequence), position + radius + 1)
        windows.append(
            {
                "position": position,
                "center": anchor,
                "before": sequence[start:position],
                "after": sequence[position + 1 : end],
            }
        )
        if len(windows) >= max_windows:
            break
    return windows


def _frame_from_candidate(
    candidate: dict[str, Any],
    sequence: list[str],
    focus_anchors: set[str],
    *,
    radius: int,
    pass_name: str,
) -> dict[str, Any]:
    location = candidate.get("location", {})
    text = candidate.get("text", "")
    citation = candidate.get("citation") or location.get("citation", "")
    frame_id = sha1_text(
        "|".join(
            [
                pass_name,
                str(candidate.get("block_ordinal", "")),
                citation,
                _compact_text(text, 220),
            ]
        )
    )[:16]
    return {
        "frame_id": f"AWFRAME-{frame_id}",
        "pass": pass_name,
        "block_ordinal": candidate.get("block_ordinal"),
        "citation": citation,
        "file_path": candidate.get("file_path") or location.get("file_path"),
        "source_path": location.get("source_path"),
        "start_line": candidate.get("line_start") or location.get("start_line"),
        "end_line": candidate.get("line_end") or location.get("end_line"),
        "score": candidate.get("score"),
        "density_score": candidate.get("density_score"),
        "direct_matched_anchors": candidate.get("direct_matched_anchors", []),
        "matched_anchors": candidate.get("matched_anchors", []),
        "anchor_windows": _windows_for_block(
            sequence,
            focus_anchors,
            radius=radius,
        ),
        "source_text": text,
        "surface_text": f"{citation}: {_compact_text(text)}" if citation else _compact_text(text),
    }


def _run_pass(
    paths,
    *,
    pass_name: str,
    seed_anchors: list[str],
    top_k: int,
    cloud_k: int,
    candidate_depth: int,
    window_radius: int,
) -> dict[str, Any]:
    blocks = read_blocks(paths)
    block_anchor_rows = read_block_anchor_rows(paths)
    block_sequences = _block_anchor_sequences(paths)
    cloud, relation_neighbors = _relation_cloud(paths, seed_anchors, cloud_k)
    candidates = score_blocks(
        paths,
        blocks,
        block_anchor_rows,
        Counter(seed_anchors),
        relation_neighbors,
        top_k=max(candidate_depth, top_k),
    )
    focus_anchors = set(seed_anchors)
    for row in relation_neighbors:
        focus_anchors.add(str(row.get("anchor", "")))

    citation_to_ordinal = {str(block.get("marker", "")): block_ordinal for block_ordinal, block in blocks.items()}
    frames: list[dict[str, Any]] = []
    seen_frames: set[str] = set()
    for candidate in candidates:
        block_ordinal = candidate.get("block_ordinal")
        if block_ordinal is None:
            block_ordinal = citation_to_ordinal.get(str(candidate.get("citation", "")))
        candidate = dict(candidate)
        candidate["block_ordinal"] = block_ordinal
        sequence = block_sequences.get(block_ordinal, [])
        frame = _frame_from_candidate(
            candidate,
            sequence,
            focus_anchors,
            radius=window_radius,
            pass_name=pass_name,
        )
        dedupe_key = "|".join(
            [
                str(frame.get("citation", "")),
                str(frame.get("block_ordinal", "")),
                _compact_text(str(frame.get("source_text", "")), 160),
            ]
        )
        if dedupe_key in seen_frames:
            continue
        seen_frames.add(dedupe_key)
        frames.append(frame)
        if len(frames) >= top_k:
            break

    return {
        "pass": pass_name,
        "seed_anchors": seed_anchors,
        "cloud_k_per_position": cloud_k,
        "candidate_depth": candidate_depth,
        "relation_cloud": cloud,
        "relation_neighbor_count": len(relation_neighbors),
        "candidate_frames": frames,
    }



def _block_anchor_sequences_from_rows(
    block_anchor_rows: list[tuple[bytes, int, int]],
    symbol_to_anchor: dict[str, str],
) -> dict[int, list[str]]:
    rows_by_block: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for symbol, block_ordinal, position in block_anchor_rows:
        rows_by_block[block_ordinal].append(
            (position, symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)))
        )
    return {
        block_ordinal: [anchor for _position, anchor in sorted(rows)]
        for block_ordinal, rows in rows_by_block.items()
    }


class LoadedMapSpeaker:
    """Read-only resident view of the native AWRAG evidence lattice."""

    def __init__(self, runtime_root: str | Path, dataset_id: str, *, hash_lock_artifacts: bool = False) -> None:
        ensure_dataset(runtime_root, dataset_id)
        self.runtime_root = str(runtime_root)
        self.dataset_id = dataset_id
        self.paths = dataset_paths(runtime_root, dataset_id)
        self.hash_lock_artifacts = hash_lock_artifacts
        load_started = perf_counter()
        self.artifact_lock_before = _resident_artifact_lock(
            self.paths,
            include_sha256=hash_lock_artifacts,
        )
        self.symbol_to_anchor = read_symbol_to_anchor(self.paths)
        self.blocks = read_blocks(self.paths)
        self.block_anchor_rows = read_block_anchor_rows(self.paths)
        self.block_sequences = _block_anchor_sequences_from_rows(
            self.block_anchor_rows,
            self.symbol_to_anchor,
        )
        self.citation_to_ordinal = {
            str(block.get("marker", "")): block_ordinal
            for block_ordinal, block in self.blocks.items()
        }
        self.relations_by_center: dict[bytes, list[tuple[bytes, int, int]]] = defaultdict(list)
        relation_rows_loaded = 0
        for center_symbol, neighbor_symbol, offset, observations in iter_relation_records(self.paths):
            if offset == 0:
                continue
            self.relations_by_center[center_symbol].append((neighbor_symbol, offset, observations))
            relation_rows_loaded += 1
        self.relation_rows_loaded = relation_rows_loaded
        self.load_elapsed_seconds = round(perf_counter() - load_started, 6)
        self.artifact_lock_after_load = _resident_artifact_lock(
            self.paths,
            include_sha256=hash_lock_artifacts,
        )
        self.load_lock_verification = _compare_artifact_locks(
            self.artifact_lock_before,
            self.artifact_lock_after_load,
        )

    def verify_lock(self) -> dict[str, Any]:
        current = _resident_artifact_lock(self.paths, include_sha256=self.hash_lock_artifacts)
        return _compare_artifact_locks(self.artifact_lock_before, current)

    def load_stats(self) -> dict[str, Any]:
        return {
            "strategy": "native_awbin_loaded_once_in_ram",
            "relation_rows_loaded": self.relation_rows_loaded,
            "relation_centers_loaded": len(self.relations_by_center),
            "block_anchor_postings_loaded": len(self.block_anchor_rows),
            "blocks_loaded": len(self.blocks),
            "symbols_loaded": len(self.symbol_to_anchor),
            "load_elapsed_seconds": self.load_elapsed_seconds,
            "count_backend": COUNT_BACKEND,
            "system_lock": self.load_lock_verification,
        }


def load_map_speaker(
    runtime_root: str | Path,
    dataset_id: str,
    *,
    hash_lock_artifacts: bool = False,
) -> LoadedMapSpeaker:
    return LoadedMapSpeaker(runtime_root, dataset_id, hash_lock_artifacts=hash_lock_artifacts)


def _relation_cloud_loaded(
    loaded: LoadedMapSpeaker,
    seed_anchors: list[str],
    cloud_k: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    seed_symbols = {symbol_bytes(anchor): anchor for anchor in seed_anchors}
    buckets: dict[str, dict[int, Counter[bytes]]] = {
        anchor: defaultdict(Counter) for anchor in seed_anchors
    }

    for center_symbol, center_anchor in seed_symbols.items():
        for neighbor_symbol, offset, observations in loaded.relations_by_center.get(center_symbol, []):
            buckets[center_anchor][offset][neighbor_symbol] += observations

    cloud: dict[str, Any] = {}
    flat_neighbors: Counter[bytes] = Counter()
    for seed_anchor in seed_anchors:
        position_rows: dict[str, list[dict[str, Any]]] = {}
        for offset in range(-DEFAULT_WINDOW_RADIUS, DEFAULT_WINDOW_RADIUS + 1):
            if offset == 0:
                continue
            rows = []
            for neighbor_symbol, observations in buckets[seed_anchor][offset].most_common(cloud_k):
                neighbor_hex = symbol_hex(neighbor_symbol)
                rows.append(
                    {
                        "anchor": loaded.symbol_to_anchor.get(neighbor_hex, neighbor_hex),
                        "symbol": neighbor_hex,
                        "relative_position": offset,
                        "observations": observations,
                    }
                )
                flat_neighbors[neighbor_symbol] += observations
            position_rows[str(offset)] = rows
        cloud[seed_anchor] = position_rows

    relation_neighbors = [
        {
            "anchor": loaded.symbol_to_anchor.get(symbol_hex(neighbor_symbol), symbol_hex(neighbor_symbol)),
            "symbol": symbol_hex(neighbor_symbol),
            "score": observations,
        }
        for neighbor_symbol, observations in flat_neighbors.most_common(cloud_k * 12)
    ]
    return cloud, relation_neighbors


def _run_loaded_pass(
    loaded: LoadedMapSpeaker,
    *,
    pass_name: str,
    seed_anchors: list[str],
    top_k: int,
    cloud_k: int,
    candidate_depth: int,
    window_radius: int,
) -> dict[str, Any]:
    cloud, relation_neighbors = _relation_cloud_loaded(loaded, seed_anchors, cloud_k)
    candidates = score_blocks(
        loaded.paths,
        loaded.blocks,
        loaded.block_anchor_rows,
        Counter(seed_anchors),
        relation_neighbors,
        top_k=max(candidate_depth, top_k),
    )
    focus_anchors = set(seed_anchors)
    for row in relation_neighbors:
        focus_anchors.add(str(row.get("anchor", "")))

    frames: list[dict[str, Any]] = []
    seen_frames: set[str] = set()
    for candidate in candidates:
        block_ordinal = candidate.get("block_ordinal")
        if block_ordinal is None:
            block_ordinal = loaded.citation_to_ordinal.get(str(candidate.get("citation", "")))
        candidate = dict(candidate)
        candidate["block_ordinal"] = block_ordinal
        sequence = loaded.block_sequences.get(block_ordinal, [])
        frame = _frame_from_candidate(
            candidate,
            sequence,
            focus_anchors,
            radius=window_radius,
            pass_name=pass_name,
        )
        dedupe_key = "|".join(
            [
                str(frame.get("citation", "")),
                str(frame.get("block_ordinal", "")),
                _compact_text(str(frame.get("source_text", "")), 160),
            ]
        )
        if dedupe_key in seen_frames:
            continue
        seen_frames.add(dedupe_key)
        frames.append(frame)
        if len(frames) >= top_k:
            break

    return {
        "pass": pass_name,
        "seed_anchors": seed_anchors,
        "cloud_k_per_position": cloud_k,
        "candidate_depth": candidate_depth,
        "relation_cloud": cloud,
        "relation_neighbor_count": len(relation_neighbors),
        "candidate_frames": frames,
    }


def speak_from_loaded_map(
    loaded: LoadedMapSpeaker,
    question: str,
    *,
    mirror_starter: str | None = None,
    top_k: int = 5,
    cloud_k: int = DEFAULT_CLOUD_K,
    candidate_depth: int = 25,
    window_radius: int = DEFAULT_WINDOW_RADIUS,
    write_receipt: bool = True,
) -> dict[str, Any]:
    question_anchors = _seed_anchors(question)
    passes = [
        _run_loaded_pass(
            loaded,
            pass_name="question",
            seed_anchors=question_anchors,
            top_k=top_k,
            cloud_k=cloud_k,
            candidate_depth=candidate_depth,
            window_radius=window_radius,
        )
    ]

    mirror_anchors: list[str] = []
    if mirror_starter:
        mirror_anchors = _unique_ordered(question_anchors + _seed_anchors(mirror_starter))
        passes.append(
            _run_loaded_pass(
                loaded,
                pass_name="mirror_answer_starter",
                seed_anchors=mirror_anchors,
                top_k=top_k,
                cloud_k=cloud_k,
                candidate_depth=candidate_depth,
                window_radius=window_radius,
            )
        )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "dataset_id": loaded.dataset_id,
        "scope": "dataset_local",
        "persistent_memory": False,
        "model_used": "none",
        "model_may_search": False,
        "count_backend": COUNT_BACKEND,
        "symbol_system": SYMBOL_SYSTEM,
        "symbol_bytes": SYMBOL_BYTES,
        "question": question,
        "question_anchors": question_anchors,
        "mirror_answer_starter": mirror_starter,
        "mirror_anchors": mirror_anchors,
        "top_k": top_k,
        "window_radius": window_radius,
        "loaded_lattice": loaded.load_stats(),
        "passes": passes,
        "normal_surface_answer": _normal_surface_answer(question, mirror_starter, passes),
        "mutation": {
            "writes_counts": False,
            "writes_lexicon": False,
            "writes_citations": False,
            "writes_coordinates": False,
            "writes_receipt_only": write_receipt,
        },
    }
    if write_receipt:
        receipt_name = f"clearspeak_map_speaker_{unique_stamp()}_{sha1_text(question)[:10]}.json"
        receipt_path = loaded.paths.outputs / receipt_name
        write_json(receipt_path, payload)
        payload["output_path"] = str(receipt_path)
    return payload

def speak_from_map(
    runtime_root: str | Path,
    dataset_id: str,
    question: str,
    *,
    mirror_starter: str | None = None,
    top_k: int = 5,
    cloud_k: int = DEFAULT_CLOUD_K,
    candidate_depth: int = 25,
    window_radius: int = DEFAULT_WINDOW_RADIUS,
    write_receipt: bool = True,
    hash_lock_artifacts: bool = False,
) -> dict[str, Any]:
    """Build deterministic evidence frames from a native count lattice loaded in RAM."""

    loaded = load_map_speaker(runtime_root, dataset_id, hash_lock_artifacts=hash_lock_artifacts)
    return speak_from_loaded_map(
        loaded,
        question,
        mirror_starter=mirror_starter,
        top_k=top_k,
        cloud_k=cloud_k,
        candidate_depth=candidate_depth,
        window_radius=window_radius,
        write_receipt=write_receipt,
    )

def _read_question_rows(path: Path) -> list[tuple[str, str | None]]:
    rows: list[tuple[str, str | None]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("{"):
            row = json.loads(line)
            rows.append((str(row["question"]), row.get("mirror_answer_starter")))
            continue
        if "\t" in line:
            question, mirror = line.split("\t", 1)
            rows.append((question.strip(), mirror.strip() or None))
        else:
            rows.append((line, None))
    return rows


def speak_question_file(
    runtime_root: str | Path,
    dataset_id: str,
    questions_path: str | Path,
    *,
    top_k: int = 5,
    cloud_k: int = DEFAULT_CLOUD_K,
    candidate_depth: int = 25,
    window_radius: int = DEFAULT_WINDOW_RADIUS,
    hash_lock_artifacts: bool = False,
) -> dict[str, Any]:
    loaded = load_map_speaker(runtime_root, dataset_id, hash_lock_artifacts=hash_lock_artifacts)
    question_rows = _read_question_rows(Path(questions_path))
    run_dir = loaded.paths.outputs / f"clearspeak_map_speaker_batch_{unique_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[str] = []
    for index, (question, mirror_starter) in enumerate(question_rows, start=1):
        result = speak_from_loaded_map(
            loaded,
            question,
            mirror_starter=mirror_starter,
            top_k=top_k,
            cloud_k=cloud_k,
            candidate_depth=candidate_depth,
            window_radius=window_radius,
            write_receipt=False,
        )
        output_path = run_dir / f"{index:04d}_{sha1_text(question)[:10]}.json"
        write_json(output_path, result)
        outputs.append(str(output_path))

    summary: dict[str, Any] = {
        "schema": BATCH_SCHEMA,
        "created_at": utc_now(),
        "dataset_id": dataset_id,
        "scope": "dataset_local",
        "persistent_memory": False,
        "model_used": "none",
        "count_backend": COUNT_BACKEND,
        "symbol_system": SYMBOL_SYSTEM,
        "question_count": len(question_rows),
        "completed": len(outputs),
        "failed": 0,
        "output_paths": outputs,
        "loaded_lattice": loaded.load_stats(),
        "resident_system_lock": loaded.verify_lock(),
    }
    summary_path = run_dir / "summary.json"
    write_json(summary_path, summary)
    summary["summary_path"] = str(summary_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Experimental AWRAG map speaker: native counts to deterministic evidence frames."
    )
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--question")
    parser.add_argument("--questions")
    parser.add_argument("--mirror-answer-starter")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--cloud-k", type=int, default=DEFAULT_CLOUD_K)
    parser.add_argument("--candidate-depth", type=int, default=25)
    parser.add_argument("--hash-lock-artifacts", action="store_true")
    args = parser.parse_args(argv)

    if bool(args.question) == bool(args.questions):
        parser.error("provide exactly one of --question or --questions")

    if args.question:
        result = speak_from_map(
            args.runtime_root,
            args.dataset_id,
            args.question,
            mirror_starter=args.mirror_answer_starter,
            top_k=args.top_k,
            cloud_k=args.cloud_k,
            candidate_depth=args.candidate_depth,
            hash_lock_artifacts=args.hash_lock_artifacts,
        )
    else:
        result = speak_question_file(
            args.runtime_root,
            args.dataset_id,
            args.questions,
            top_k=args.top_k,
            cloud_k=args.cloud_k,
            candidate_depth=args.candidate_depth,
            hash_lock_artifacts=args.hash_lock_artifacts,
        )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
