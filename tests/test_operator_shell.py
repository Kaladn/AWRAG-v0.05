from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from awrag.operator_contract import (
    COMMAND_REGISTRY,
    SOURCE_ACTIVE_OPERATOR,
    command_table,
    parse_operator_command,
    render_help,
    render_shortcuts,
)
from awrag.operator_shell import OperatorShell


def test_operator_command_registry_contains_required_handles() -> None:
    expected = {
        "intake": "Ctrl+I",
        "query": "Ctrl+Q",
        "batch": "Ctrl+B",
        "status": "Ctrl+S",
        "laptop": "Ctrl+L",
        "exfil": "Ctrl+E",
        "receipts": "Ctrl+R",
        "settings": "Ctrl+,",
        "help": "Ctrl+H",
        "quit": "Ctrl+X",
    }

    table = {row["name"]: row for row in command_table()}
    assert set(table) == set(expected)
    for name, shortcut in expected.items():
        assert table[name]["prefix"] == f"/{name}"
        assert table[name]["shortcut"] == shortcut
        assert isinstance(table[name]["hash"], str)
        assert len(str(table[name]["hash"])) == 64


def test_operator_command_must_start_live_input() -> None:
    assert parse_operator_command("/status", source=SOURCE_ACTIVE_OPERATOR) == COMMAND_REGISTRY["status"]
    assert parse_operator_command("run /status", source=SOURCE_ACTIVE_OPERATOR) is None
    assert parse_operator_command("old data said /status", source=SOURCE_ACTIVE_OPERATOR) is None
    assert parse_operator_command("/status", source="corpus_replay") is None
    assert parse_operator_command("#status", source=SOURCE_ACTIVE_OPERATOR) is None


def test_operator_help_and_shortcuts_render() -> None:
    shortcuts = render_shortcuts()
    help_text = render_help()

    assert "/intake Ctrl+I" in shortcuts
    assert "/laptop Ctrl+L" in shortcuts
    assert "Corpus slash text is data" in help_text
    assert "locked: exfil action bridge not enabled" in help_text


def test_operator_shell_returns_command_cards_without_mutating(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    shell = OperatorShell()

    result = shell.handle_input("/status")

    assert result["accepted"] is True
    assert result["command"] == "status"
    assert "python -m awrag.cli status" in str(result["message"])
    assert not (tmp_path / "datasets").exists()
    assert not (tmp_path / "State").exists()
    assert not list(tmp_path.rglob("*.awbin"))


def test_operator_shell_locks_exfil() -> None:
    result = OperatorShell().handle_input("/exfil")

    assert result["kind"] == "locked"
    assert result["accepted"] is True
    assert "action bridge not enabled" in str(result["message"])


def test_operator_shell_once_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "awrag.operator_shell",
            "--once",
            "/query",
            "--json",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["accepted"] is True
    assert payload["command"] == "query"
    assert "python -m awrag.cli query" in payload["message"]
