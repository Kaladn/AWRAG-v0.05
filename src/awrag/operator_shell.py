from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .engine import query as aw_query
from .engine import status as aw_status
from .operator_contract import COMMAND_REGISTRY, parse_operator_command, render_help, render_shortcuts
from .operator_state import audit_operator_state


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="awrag-operator",
        description="Chat-first terminal operator shell for AWRAG command contracts.",
    )
    parser.add_argument("--once", help="Process one live operator input and exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON for --once.")
    parser.add_argument("--launch-side-windows", action="store_true", help="Allow implemented side-window commands to launch helpers.")
    parser.add_argument("--runtime-root", type=Path, help="Runtime root for live AW question mode.")
    parser.add_argument("--dataset-id", help="Dataset id for live AW question mode.")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K evidence locations for live AW question mode.")
    args = parser.parse_args()

    shell = OperatorShell(
        launch_side_windows=args.launch_side_windows,
        runtime_root=args.runtime_root,
        dataset_id=args.dataset_id,
        top_k=args.top_k,
    )
    if args.once is not None:
        result = shell.handle_input(args.once)
        if args.json:
            print(json.dumps(result, ensure_ascii=True))
        else:
            print(result["message"])
        return

    shell.run()


class OperatorShell:
    def __init__(
        self,
        *,
        launch_side_windows: bool = False,
        runtime_root: str | Path | None = None,
        dataset_id: str | None = None,
        top_k: int = 5,
    ) -> None:
        self.launch_side_windows = launch_side_windows
        self.runtime_root = Path(runtime_root).expanduser().resolve() if runtime_root is not None else None
        self.dataset_id = dataset_id
        self.top_k = top_k

    def run(self) -> None:
        print("AWRAG Operator Shell")
        print("Chat stays central. Commands are listed below the input.")
        if self.is_connected:
            print(self._connection_card())
            print("Ask a question directly. Slash commands must start at character 0.")
        else:
            print("No dataset connected. Start with --runtime-root and --dataset-id for AW question mode.")
        print(render_shortcuts())
        print("Type /help for command details. Type /quit to exit.")
        while True:
            try:
                live_input = input("\naw> ")
            except (EOFError, KeyboardInterrupt):
                print("\noperator shell closed")
                return
            result = self.handle_input(live_input)
            print(result["message"])
            if result.get("exit"):
                return

    def handle_input(self, live_input: str) -> dict[str, object]:
        osrl_audit = audit_operator_state(live_input)
        command = parse_operator_command(live_input)
        if command is None:
            if self.is_connected and live_input.strip():
                return self._handle_aw_question(live_input, osrl_audit=osrl_audit)
            return {
                "kind": "conversation_osrl",
                "message": osrl_audit["system_output"]["payload"] + "\n" + render_shortcuts(),
                "accepted": False,
                "osrl_audit": osrl_audit,
            }
        if command.name == "help":
            return {"kind": "help", "accepted": True, "message": render_help(), "osrl_audit": osrl_audit}
        if command.name == "quit":
            return {"kind": "quit", "accepted": True, "exit": True, "message": "operator shell closed", "osrl_audit": osrl_audit}
        if command.name == "settings":
            return {
                "kind": "settings",
                "accepted": True,
                "message": f"side_window_launch={'enabled' if self.launch_side_windows else 'disabled'}",
                "osrl_audit": osrl_audit,
            }
        if not command.implemented:
            return {
                "kind": "locked",
                "accepted": True,
                "command": command.name,
                "message": f"{command.prefix} is locked: action bridge not enabled.",
                "osrl_audit": osrl_audit,
            }
        if command.name == "laptop" and self.launch_side_windows:
            result = self._launch_laptop_helper()
            result["osrl_audit"] = osrl_audit
            return result
        return {
            "kind": "command_contract",
            "accepted": True,
            "command": command.name,
            "mutating": command.mutating,
            "side_window": command.side_window,
            "message": _command_card(command.name),
            "osrl_audit": osrl_audit,
        }

    @property
    def is_connected(self) -> bool:
        return self.runtime_root is not None and bool(self.dataset_id)

    def _connection_card(self) -> str:
        assert self.runtime_root is not None
        assert self.dataset_id is not None
        try:
            state = aw_status(self.runtime_root, self.dataset_id)
            return "\n".join(
                [
                    "Connected dataset:",
                    f"- runtime_root: {self.runtime_root}",
                    f"- dataset_id: {self.dataset_id}",
                    f"- index_status: {state.get('index_status')}",
                    f"- query_allowed: {str(state.get('query_allowed')).lower()}",
                    f"- count_backend: {state.get('count_backend')}",
                    f"- anchors: {state.get('anchor_count')}",
                    f"- relations: {state.get('relation_count')}",
                    f"- blocks: {state.get('block_count')}",
                ]
            )
        except Exception as exc:  # noqa: BLE001 - connection card should explain why chat cannot query.
            return "\n".join(
                [
                    "Dataset connection failed:",
                    f"- runtime_root: {self.runtime_root}",
                    f"- dataset_id: {self.dataset_id}",
                    f"- error: {exc}",
                ]
            )

    def _handle_aw_question(self, question: str, *, osrl_audit: dict[str, object]) -> dict[str, object]:
        assert self.runtime_root is not None
        assert self.dataset_id is not None
        result = aw_query(self.runtime_root, self.dataset_id, question, top_k=self.top_k)
        message = _render_aw_chat_answer(result)
        return {
            "kind": "aw_question",
            "accepted": True,
            "dataset_id": self.dataset_id,
            "runtime_root": str(self.runtime_root),
            "output_path": result.get("output_path"),
            "model_used": result.get("model_used", "none"),
            "model_may_search": result.get("model_may_search", False),
            "message": message,
            "osrl_audit": osrl_audit,
        }

    def _launch_laptop_helper(self) -> dict[str, object]:
        script = Path(__file__).resolve().parents[2] / "Start_Laptop_Temp_Intake.ps1"
        if not script.exists():
            return {
                "kind": "side_window_missing",
                "accepted": True,
                "command": "laptop",
                "message": f"laptop side-window helper missing: {script}",
            }
        subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script)])
        return {
            "kind": "side_window_launched",
            "accepted": True,
            "command": "laptop",
            "message": "Started laptop temp intake side-window helper.",
        }


