from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from awrag.operator_shell import OperatorShell
from awrag.operator_state import audit_operator_state
from awrag.operator_state.modes import (
    AMBIGUITY_MODE,
    DESTRUCTIVE_COMMAND_LOCK,
    EVIDENCE_AUDIT_MODE,
    SYSTEM_COMMAND_MODE,
    TASK_MODE,
    VENT_MODE,
)


def test_osrl_destructive_high_affect_lock() -> None:
    audit = audit_operator_state("This is garbage. Delete it all right now.")

    assert audit["operational_routing"]["selected_mode"] == DESTRUCTIVE_COMMAND_LOCK
    assert audit["structural_analysis"]["destructive_command"] is True
    assert audit["structural_analysis"]["target_is_ambiguous"] is True
    assert audit["structural_analysis"]["mutation_allowed"] is False
    assert audit["operational_routing"]["action_state"] == "AUDIT_ONLY"


def test_osrl_urgency_missing_target() -> None:
    audit = audit_operator_state("Quick, get me the server metrics from yesterday.")

    assert audit["operational_routing"]["selected_mode"] == AMBIGUITY_MODE
    assert audit["anchor_scores"]["urgency"] > 0
    assert audit["anchor_scores"]["target_specificity"] < 0.35
    assert audit["structural_analysis"]["mutation_allowed"] is False


def test_osrl_vent_with_no_command() -> None:
    audit = audit_operator_state("I've been staring at this broken logic for six hours and I'm sick of it.")

    assert audit["operational_routing"]["selected_mode"] == VENT_MODE
    assert audit["structural_analysis"]["command_anchor_present"] is False
    assert audit["structural_analysis"]["mutation_allowed"] is False


def test_osrl_care_valid_system_command_audit_only() -> None:
    audit = audit_operator_state("This project matters. Back up the main branch receipt files.")

    assert audit["operational_routing"]["selected_mode"] == SYSTEM_COMMAND_MODE
    assert audit["anchor_scores"]["care_priority"] > 0
    assert audit["operational_routing"]["action_state"] == "AUDIT_ONLY"
    assert audit["hard_boundaries"]["backend_mutation"] is False


def test_osrl_evidence_request() -> None:
    audit = audit_operator_state("Show me the score, citation, and trace for why this answer was chosen.")

    assert audit["operational_routing"]["selected_mode"] == EVIDENCE_AUDIT_MODE
    assert audit["extracted_anchors"]["evidence_anchors"]
    assert audit["hard_boundaries"]["count_mutation"] is False


def test_osrl_clear_non_destructive_task() -> None:
    audit = audit_operator_state("Show status for dataset scifact.")

    assert audit["operational_routing"]["selected_mode"] == TASK_MODE
    assert audit["anchor_scores"]["mutation_risk"] == 0
    assert audit["structural_analysis"]["mutation_allowed"] is False


def test_operator_shell_runs_osrl_for_non_command_input() -> None:
    result = OperatorShell().handle_input("This is garbage. Delete it all right now.")

    assert result["kind"] == "conversation_osrl"
    assert result["accepted"] is False
    assert result["osrl_audit"]["operational_routing"]["selected_mode"] == DESTRUCTIVE_COMMAND_LOCK
    assert "Destructive command blocked" in str(result["message"])


def test_osrl_cli_input_and_output_receipt(tmp_path: Path) -> None:
    output = tmp_path / "osrl_receipt.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "awrag.cli",
            "operator-state-audit",
            "--input",
            "Show me the score and citation trace.",
            "--output",
            str(output),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert payload["operational_routing"]["selected_mode"] == EVIDENCE_AUDIT_MODE
    assert receipt["operational_routing"]["action_state"] == "AUDIT_ONLY"
    assert receipt["hard_boundaries"]["production_command_execution"] is False


def test_osrl_cli_no_output_does_not_mutate_repo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "awrag.cli",
            "operator-state-audit",
            "--input",
            "Show status for dataset scifact.",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["operational_routing"]["selected_mode"] == TASK_MODE
    assert not list(tmp_path.rglob("*.awbin"))
    assert not (tmp_path / "datasets").exists()
    assert not (tmp_path / "State").exists()
