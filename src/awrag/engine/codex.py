from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .base import sha1_text, utc_now, with_protected_notice


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

