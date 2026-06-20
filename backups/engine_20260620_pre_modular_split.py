from __future__ import annotations

import hashlib
import json
import re
import struct
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
from typing import Any, Iterable

from .nlp_resolver import resolve_answer


COPYRIGHT = "Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved."
WATERMARK = "AWRAG public-review facsimile output; not source evidence. Verify against cited source coordinates."
LICENSE_REF = "AWRAG Public Review License"
FACSIMILE_WARNING = "This output is a local processing facsimile, not source evidence or professional advice."
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?|[^\sA-Za-z0-9]", re.UNICODE)
MAX_BLOCK_LINES = 40
SYMBOL_SYSTEM = "awrag_public_6b@1"
SYMBOL_BYTES = 6
SYMBOL_HEX_CHARS = SYMBOL_BYTES * 2
COUNT_BACKEND = "awrag_native_binary_counts@1"
FORENSIC_LADDER = [
    ("L1", "artifact_or_subject_referenced"),
    ("L2", "artifact_existence_evidenced"),
    ("L3", "artifact_contents_recovered"),
    ("L4", "artifact_modification_evidenced"),
    ("L5", "artifact_referenced_after_modification"),
    ("L6", "deletion_or_rejection_discussed"),
    ("L7", "deletion_or_rejection_evidenced"),
    ("L8", "contradictory_statements_found"),
    ("L9", "execution_or_deployment_evidenced"),
]
ANCHOR_RECORD = struct.Struct(">6sQ")
RELATION_RECORD = struct.Struct(">6s6shI")
BLOCK_ANCHOR_RECORD = struct.Struct(">6sIH")
STOP_ANCHORS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "do",
    "does", "doc", "docs", "document", "documents", "explain", "explained",
    "explains", "file", "files", "for", "from", "how", "in", "into", "is",
    "it", "of", "on", "or", "project", "say", "said", "says", "mention",
    "mentioned", "mentions", "that", "the", "this", "to", "what", "where",
    "which", "who", "why", "with",
}


@dataclass(frozen=True)
class DatasetPaths:
    root: Path
    incoming: Path
    state: Path
    counts: Path
    coordinates: Path
    citations: Path
    outputs: Path
    receipts: Path
    anchor_counts_path: Path
    relation_counts_path: Path
    block_anchor_path: Path
    blocks_path: Path
    lexicon_path: Path
    chat_metadata_path: Path
    manifest_path: Path


def safe_id(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip()).strip("._")
    if not out:
        raise ValueError("dataset id is required")
    return out


def dataset_paths(runtime_root: str | Path, dataset_id: str) -> DatasetPaths:
    root = Path(runtime_root).expanduser().resolve() / "datasets" / safe_id(dataset_id)
    return DatasetPaths(
        root=root,
        incoming=root / "incoming",
        state=root / "state",
        counts=root / "counts",
        coordinates=root / "coordinates",
        citations=root / "citations",
        outputs=root / "outputs",
        receipts=root / "receipts",
        anchor_counts_path=root / "counts" / "anchor_counts.awbin",
        relation_counts_path=root / "counts" / "relation_counts.awbin",
        block_anchor_path=root / "counts" / "block_anchor_postings.awbin",
        blocks_path=root / "state" / "blocks.jsonl",
        lexicon_path=root / "state" / "dataset_lexicon.json",
        chat_metadata_path=root / "state" / "chat_metadata_index.jsonl",
        manifest_path=root / "dataset_manifest.json",
    )


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


def query(
    runtime_root: str | Path,
    dataset_id: str,
    question: str,
    *,
    top_k: int = 5,
    created_after: str | None = None,
    created_before: str | None = None,
    speaker: str | None = None,
) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    q_anchors = expand_query_anchors(anchorize(question))
    if not q_anchors:
        raise ValueError("question produced no anchors")
    q_counter = Counter(q_anchors)

    blocks = read_blocks(paths)
    block_anchor_rows = read_block_anchor_rows(paths)
    metadata_filter = build_metadata_filter(created_after=created_after, created_before=created_before, speaker=speaker)
    if metadata_filter["active"]:
        blocks, block_anchor_rows = apply_block_metadata_filter(blocks, block_anchor_rows, metadata_filter)
    relation_neighbors = top_relation_neighbors(paths, q_counter, limit=16)
    raw_candidate_blocks = score_blocks(paths, blocks, block_anchor_rows, q_counter, relation_neighbors, top_k=max(top_k * 5, 25))
    qualified = qualify_evidence(question, Counter(anchorize(question)), raw_candidate_blocks, top_k=top_k)

    answer_packet = {
        "instruction": "Use cited local evidence coordinates only. This packet is a facsimile output, not source evidence.",
        "citations_owned_by": "AWRAG",
        "qualification": qualified["summary"],
        "qualification_receipts": qualified["receipts"],
        "locations": qualified["locations"],
        "rejected_locations": qualified["rejected"],
    }
    final_answer = resolve_answer(question, answer_packet)
    forensic_receipt = build_forensic_support_receipt(question, answer_packet, final_answer)

    output = {
        "schema": "awrag_query_result@1",
        "created_at": utc_now(),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "question": question,
        "question_anchors": list(q_counter),
        "relation_neighbors": relation_neighbors,
        "count_backend": COUNT_BACKEND,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
        "metadata_filter": metadata_filter,
        "answer_packet": answer_packet,
        "final_answer": final_answer,
        "forensic_support_receipt": forensic_receipt,
    }
    output_path = paths.outputs / f"query_{unique_stamp()}_{sha1_text(question)[:8]}.json"
    write_json(output_path, output)
    output["output_path"] = str(output_path)
    return with_protected_notice(output)


