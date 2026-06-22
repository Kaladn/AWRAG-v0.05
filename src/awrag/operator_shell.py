from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .operator_contract import COMMAND_REGISTRY, parse_operator_command, render_help, render_shortcuts


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="awrag-operator",
        description="Chat-first terminal operator shell for AWRAG command contracts.",
    )
    parser.add_argument("--once", help="Process one live operator input and exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON for --once.")
    parser.add_argument("--launch-side-windows", action="store_true", help="Allow implemented side-window commands to launch helpers.")
    args = parser.parse_args()

    shell = OperatorShell(launch_side_windows=args.launch_side_windows)
    if args.once is not None:
        result = shell.handle_input(args.once)
        if args.json:
            print(json.dumps(result, ensure_ascii=True))
        else:
            print(result["message"])
        return

    shell.run()


class OperatorShell:
    def __init__(self, *, launch_side_windows: bool = False) -> None:
        self.launch_side_windows = launch_side_windows

    def run(self) -> None:
        print("AWRAG Operator Shell")
        print("Chat stays central. Commands are listed below the input.")
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
        command = parse_operator_command(live_input)
        if command is None:
            return {
                "kind": "chat_text",
                "message": "No operator command accepted. Slash commands must start at character 0 of live operator input.\n" + render_shortcuts(),
                "accepted": False,
            }
        if command.name == "help":
            return {"kind": "help", "accepted": True, "message": render_help()}
        if command.name == "quit":
            return {"kind": "quit", "accepted": True, "exit": True, "message": "operator shell closed"}
        if command.name == "settings":
            return {
                "kind": "settings",
                "accepted": True,
                "message": f"side_window_launch={'enabled' if self.launch_side_windows else 'disabled'}",
            }
        if not command.implemented:
            return {
                "kind": "locked",
                "accepted": True,
                "command": command.name,
                "message": f"{command.prefix} is locked: action bridge not enabled.",
            }
        if command.name == "laptop" and self.launch_side_windows:
            return self._launch_laptop_helper()
        return {
            "kind": "command_contract",
            "accepted": True,
            "command": command.name,
            "mutating": command.mutating,
            "side_window": command.side_window,
            "message": _command_card(command.name),
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
        "run:",
        command.cli_template,
    ]
    if command.mutating:
        lines.append("receipt required before trust.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