def _command_card(command_name: str) -> str:
    command = COMMAND_REGISTRY[command_name]
    lines = [
        f"{command.prefix} command",
        f"shortcut: {command.shortcut}",
        f"summary: {command.summary}",
        f"mutating: {str(command.mutating).lower()}",
        f"side_window: {str(command.side_window).lower()}",
        "touches:",
        *[f"- {value}" for value in command.touches],
        "receipts:",
        *[f"- {value}" for value in command.receipts],
        "review:",
        *[f"- {value}" for value in command.next_review],
        "run:",
        command.cli_template,
    ]
    if command.mutating:
        lines.append("receipt required before trust.")
    return "\n".join(lines)


def _render_aw_chat_answer(result: dict[str, object]) -> str:
    answer_packet = result.get("answer_packet") if isinstance(result.get("answer_packet"), dict) else {}
    final_answer = result.get("final_answer") if isinstance(result.get("final_answer"), dict) else {}
    qualification = answer_packet.get("qualification") if isinstance(answer_packet, dict) else {}
    locations = answer_packet.get("locations") if isinstance(answer_packet, dict) else []
    if not isinstance(locations, list):
        locations = []

    lines = [
        "AW answer",
        f"support: {qualification.get('support_state') if isinstance(qualification, dict) else 'unknown'}",
        f"model_used: {result.get('model_used', 'none')}",
        f"model_may_search: {str(result.get('model_may_search', False)).lower()}",
        "",
        "speech_summary:",
        str(final_answer.get("text", "No answer text returned.") if isinstance(final_answer, dict) else "No answer text returned."),
        "",
        "data links:",
    ]
    if not locations:
        lines.append("- none")
    for index, location in enumerate(locations[:3], start=1):
        if not isinstance(location, dict):
            continue
        file_path = location.get("file_path")
        line_start = location.get("line_start")
        source_link = f"{file_path}:{line_start}" if file_path and line_start else file_path
        lines.append(
            "- "
            f"{index}. {location.get('citation')} "
            f"source={source_link} "
            f"lines={location.get('line_start')}-{location.get('line_end')} "
            f"direct={location.get('direct_hit_count')} "
            f"density={location.get('density_score')} "
            f"score={location.get('score')}"
        )
    lines.extend(
        [
            "",
            f"packet_file: {result.get('output_path')}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