def build_forensic_support_receipt(
    question: str,
    answer_packet: dict[str, Any],
    final_answer: dict[str, Any],
) -> dict[str, Any]:
    """Build a conservative forensic reconstruction receipt from admitted evidence.

    The receipt never accuses. It names only what the AWRAG packet can support
    from admitted locations and explicitly lists common claims that remain
    unsupported.
    """
    locations = list(answer_packet.get("locations") or [])
    citations = [str(row.get("citation")) for row in locations if row.get("citation")]
    evidence_text = "\n".join(str(row.get("text") or "") for row in locations)
    evidence_terms = set(anchorize(evidence_text))
    question_terms = set(anchorize(question))
    text_folded = evidence_text.casefold()
    final_status = str(final_answer.get("status") or "")

    supported: list[str] = []
    ladder_hits: list[str] = []

    if locations:
        ladder_hits.append("L1")
        supported.append("artifact_or_subject_referenced")

    if locations and question_terms and len(question_terms & evidence_terms) >= min(2, len(question_terms)):
        ladder_hits.append("L2")
        supported.append("artifact_existence_evidenced")

    if _contains_any(text_folded, ("```", "def ", "class ", "function ", "import ", ".py", "module 1", "module_")):
        ladder_hits.append("L3")
        supported.append("artifact_contents_recovered")

    if _contains_any(text_folded, ("modified", "updated", "changed", "rewrote", "patched", "edited", "version")):
        ladder_hits.append("L4")
        supported.append("artifact_modification_evidenced")

    if "L4" in ladder_hits and _contains_any(text_folded, ("after", "later", "then", "again")):
        ladder_hits.append("L5")
        supported.append("artifact_referenced_after_modification")

    if _contains_any(text_folded, ("deleted", "delete", "threw it away", "thrown away", "ditched", "discarded", "rejected", "not as a build plan")):
        ladder_hits.append("L6")
        supported.append("deletion_or_rejection_discussed")

    if _contains_any(text_folded, ("deletion receipt", "delete log", "removed from disk", "file no longer exists", "not recovered")):
        ladder_hits.append("L7")
        supported.append("deletion_or_rejection_evidenced")

    if _contains_any(text_folded, ("contradiction", "contradictory", "conflict", "conflicting statement", "inconsistent")):
        ladder_hits.append("L8")
        supported.append("contradictory_statements_found")

    if _contains_any(text_folded, ("executed", "ran command", "ran script", "deployed", "launched", "installed", "in production", "production deployment")):
        ladder_hits.append("L9")
        supported.append("execution_or_deployment_evidenced")

    supported = _dedupe_preserve_order(supported)
    ladder_hits = _dedupe_preserve_order(ladder_hits)
    supported_set = set(supported)
    not_supported = [name for _, name in FORENSIC_LADDER if name not in supported_set]
    support_level = forensic_support_level(ladder_hits, final_status)

    return {
        "schema": "awrag_forensic_support_receipt@1",
        "mode": "reconstructive_not_accusatory",
        "support_level": support_level,
        "ladder": [{"level": level, "meaning": meaning} for level, meaning in FORENSIC_LADDER],
        "ladder_hits": ladder_hits,
        "supported": supported,
        "not_supported": not_supported,
        "citations": citations,
        "claim_language": "The record supports only the listed evidence states. Absence from supported means not established by admitted locations.",
        "conclusion": forensic_conclusion(support_level, supported, not_supported),
    }


