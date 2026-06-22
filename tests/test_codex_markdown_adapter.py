from __future__ import annotations

from pathlib import Path

from awrag.engine import intake, stage_codex_markdown_export


def test_stage_codex_markdown_export_writes_chat_turns(tmp_path: Path) -> None:
    source = tmp_path / "codex_export.md"
    staged = tmp_path / "staged" / "codex_chat.awrag.md"
    source.write_text(
        "# Codex VS Code Main Chat Export\n\n"
        "## Source Metadata\n\n"
        "- Session id: `session-a`\n"
        "- Originator: `codex_vscode`\n\n"
        "## Transcript\n\n"
        "### 1. User\n\n"
        "Timestamp: `2026-06-22T10:00:00Z`\n\n"
        "What voltage settings did I end on?\n\n"
        "---\n\n"
        "### 2. Assistant\n\n"
        "Timestamp: `2026-06-22T10:00:10Z`\n\n"
        "The cited chat block says the final voltage mode stayed manual.\n",
        encoding="utf-8",
    )

    receipt = stage_codex_markdown_export(source, staged)

    assert receipt["schema"] == "awrag_codex_markdown_stage_receipt@1"
    assert receipt["turn_count"] == 2
    assert receipt["speaker_counts"] == {"assistant": 1, "user": 1}
    body = staged.read_text(encoding="utf-8")
    assert "## CHAT_TURN_1" in body
    assert "CHAT_SOURCE_EXPORT: codex_markdown_export" in body
    assert "CHAT_CONVERSATION_ID: session-a" in body
    assert "CHAT_SPEAKER: user" in body
    assert "CHAT_SPEAKER: assistant" in body
    assert "CHAT_LIFETIME_ALLOWED: false" in body


def test_staged_codex_markdown_can_be_ingested_as_chat_dataset(tmp_path: Path) -> None:
    source = tmp_path / "codex_export.md"
    staged = tmp_path / "codex_chat.awrag.md"
    runtime = tmp_path / "runtime"
    source.write_text(
        "# Codex VS Code Main Chat Export\n\n"
        "## Source Metadata\n\n"
        "- Session id: `session-b`\n"
        "- Originator: `codex_vscode`\n\n"
        "## Transcript\n\n"
        "### 1. User\n\n"
        "Timestamp: `2026-06-22T10:00:00Z`\n\n"
        "AnchorWorks citations stay dataset local.\n",
        encoding="utf-8",
    )

    stage_codex_markdown_export(source, staged)
    result = intake(runtime, "codex_chat_unit", staged)

    assert result["dataset_id"] == "codex_chat_unit"
    assert result["chat_metadata_row_count"] == 1
    assert result["persistent_memory"] is False
    index_path = runtime / "datasets" / "codex_chat_unit" / "state" / "chat_metadata_index.jsonl"
    assert index_path.exists()
    assert "session-b" in index_path.read_text(encoding="utf-8")