def forensic_support_level(ladder_hits: list[str], final_status: str) -> str:
    if not ladder_hits or final_status == "not_enough_information":
        return "insufficient"
    if "L8" in ladder_hits:
        return "conflict"
    if "L9" in ladder_hits or "L3" in ladder_hits:
        return "strong"
    if len(ladder_hits) >= 2:
        return "partial"
    return "weak"


def forensic_conclusion(support_level: str, supported: list[str], not_supported: list[str]) -> str:
    if support_level == "insufficient":
        return "The admitted record does not provide enough evidence to support the requested forensic claim."
    supported_text = ", ".join(supported) if supported else "nothing"
    unsupported_text = ", ".join(not_supported[:4]) if not_supported else "no common unsupported states"
    return f"The record supports: {supported_text}. The record does not establish: {unsupported_text}."


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out



def batch_questions(
    runtime_root: str | Path,
    dataset_id: str,
    questions_path: str | Path,
    *,
    top_k: int = 5,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Run a plain question list through the existing single-question query path."""
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    source = Path(questions_path).expanduser().resolve()
    questions = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    run_id = unique_stamp()
    run_dir = paths.outputs / f"batch_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    completed = 0
    failures: list[dict[str, Any]] = []
    output_paths: list[str] = []
    question_results: list[dict[str, Any]] = []

    items = _progress_iter(enumerate(questions, start=1), total=len(questions), enabled=show_progress)
    for index, question in items:
        item_started = perf_counter()
        try:
            result = query(runtime_root, dataset_id, question, top_k=top_k)
            elapsed = perf_counter() - item_started
            completed += 1
            output_path = str(result["output_path"])
            output_paths.append(output_path)
            question_results.append({
                "index": index,
                "question": question,
                "status": "completed",
                "output_path": output_path,
                "query_time_seconds": elapsed,
                "model_used": result.get("model_used", "none"),
            })
        except Exception as exc:  # pragma: no cover - defensive batch receipt path
            elapsed = perf_counter() - item_started
            failure = {
                "index": index,
                "question": question,
                "status": "failed",
                "error": str(exc),
                "query_time_seconds": elapsed,
                "model_used": "none",
            }
            failures.append(failure)
            question_results.append(failure)

    total_elapsed = perf_counter() - started
    average = total_elapsed / len(questions) if questions else 0.0
    summary = with_protected_notice({
        "schema": "awrag_batch_run_summary@1",
        "run_id": run_id,
        "created_at": utc_now(),
        "dataset": safe_id(dataset_id),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "questions_path": str(source),
        "question_count": len(questions),
        "completed": completed,
        "failed": len(failures),
        "output_paths": output_paths,
        "question_results": question_results,
        "failures": failures,
        "avg_query_time": average,
        "avg_query_time_seconds": average,
        "total_time_seconds": total_elapsed,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
    })
    summary_path = run_dir / "batch_run_summary.json"
    write_json(summary_path, summary)
    summary["summary_path"] = str(summary_path)
    return summary


def stage_codex_sessions(
    sessions_root: str | Path,
    output_path: str | Path,
    *,
    session_index_path: str | Path | None = None,
    max_files: int | None = None,
) -> dict[str, Any]:
    """Convert Codex session JSONL files into AWRAG chat-turn markdown."""
    root = Path(sessions_root).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    index = read_codex_session_index(session_index_path)
    files = sorted(root.rglob("*.jsonl"), key=lambda item: str(item))
    if max_files is not None:
        files = files[:max(0, int(max_files))]
    output.parent.mkdir(parents=True, exist_ok=True)

    turn_count = 0
    session_count = 0
    speaker_counts: Counter[str] = Counter()
    earliest: str | None = None
    latest: str | None = None

    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for file_path in files:
            session_id = ""
            source = "codex"
            title = file_path.stem
            session_had_turns = False
            for raw_line in file_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not raw_line.strip():
                    continue
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if row.get("type") == "session_meta":
                    payload = row.get("payload") or {}
                    session_id = str(payload.get("id") or session_id or file_path.stem)
                    source = str(payload.get("source") or payload.get("originator") or source)
                    title = index.get(session_id, title)
                    continue
                speaker, text = codex_message_from_row(row)
                if not speaker or not text.strip():
                    continue
                turn_count += 1
                session_had_turns = True
                created_at = str(row.get("timestamp") or "")
                if created_at:
                    earliest = created_at if earliest is None else min(earliest, created_at)
                    latest = created_at if latest is None else max(latest, created_at)
                speaker_counts[speaker] += 1
                message_id = sha1_text(f"{file_path}:{turn_count}:{created_at}:{speaker}")[:16]
                handle.write(f"## CHAT_TURN_{turn_count}\n")
                handle.write(f"CHAT_SOURCE_EXPORT: codex_sessions\n")
                handle.write(f"CHAT_SOURCE_SCOPE: {source}\n")
                handle.write(f"CHAT_CONVERSATION_ID: {session_id or file_path.stem}\n")
                handle.write(f"CHAT_MESSAGE_ID: {message_id}\n")
                handle.write(f"CHAT_TITLE: {title}\n")
                handle.write(f"CHAT_CREATED_AT: {created_at}\n")
                handle.write(f"CHAT_SPEAKER: {speaker}\n")
                handle.write("CHAT_TRUTH_SCOPE: system_doctrine_not_world_truth\n")
                handle.write("CHAT_LIFETIME_ALLOWED: false\n")
                handle.write("CHAT_TEXT:\n")
                handle.write(text.strip() + "\n\n")
            if session_had_turns:
                session_count += 1

    return with_protected_notice({
        "schema": "awrag_codex_session_stage_receipt@1",
        "created_at": utc_now(),
        "sessions_root": str(root),
        "output_path": str(output),
        "source_file_count": len(files),
        "session_count": session_count,
        "turn_count": turn_count,
        "speaker_counts": dict(sorted(speaker_counts.items())),
        "earliest_timestamp": earliest,
        "latest_timestamp": latest,
        "scope": "staged_dataset_source",
        "lifetime_allowed": False,
    })


def read_codex_session_index(session_index_path: str | Path | None) -> dict[str, str]:
    if not session_index_path:
        return {}
    path = Path(session_index_path).expanduser()
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = str(row.get("id") or "")
        title = str(row.get("thread_name") or "")
        if session_id and title:
            out[session_id] = title
    return out


def codex_message_from_row(row: dict[str, Any]) -> tuple[str | None, str]:
    payload = row.get("payload") or {}
    if row.get("type") != "response_item" or payload.get("type") != "message":
        return None, ""
    role = str(payload.get("role") or "").casefold()
    if role not in {"user", "assistant"}:
        return None, ""
    parts = payload.get("content") or []
    texts: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        value = part.get("text")
        if value is None:
            value = part.get("value")
        if value is not None:
            texts.append(str(value))
    return role, "\n".join(texts).strip()


def build_citation_crosslinks(
    runtime_root: str | Path,
    left_dataset_id: str,
    right_dataset_id: str,
    question: str,
    *,
    top_k: int = 8,
    min_shared: int = 3,
) -> dict[str, Any]:
    """Build a cross-dataset citation sidecar from normal AWRAG query packets."""
    left = query(runtime_root, left_dataset_id, question, top_k=top_k)
    right = query(runtime_root, right_dataset_id, question, top_k=top_k)
    left_rows = crosslink_candidate_rows(left)
    right_rows = crosslink_candidate_rows(right)
    links: list[dict[str, Any]] = []

    for left_row in left_rows:
        left_anchors = crosslink_anchor_set(str(left_row.get("text") or ""))
        for right_row in right_rows:
            right_anchors = crosslink_anchor_set(str(right_row.get("text") or ""))
            shared = sorted(left_anchors & right_anchors)
            if len(shared) < min_shared:
                continue
            links.append({
                "schema": "awrag_citation_crosslink@1",
                "from_dataset": safe_id(left_dataset_id),
                "from_citation": left_row.get("citation"),
                "from_line_start": left_row.get("line_start"),
                "from_line_end": left_row.get("line_end"),
                "to_dataset": safe_id(right_dataset_id),
                "to_citation": right_row.get("citation"),
                "to_line_start": right_row.get("line_start"),
                "to_line_end": right_row.get("line_end"),
                "link_type": classify_crosslink(shared),
                "shared_anchors": shared[:30],
                "shared_anchor_count": len(shared),
                "confidence": crosslink_confidence(len(shared)),
                "created_from": "awrag_dataset_local_query_packets",
                "lifetime_allowed": False,
            })

    links.sort(key=lambda item: (-int(item["shared_anchor_count"]), str(item["from_citation"]), str(item["to_citation"])))
    run_id = f"{safe_id(left_dataset_id)}__{safe_id(right_dataset_id)}"
    out_dir = Path(runtime_root).expanduser().resolve() / "datasets" / "_crosslinks" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "citation_crosslinks.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for link in links:
            handle.write(json.dumps(with_protected_notice(link), ensure_ascii=True) + "\n")

    summary = with_protected_notice({
        "schema": "awrag_citation_crosslink_summary@1",
        "created_at": utc_now(),
        "left_dataset_id": safe_id(left_dataset_id),
        "right_dataset_id": safe_id(right_dataset_id),
        "question": question,
        "top_k": top_k,
        "min_shared": min_shared,
        "left_candidate_count": len(left_rows),
        "right_candidate_count": len(right_rows),
        "crosslink_count": len(links),
        "crosslink_path": str(path),
        "top_crosslinks": links[:10],
        "left_output_path": left.get("output_path"),
        "right_output_path": right.get("output_path"),
        "lifetime_allowed": False,
    })
    write_json(out_dir / "citation_crosslink_summary.json", summary)
    return summary


def crosslink_candidate_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    packet = result.get("answer_packet") or {}
    rows = list(packet.get("locations") or [])
    rows.extend(packet.get("rejected_locations") or [])
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        citation = str(row.get("citation") or "")
        if citation and citation not in deduped:
            deduped[citation] = row
    return list(deduped.values())


def classify_crosslink(shared: list[str]) -> str:
    shared_set = set(shared)
    if {"citation", "linking"} & shared_set and {"graph", "network", "cross"} & shared_set:
        return "same_requirement"
    if {"file", "path", "commit"} & shared_set:
        return "implementation_followup"
    if {"contradiction", "conflict", "conflicting"} & shared_set:
        return "contradiction"
    return "same_evidence_field"


def crosslink_confidence(shared_count: int) -> str:
    if shared_count >= 8:
        return "strong"
    if shared_count >= 5:
        return "partial"
    return "weak"


def crosslink_anchor_set(text: str) -> set[str]:
    cleaned = evidence_text_only(text)
    blocked = STOP_ANCHORS | {
        "chat", "created", "conversation", "doctrine", "export", "false", "id",
        "message", "scope", "source", "speaker", "text", "truth", "turn",
        "user", "assistant", "model", "system", "because", "would", "could",
        "should", "there", "these", "those", "this", "that", "with", "from",
    }
    out: set[str] = set()
    for anchor in anchorize(cleaned):
        if anchor in blocked:
            continue
        if len(anchor) < 3:
            continue
        if anchor.isdigit():
            continue
        out.add(anchor)
    return out


def evidence_text_only(text: str) -> str:
    lines: list[str] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## CHAT_TURN_"):
            continue
        if re.match(r"^CHAT_[A-Z0-9_]+:", stripped):
            continue
        lines.append(line)
    return "\n".join(lines)


def _progress_iter(iterable: Iterable[Any], *, total: int, enabled: bool) -> Iterable[Any]:
    if not enabled:
        return iterable
    try:
        from tqdm import tqdm
    except Exception:  # pragma: no cover - fallback only when tqdm is unavailable
        return iterable
    return tqdm(iterable, total=total, desc="AWRAG batch", unit="question")
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


def parse_chat_metadata_block(text: str) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    wanted = {
        "CHAT_CONVERSATION_ID": "conversation_id",
        "CHAT_MESSAGE_ID": "message_id",
        "CHAT_TITLE": "title",
        "CHAT_CREATED_AT": "created_at_original",
        "CHAT_SPEAKER": "speaker",
        "CHAT_TRUTH_SCOPE": "truth_scope",
        "CHAT_LIFETIME_ALLOWED": "lifetime_allowed",
    }
    turn_match = re.search(r"^##\s+CHAT_TURN_([0-9]+)\s*$", text, flags=re.MULTILINE)
    if turn_match:
        metadata["turn_index"] = turn_match.group(1)
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        target = wanted.get(key)
        if target:
            metadata[target] = value.strip()
    if not metadata.get("conversation_id") and not metadata.get("message_id") and "turn_index" not in metadata:
        return {}
    created = metadata.get("created_at_original", "")
    parsed = parse_chat_datetime(created)
    if parsed:
        metadata["created_at"] = parsed.isoformat()
        metadata["date"] = parsed.date().isoformat()
        metadata["time"] = parsed.time().isoformat(timespec="seconds")
    speaker = metadata.get("speaker")
    if speaker:
        metadata["speaker"] = speaker.casefold()
    if "lifetime_allowed" in metadata:
        metadata["lifetime_allowed"] = metadata["lifetime_allowed"].casefold() == "true"
    if "turn_index" in metadata:
        metadata["turn_index"] = int(metadata["turn_index"])
    return metadata


def parse_chat_datetime(value: str) -> datetime | None:
    value = str(value or "").strip()
    if not value:
        return None
    formats = [
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_filter_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parse_chat_datetime(value)
    if parsed:
        return parsed
    raise ValueError(f"invalid chat metadata date filter: {value!r}")


def build_metadata_filter(
    *,
    created_after: str | None,
    created_before: str | None,
    speaker: str | None,
) -> dict[str, Any]:
    after = parse_filter_date(created_after)
    before = parse_filter_date(created_before)
    normalized_speaker = speaker.casefold().strip() if speaker else None
    return {
        "schema": "awrag_query_metadata_filter@1",
        "active": bool(after or before or normalized_speaker),
        "created_after": after.isoformat() if after else None,
        "created_before": before.isoformat() if before else None,
        "speaker": normalized_speaker,
    }


def apply_block_metadata_filter(
    blocks: dict[int, dict[str, Any]],
    block_anchor_rows: list[tuple[bytes, int, int]],
    metadata_filter: dict[str, Any],
) -> tuple[dict[int, dict[str, Any]], list[tuple[bytes, int, int]]]:
    allowed: set[int] = set()
    after = parse_filter_date(metadata_filter.get("created_after"))
    before = parse_filter_date(metadata_filter.get("created_before"))
    speaker = metadata_filter.get("speaker")
    for ordinal, block in blocks.items():
        metadata = block.get("chat_metadata") or {}
        if not metadata:
            continue
        if speaker and str(metadata.get("speaker", "")).casefold() != speaker:
            continue
        created = parse_chat_datetime(str(metadata.get("created_at") or metadata.get("created_at_original") or ""))
        if after and (not created or created < after):
            continue
        if before and (not created or created > before):
            continue
        allowed.add(ordinal)
    filtered_blocks = {ordinal: block for ordinal, block in blocks.items() if ordinal in allowed}
    filtered_rows = [row for row in block_anchor_rows if row[1] in allowed]
    return filtered_blocks, filtered_rows


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


def anchorize(text: str) -> list[str]:
    anchors: list[str] = []
    for match in WORD_RE.finditer(text):
        value = match.group(0).strip().casefold()
        if not value:
            continue
        if not any(ch.isalnum() for ch in value):
            continue
        if value in STOP_ANCHORS:
            continue
        if value.isalnum() and any(ch.isalpha() for ch in value) and any(ch.isdigit() for ch in value):
            anchors.extend(ch for ch in value if ch.isalnum())
        else:
            anchors.append(normalize_anchor(value))
    return anchors


def normalize_anchor(anchor: str) -> str:
    value = str(anchor or "").casefold().strip()
    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"
    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def expand_query_anchors(anchors: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        variants = [anchor, normalize_anchor(anchor)]
        if anchor.isalpha() and len(anchor) > 2:
            variants.append(anchor + "s")
        for variant in variants:
            if variant and variant not in STOP_ANCHORS and variant not in seen:
                out.append(variant)
                seen.add(variant)
    return out


def symbol_for(anchor: str) -> str:
    return "0x" + sha1_text(anchor)[:SYMBOL_HEX_CHARS].upper()


def symbol_bytes(anchor: str) -> bytes:
    return bytes.fromhex(symbol_for(anchor)[2:])


def symbol_hex(raw: bytes) -> str:
    return "0x" + raw.hex().upper()


def assert_no_symbol_collisions(anchors: Counter[str]) -> None:
    seen: dict[str, str] = {}
    for anchor in sorted(anchors):
        symbol = symbol_for(anchor)
        existing = seen.get(symbol)
        if existing is not None and existing != anchor:
            raise ValueError(
                "symbol collision in dataset-local public namespace: "
                f"{existing!r} and {anchor!r} both map to {symbol}"
            )
        seen[symbol] = anchor


def top_relation_neighbors(paths: DatasetPaths, q_counter: Counter[str], *, limit: int) -> list[dict[str, Any]]:
    scores: Counter[bytes] = Counter()
    blocked_symbols = {symbol_bytes(anchor) for anchor in q_counter} | {symbol_bytes(anchor) for anchor in STOP_ANCHORS}
    query_symbols = {symbol_bytes(anchor): weight for anchor, weight in q_counter.items()}
    symbol_to_anchor = read_symbol_to_anchor(paths)
    for anchor_symbol, neighbor_symbol, _offset, observations in iter_relation_records(paths):
        weight = query_symbols.get(anchor_symbol)
        if not weight or neighbor_symbol in blocked_symbols:
            continue
        scores[neighbor_symbol] += observations * weight
    return [
        {"anchor": symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)), "symbol": symbol_hex(symbol), "score": score}
        for symbol, score in scores.most_common(limit)
    ]


def score_blocks(
    paths: DatasetPaths,
    blocks: dict[int, dict[str, Any]],
    block_anchor_rows: list[tuple[bytes, int, int]],
    q_counter: Counter[str],
    relation_neighbors: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    weights: Counter[bytes] = Counter()
    direct_symbols = {symbol_bytes(anchor) for anchor in q_counter}
    symbol_to_anchor = read_symbol_to_anchor(paths)
    for anchor, count in q_counter.items():
        weights[symbol_bytes(anchor)] += 80 * count
    for index, row in enumerate(relation_neighbors):
        weights[bytes.fromhex(str(row["symbol"])[2:])] += max(1, 4 - index // 4)

    posting_counts: Counter[bytes] = Counter(symbol for symbol, _block, _pos in block_anchor_rows)
    block_lengths: Counter[int] = Counter(block for _symbol, block, _pos in block_anchor_rows)
    block_scores: Counter[int] = Counter()
    hits: dict[int, set[bytes]] = {}
    direct_hits: Counter[int] = Counter()
    seen_postings: set[tuple[bytes, int]] = set()

    for symbol, block_ordinal, _position in block_anchor_rows:
        weight = weights.get(symbol)
        if not weight:
            continue
        posting_key = (symbol, block_ordinal)
        if posting_key in seen_postings:
            continue
        seen_postings.add(posting_key)
        document_frequency = posting_counts[symbol]
        adjusted_weight = weight / max(1.0, document_frequency ** 0.5)
        block_scores[block_ordinal] += adjusted_weight
        hits.setdefault(block_ordinal, set()).add(symbol)
        if symbol in direct_symbols:
            direct_hits[block_ordinal] += 1

    ranked_rows: list[tuple[int, float, float, int]] = []
    for block_ordinal, score in block_scores.items():
        anchor_count = block_lengths.get(block_ordinal, 1)
        density = float(score) / max(1.0, anchor_count ** 0.5)
        ranked_rows.append((block_ordinal, float(score), density, anchor_count))
    ranked = sorted(ranked_rows, key=lambda item: (-direct_hits[item[0]], -item[2], -item[1], item[0]))

    out: list[dict[str, Any]] = []
    for block_ordinal, score, density, anchor_count in ranked[:top_k]:
        block = blocks.get(block_ordinal)
        if not block:
            continue
        matched_symbols = hits.get(block_ordinal, set())
        out.append({
            "citation": str(block["marker"]),
            "file_path": str(block["file_path"]),
            "line_start": int(block["line_start"]),
            "line_end": int(block["line_end"]),
            "score": round(float(score), 4),
            "density_score": round(float(density), 4),
            "block_anchor_count": anchor_count,
            "direct_hit_count": int(direct_hits[block_ordinal]),
            "direct_matched_anchors": sorted(symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)) for symbol in matched_symbols & direct_symbols),
            "matched_anchors": sorted(symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)) for symbol in matched_symbols),
            "text": str(block["text"]),
        })
    return out


def qualify_evidence(question: str, q_counter: Counter[str], candidates: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    question_terms = [anchor for anchor in q_counter if anchor not in STOP_ANCHORS]
    required_terms = significant_question_terms(question_terms)
    path_intent = has_path_or_config_intent(question)
    unsupported_intent = len(required_terms) >= 4

    receipts: list[dict[str, Any]] = []
    qualified_rows: list[tuple[float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        receipt = qualify_candidate(candidate, required_terms, path_intent, unsupported_intent)
        receipts.append(receipt)
        enriched = dict(candidate)
        enriched["qualification"] = receipt
        if receipt["qualified"]:
            qualified_rows.append((float(receipt["qualified_score"]), enriched))
        else:
            rejected.append(enriched)

    qualified_rows.sort(key=lambda item: (-item[0], -float(item[1].get("density_score", 0)), -float(item[1].get("score", 0))))
    locations = [item[1] for item in qualified_rows[:top_k]]
    support_state = "qualified_evidence" if locations else "no_qualified_evidence"
    return {
        "summary": {
            "schema": "awrag_evidence_qualification_summary@1",
            "support_state": support_state,
            "raw_candidate_count": len(candidates),
            "qualified_count": len(qualified_rows),
            "rejected_count": len(rejected),
            "required_terms": required_terms,
            "path_or_config_intent": path_intent,
        },
        "receipts": receipts,
        "locations": locations,
        "rejected": rejected[:top_k],
    }


def qualify_candidate(candidate: dict[str, Any], required_terms: list[str], path_intent: bool, unsupported_intent: bool) -> dict[str, Any]:
    text = str(candidate.get("text", ""))
    text_anchors = set(anchorize(text))
    direct = set(candidate.get("direct_matched_anchors") or [])
    covered = sorted(anchor for anchor in required_terms if anchor in text_anchors or anchor in direct)
    missing = sorted(anchor for anchor in required_terms if anchor not in covered)
    coverage = len(covered) / max(1, len(required_terms))
    heading_only = is_heading_only(text)
    broad_heading = heading_only and is_broad_heading(text)
    slash_phrase = contains_unqualified_slash_phrase(text)

    reject_reasons: list[str] = []
    if broad_heading:
        reject_reasons.append("section_heading_ambiguity")
    if heading_only and coverage < 0.75:
        reject_reasons.append("heading_without_content")
    if path_intent and slash_phrase and not contains_true_path_or_endpoint(text):
        reject_reasons.append("path_config_classifier_miss")
    if unsupported_intent and coverage < 0.50:
        reject_reasons.append("unsupported_refusal_threshold")
    if len(required_terms) >= 3 and coverage < 0.34:
        reject_reasons.append("predicate_object_coverage_miss")

    qualified = not reject_reasons
    score = float(candidate.get("density_score", 0)) + 8.0 * coverage + min(4.0, float(candidate.get("direct_hit_count", 0))) - (3.0 if heading_only else 0.0)
    return {
        "schema": "awrag_candidate_qualification@1",
        "candidate": candidate.get("citation"),
        "qualified": qualified,
        "reject_reasons": reject_reasons,
        "covered_terms": covered,
        "missing_terms": missing[:20],
        "coverage": round(coverage, 4),
        "heading_only": heading_only,
        "broad_heading": broad_heading,
        "path_or_config_candidate": contains_true_path_or_endpoint(text),
        "qualified_score": round(score, 4),
    }


def significant_question_terms(anchors: list[str]) -> list[str]:
    low_value = STOP_ANCHORS | {
        "answer", "ask", "asked", "claim", "data", "dataset", "describe", "described",
        "evidence", "find", "found", "give", "local", "provide", "question", "row",
        "section", "show", "staged", "under", "value",
    }
    out: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        if anchor in low_value:
            continue
        if len(anchor) == 1 and not anchor.isdigit():
            continue
        if anchor not in seen:
            out.append(anchor)
            seen.add(anchor)
    return out


def is_heading_only(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    return len(lines) == 1 and (lines[0].startswith("#") or len(lines[0]) <= 80)


def is_broad_heading(text: str) -> bool:
    stripped = text.strip().strip("#*` ").casefold()
    broad = {
        "conclusion", "discussion", "implemented", "next steps", "governance",
        "overview", "summary", "background", "results", "methods", "user upload",
        "what it opens", "citation integration", "citations pane",
    }
    return stripped in broad or stripped.startswith(("implemented", "next steps"))


def has_path_or_config_intent(question: str) -> bool:
    q = question.casefold()
    return any(token in q for token in ("path", "config", "endpoint", "api", "route", "url", "file"))


def contains_unqualified_slash_phrase(text: str) -> bool:
    return bool(re.search(r"\b[a-zA-Z]{2,}/[a-zA-Z]{2,}\b", text))


def contains_true_path_or_endpoint(text: str) -> bool:
    patterns = [
        r"[A-Za-z]:\\",
        r"[/\\][A-Za-z0-9_.-]+[/\\]",
        r"\bapi/[A-Za-z0-9_./{}-]+",
        r"/api/[A-Za-z0-9_./{}-]+",
        r"\b[A-Za-z0-9_.-]+\.(json|toml|yaml|yml|py|md|txt|csv)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


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


def public_paths(paths: DatasetPaths) -> dict[str, str]:
    return {
        "dataset_root": str(paths.root),
        "anchor_counts": str(paths.anchor_counts_path),
        "relation_counts": str(paths.relation_counts_path),
        "block_anchor_postings": str(paths.block_anchor_path),
        "lexicon": str(paths.lexicon_path),
        "coordinates": str(paths.coordinates),
        "citations": str(paths.citations),
        "outputs": str(paths.outputs),
        "receipts": str(paths.receipts),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(with_protected_notice(payload), ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def protected_notice() -> dict[str, Any]:
    return {
        "copyright": COPYRIGHT,
        "owner": "Cortex Evolved Systems",
        "license": LICENSE_REF,
        "watermark": WATERMARK,
        "facsimile_warning": FACSIMILE_WARNING,
        "watermark_locked": True,
        "removal_prohibited": True,
    }


def with_protected_notice(payload: dict[str, Any]) -> dict[str, Any]:
    protected = protected_notice()
    protected.update(payload)
    for key, value in protected_notice().items():
        protected[key] = value
    return protected


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="replace")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
